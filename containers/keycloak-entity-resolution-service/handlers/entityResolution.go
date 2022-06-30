package handlers

import (
	ctx "context"
	"encoding/json"
	"errors"
	"fmt"
	"io/ioutil"
	"net/http"

	"github.com/Nerzal/gocloak/v11"
	"go.opentelemetry.io/otel"
	"go.uber.org/zap"
)

var tracer = otel.Tracer("handlers")

// EntityResolution
type EntityResolution struct {
	Identifier        string   `json:"identifier" example:"bob@sample.org"`
	EntityIdentifiers []string `json:"entity_ids" example:"XUX-ASDF-ASDFSD"`
}

// EntityResolution
type EntityResolutionResponse struct {
	AttributeType     string             `json:"type" example:"email"`
	EntityResolutions []EntityResolution `json:"entity_resolutions"`
}

// EntityResolution request model
type EntityResolutionRequest struct {
	//enum: email,username
	AttributeType     string   `json:"type" example:"email"`
	EntityIdentifiers []string `json:"identifiers" example:"bob@sample.org"`
}

type KeyCloakConnector struct {
	token  *gocloak.JWT
	client gocloak.GoCloak
}

type KeyCloakConfg struct {
	Url          string
	Realm        string
	ClientId     string
	ClientSecret string
	AuthPath     bool `default:true`
}

// GetEntitlements godoc
// @Summary      Resolve a set of entity labels to their keycloak identifiers
// @Description  Provide an attribute type and attribute label list
// @Description  and receive a list of entity idenitifiers
// @Success      200 {array}  handlers.EntityResolution
// @Param        "Entity Resolution Request" body handlers.EntityResolutionRequest true "Entity Identifiers to be resolved"
// @Accept       json
// @Produce      json
// @Router       /resolve [post]
func GetEntityResolutionHandler(kcConfig KeyCloakConfg, logger *zap.SugaredLogger) http.Handler {
	//Try initial login
	c, err := getKCClient(kcConfig, logger)
	if err != nil {
		logger.Fatal("Error connecting to keycloakd")
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
		bodBytes, err := ioutil.ReadAll(req.Body)
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
		logger.Infof("Received payload", payload)

		kcConnector, err := getKCClient(kcConfig, logger)
		if err != nil {
			logger.Errorf("Error connecting to keycloak %s", err)
			w.WriteHeader(http.StatusBadRequest)
			return
		}

		for i := 0; i < len(payload.EntityIdentifiers); i++ {
			entityIdentifier := payload.EntityIdentifiers[i]
			var entityIdentifiers []string
			logger.Infof("Lookup entity %s/%s", payload.AttributeType, entityIdentifier)
			var getUserParams gocloak.GetUsersParams
			if payload.AttributeType == "email" {
				getUserParams = gocloak.GetUsersParams{Email: &entityIdentifier}
			} else if payload.AttributeType == "username" {
				getUserParams = gocloak.GetUsersParams{Username: &entityIdentifier}
			}
			users, userErr := kcConnector.client.GetUsers(ctxb, kcConnector.token.AccessToken, kcConfig.Realm, getUserParams)
			logger.Info("userError is nil", userErr == nil)
			logger.Infof("user leng %d", len(users))
			if userErr != nil {
				logger.Error("Error getting user", userErr)
			} else if len(users) == 1 {
				user := users[0]
				logger.Infof("User %s found for %s ", *user.ID, entityIdentifier)
				entityIdentifiers = append(entityIdentifiers, *user.ID)
			} else {
				logger.Debug("No user found for ", entityIdentifier)
			}
			resolvedEntities = append(resolvedEntities, EntityResolution{Identifier: entityIdentifier, EntityIdentifiers: entityIdentifiers})
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		err = json.NewEncoder(w).Encode(EntityResolutionResponse{AttributeType: payload.AttributeType, EntityResolutions: resolvedEntities})
		if err != nil {
			logger.Errorf("Error encoding resolved entities in response! Error was %s", err)
			http.Error(w, "Server Error", http.StatusInternalServerError)
			return
		}
	}

	return http.HandlerFunc(entityResolutionHandler)
}

func getKCClient(kcConfig KeyCloakConfg, logger *zap.SugaredLogger) (*KeyCloakConnector, error) {
	//TODO cache token / refresh...using oauth2/oidc provider
	var client gocloak.GoCloak = nil
	if kcConfig.AuthPath {
		client = gocloak.NewClient(kcConfig.Url)
	} else {
		client = gocloak.NewClient(kcConfig.Url, gocloak.SetAuthAdminRealms("admin/realms"), gocloak.SetAuthRealms("realms"))
	}

	ctxb := ctx.Background()
	token, err := client.LoginClient(ctxb, kcConfig.ClientId, kcConfig.ClientSecret, kcConfig.Realm)
	if err != nil {
		logger.Warn("Error connecting to keycloak!", zap.Error(err))
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
	attrType := payload.AttributeType
	if attrType == "" {
		err = errors.New("type required")
		return nil, err
	} else if !(attrType == "email" || attrType == "username") {
		logger.Warn("Unknown type ", attrType)
		err = fmt.Errorf("Unknown Type %s", attrType)
		return nil, err
	}

	return &payload, nil
}
