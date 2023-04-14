package handlers

import (
	ctx "context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"

	"github.com/Nerzal/gocloak/v11"
	"go.opentelemetry.io/otel"
	"go.uber.org/zap"
)

var tracer = otel.Tracer("handlers")

const (
	TypeEmail    = "email"
	TypeUsername = "username"
)

// EntityResolution response model
// @Description Returns the original identifier that was used to query for
// @Description the included EntityRepresentations.
// @Description Includes all EntityRepresentations that are mapped to the original identifier.
// @Description EntityRepresentations are generic JSON objects as returned and serialized from the entity store.
type EntityResolution struct {
	OriginalIdentifier EntityIdentifier `json:"original_id"`
	//Generic JSON object containing a complete JSON representation of all the resolved entities and their
	//properties, as generated by the entity store.
	EntityRepresentations []map[string]interface{}
}

type EntityIdentifier struct {
	Identifier string `json:"identifier" example:"bob@sample.org"`
	Type       string `json:"type" example:"email" enums:"email,username"`
}

// EntityResolution request model
// @Description Request containing entity identifiers which will be used to query/resolve to an EntityRepresentation
// @Description by querying the underlying store.
// @Description This assumes that some entity store exists somewhere, and
// @Description that user store keeps track of entities by canonical ID, and that each entity
// @Description with a canonical ID might be "searchable" or "identifiable" by some other, non-canonical
// @Description identifier.
// @Description At least one entity identifier is required
type EntityResolutionRequest struct {
	//enum: email,username
	EntityIdentifiers []EntityIdentifier `json:"entity_identifiers"`
}

type KeyCloakConnector struct {
	token  *gocloak.JWT
	client gocloak.GoCloak
}

type KeyCloakConfg struct {
	Url            string
	Realm          string
	ClientId       string
	ClientSecret   string
	LegacyKeycloak bool `default:"false"`
	SubGroups      bool `default:"false"`
}

// GetEntitlements godoc
// @Summary      Resolve a set of entity labels to their keycloak identifiers
// @Description  Provide an attribute type and attribute label list
// @Description  and receive a list of entity idenitifiers
// @Success      200 {array} []handlers.EntityResolution
// @Param        "Entity Resolution Request" body handlers.EntityResolutionRequest true "Entity Identifiers to be resolved"
// @Accept       json
// @Produce      json
// @Router       /resolve [post]
func GetEntityResolutionHandler(kcConfig KeyCloakConfg, logger *zap.SugaredLogger) http.Handler {
	//Try initial login
	c, err := getKCClient(kcConfig, logger)
	if err != nil {
		logger.Fatalf("Error connecting to keycloak at %s", kcConfig.Url)
	}
	logger.Debug("client token", c.token.AccessToken)

	ctxb := ctx.Background()

	entityResolutionHandler := func(w http.ResponseWriter, req *http.Request) {
		spanCtx := req.Context()
		handlerCtx, span := tracer.Start(spanCtx, "GetEntityResolutionHandler")
		defer span.End()

		if req.Method != http.MethodPost {
			logger.Error("Rejected request, invalid HTTP verb")
			http.Error(w, "Method Not Allowed", http.StatusMethodNotAllowed)
			return
		}

		logger.Debug("GetEntityResolutionHandler - reading request body")

		//Read + consume body
		bodBytes, err := io.ReadAll(req.Body)
		defer req.Body.Close()
		if err != nil {
			logger.Errorf("Couldn't read client request! Error was %s", err)
			w.WriteHeader(http.StatusBadRequest)
			return
		}

		payload, err := getRequestPayload(bodBytes, handlerCtx, logger)
		if err != nil {
			logger.Errorf("Couldn't deserialize client request! Error was %s", err)
			w.WriteHeader(http.StatusBadRequest)
			return
		}

		var resolvedEntities []EntityResolution
		logger.Debugf("Received payload", payload)

		kcConnector, err := getKCClient(kcConfig, logger)
		if err != nil {
			logger.Fatalf("Error connecting to keycloak %s at url %s", err, kcConfig.Url)
			w.WriteHeader(http.StatusBadRequest)
			return
		}

		for _, ident := range payload.EntityIdentifiers {
			var keycloakEntities []*gocloak.User
			logger.Debugf("Lookup entity %s/%s", ident.Type, ident.Identifier)
			var getUserParams gocloak.GetUsersParams

            exactMatch := true
			switch ident.Type {
			case TypeEmail:
				getUserParams = gocloak.GetUsersParams{Email: &ident.Identifier, Exact: &exactMatch }
			case TypeUsername:
				getUserParams = gocloak.GetUsersParams{Username: &ident.Identifier, Exact: &exactMatch }
			}

			users, userErr := kcConnector.client.GetUsers(ctxb, kcConnector.token.AccessToken, kcConfig.Realm, getUserParams)
			if userErr != nil {
				logger.Error("Error getting user", userErr)
				w.WriteHeader(http.StatusInternalServerError)
				return
			} else if len(users) == 1 {
				user := users[0]
				logger.Debugf("User %s found for %s ", *user.ID, ident.Identifier)
				keycloakEntities = append(keycloakEntities, user)
			} else {
				logger.Debug("No user found for ", ident.Identifier)
				if ident.Type == TypeEmail {
					//try by group
					groups, groupErr := kcConnector.client.GetGroups(ctxb, kcConnector.token.AccessToken, kcConfig.Realm, gocloak.GetGroupsParams{Search: &ident.Identifier})
					if groupErr != nil {
						logger.Error("Error getting group", groupErr)
						w.WriteHeader(http.StatusInternalServerError)
						return
					} else if len(groups) == 1 {
						logger.Debug("Group found for ", ident.Identifier)
						group := groups[0]
						expandedRepresentations, exErr := expandGroup(*group.ID, kcConnector,
							&kcConfig, ctxb, logger)
						if exErr != nil {
							w.WriteHeader(http.StatusInternalServerError)
							return
						} else {
							keycloakEntities = expandedRepresentations
						}
					}
				}
			}

			//Convert Keycloak entity structs to generic JSON objects for the response.
			var jsonEntities []map[string]interface{}
			for _, er := range keycloakEntities {
				json, err := typeToGenericJSONMap(er, logger)
				if err != nil {
					logger.Errorf("Error serializing entity representation: %s", err)
					w.WriteHeader(http.StatusInternalServerError)
					return
				}
				jsonEntities = append(jsonEntities, json)
			}
			resolvedEntities = append(resolvedEntities, EntityResolution{OriginalIdentifier: ident, EntityRepresentations: jsonEntities})
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		err = json.NewEncoder(w).Encode(resolvedEntities)
		if err != nil {
			logger.Errorf("Error encoding resolved entities in response! Error was %s", err)
			http.Error(w, "Server Error", http.StatusInternalServerError)
			return
		}
	}
	return http.HandlerFunc(entityResolutionHandler)
}

func typeToGenericJSONMap[Marshalable any](inputStruct Marshalable, logger *zap.SugaredLogger) (map[string]interface{}, error) {
	//For now, since we dont' know the "shape" of the entity/user record or representation we will get from a specific entity store,
	//
	tmpDoc, err := json.Marshal(inputStruct)
	if err != nil {
		logger.Errorf("Error marshalling input type! Error was %s", err)
		return nil, err
	}

	var genericMap map[string]interface{}

	err = json.Unmarshal(tmpDoc, &genericMap)
	if err != nil {
		logger.Errorf("Could not deserialize generic entitlement context JSON input document! Error was %s", err)
		return nil, err
	}

	return genericMap, nil
}

func expandGroup(groupID string, kcConnector *KeyCloakConnector,
	kcConfig *KeyCloakConfg, ctx ctx.Context, logger *zap.SugaredLogger) ([]*gocloak.User, error) {

	var entityRepresentations []*gocloak.User
	logger.Debugf("Add members of group %s", groupID)
	grp, err := kcConnector.client.GetGroup(ctx, kcConnector.token.AccessToken, kcConfig.Realm, groupID)
	if err == nil {
		grpMembers, memberErr := kcConnector.client.GetGroupMembers(ctx, kcConnector.token.AccessToken, kcConfig.Realm,
			*grp.ID, gocloak.GetGroupsParams{})
		if memberErr == nil {
			logger.Debugf("Adding members %d members from group %s", len(grpMembers), *grp.Name)
			for i := 0; i < len(grpMembers); i++ {
				user := grpMembers[i]
				entityRepresentations = append(entityRepresentations, user)
			}
		} else {
			logger.Error("Error getting group members", memberErr)
			err = memberErr
		}
		// TODO crawl sub groups?

		// if kcConfig.SubGroups {

		// }
	} else {
		logger.Error("Error getting group", err)
	}
	return entityRepresentations, err
}

func getKCClient(kcConfig KeyCloakConfg, logger *zap.SugaredLogger) (*KeyCloakConnector, error) {
	//TODO cache token / refresh...using oauth2/oidc provider
	var client gocloak.GoCloak
	logger.Debugf("Connecting to keycloak using URL: %s and Realm: %s", kcConfig.Url, kcConfig.Realm)
	//See https://github.com/Nerzal/gocloak/issues/346
	if kcConfig.LegacyKeycloak {
		logger.Warn("Using legacy connection mode for Keycloak < 17.x.x")
		client = gocloak.NewClient(kcConfig.Url)
	} else {
		client = gocloak.NewClient(kcConfig.Url, gocloak.SetAuthAdminRealms("admin/realms"), gocloak.SetAuthRealms("realms"))
	}

	ctxb := ctx.Background()
	token, err := client.LoginClient(ctxb, kcConfig.ClientId, kcConfig.ClientSecret, kcConfig.Realm)
	if err != nil {
		logger.Warn("Error connecting to keycloak!", zap.Error(err))
		return nil, err
	}
	keycloakConnector := KeyCloakConnector{token: token, client: client}
	return &keycloakConnector, err
}

func getRequestPayload(bodBytes []byte, parentCtx ctx.Context, logger *zap.SugaredLogger) (*EntityResolutionRequest, error) {
	_, span := tracer.Start(parentCtx, "getRequestPayload")
	defer span.End()

	logger.Debugf("Parsing request payload: %s", string(bodBytes))
	// Unmarshal
	var payload EntityResolutionRequest
	err := json.Unmarshal(bodBytes, &payload)
	if err != nil {
		logger.Warn("Error parsing request body")
		return nil, err
	}
	//Validate acceptable "type"
	var typeErr error
	for _, ident := range payload.EntityIdentifiers {
		switch ident.Type {
		case TypeEmail:
			fallthrough
		case TypeUsername:
			return &payload, nil
		case "":
			typeErr = errors.New("type required")
			logger.Warn(typeErr)
		default:
			typeErr = fmt.Errorf("Unknown Type %s for identifier %s", ident.Type, ident.Identifier)
			logger.Warn(typeErr)
		}
	}

	return nil, typeErr
}
