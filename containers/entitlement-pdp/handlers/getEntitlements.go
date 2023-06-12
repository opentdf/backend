package handlers

import (
	"bytes"
	ctx "context"
	"encoding/json"
	"errors"
	"io"
	"log"
	"net/http"

	"go.opentelemetry.io/otel"
	"go.uber.org/zap"
)

const (
	ErrPayloadUnmarshal = Error("payload json unmarshal failure")
	ErrPayloadInvalid   = Error("payload json invalid")
)

var tracer = otel.Tracer("handlers")

// EntityAttribute model
// @Description Represents a single entity attribute.
type EntityAttribute struct {
	// Attribute, in URI format, e.g.: "https://example.org/attr/Classification/value/COI"
	Attribute string `json:"attribute" example:"https://example.org/attr/OPA/value/AddedByOPA"`
	// Optional display name for the attribute
	DisplayName string `json:"displayName,omitempty" example:"Added By OPA"`
}

type EntityEntitlement struct {
	EntityId         string            `json:"entity_identifier" example:"bc03f40c-a7af-4507-8198-d5334e2823e6"`
	EntityAttributes []EntityAttribute `json:"entity_attributes"`
}

// EntitlementsRequest request model
// @Description Request containing entity identifiers seeking entitlement.
// @Description At least one entity (primary requestor) is required
// @Description The Entitlements PDP is expected to be invoked directly by an identity provider
// @Description and with contextual entity information attested to and possessed by that identity provider
type EntitlementsRequest struct {
	// The identifier for the primary entity seeking entitlement.
	// For PE auth, this will be a PE ID. For NPE/direct grant auth, this will be an NPE ID.
	PrimaryEntityId string `json:"primary_entity_id" example:"bc03f40c-a7af-4507-8198-d5334e2823e6"`
	// Optional, may be left empty.
	// For PE auth, this will be one or more NPE IDs (client-on-behalf-of-user).
	// For NPE/direct grant auth,
	// this may be either empty (client-on-behalf-of-itself) or populated with one
	// or more NPE IDs (client-on-behalf-of-other-clients, aka chaining flow)
	SecondaryEntityIds []string `json:"secondary_entity_ids" example:"4f6636ca-c60c-40d1-9f3f-015086303f74"`
	// Optional, may be left empty.
	// A free-form, (valid, escaped) JSON object in string format, containing any additional IdP/input context around and from
	// the entity authentication process. This JSON object will be checked as a valid, generic JSON document,
	// and then passed to the PDP engine as-is, as an input document.
	EntitlementContextObject string `json:"entitlement_context_obj,omitempty" example:"{\"somekey\":\"somevalue\"}"`
}

type PDPEngine interface {
	ApplyEntitlementPolicy(primaryEntity string, secondaryEntities []string, entitlementContextJSON string, parentCtx ctx.Context) ([]EntityEntitlement, error)
}

// GetEntitlementsHandler godoc
// @Summary      Request an entitlements set from the PDP
// @Description  Provide entity identifiers to the entitlement PDP
// @Description  and receive an array of attribute sets for each entity involved in the entitlement decisions
// @Tags         Entitlements
// @Accept       json
// @Produce      json
// @Param        "Entitlements Request" body handlers.EntitlementsRequest true "List of primary and secondary entity identifiers to entitle"
// @Success      200 {array}  handlers.EntityEntitlement
// @Failure      400 {string} http.StatusBadRequest
// @Failure      404 {string} http.StatusNotFound
// @Failure      500 {string} http.StatusServerError
// @Router       /entitlements [post]
func GetEntitlementsHandler(pdp PDPEngine, logger *zap.SugaredLogger) http.Handler {
	entitlementsHandler := func(w http.ResponseWriter, req *http.Request) {
		spanCtx := req.Context()
		handlerCtx, span := tracer.Start(spanCtx, "GetEntitlementsHandler")
		defer span.End()

		if req.Method != http.MethodPost {
			logger.Error("Rejected request, invalid HTTP verb")
			http.Error(w, "Method Not Allowed", http.StatusMethodNotAllowed)
			return
		}

		logger.Debug("GetEntitlementsHandler - reading request body")

		// Read + consume body
		bodBytes, err := io.ReadAll(req.Body)
		defer func(Body io.ReadCloser) {
			err := Body.Close()
			if err != nil {
				log.Println(err)
			}
		}(req.Body)
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

		entitlements, err := pdp.ApplyEntitlementPolicy(
			payload.PrimaryEntityId,
			payload.SecondaryEntityIds,
			payload.EntitlementContextObject,
			handlerCtx)

		if err != nil {
			logger.Errorf("Policy engine returned error! Error was %s", err)
			w.WriteHeader(http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		err = json.NewEncoder(w).Encode(entitlements)
		if err != nil {
			logger.Errorf("Error encoding entitlements in response! Error was %s", err)
			http.Error(w, "Server Error", http.StatusInternalServerError)
			return
		}
	}

	return http.HandlerFunc(entitlementsHandler)
}

func getRequestPayload(bodBytes []byte, parentCtx ctx.Context, logger *zap.SugaredLogger) (*EntitlementsRequest, error) {
	_, span := tracer.Start(parentCtx, "getRequestPayload")
	defer span.End()

	logger.Debugf("Parsing request payload: %s", string(bodBytes))
	// Unmarshal
	var payload EntitlementsRequest
	err := json.Unmarshal(bodBytes, &payload)
	if err != nil {
		logger.Warn("Error parsing Exchange request body")
		return nil, Error.Join(ErrPayloadUnmarshal, err)
	}

	// If context supplied, must be in JSON format
	if payload.EntitlementContextObject != "" {
		if !json.Valid([]byte(payload.EntitlementContextObject)) {
			err := Error.Join(ErrPayloadInvalid, err)
			logger.Warn(err)
			return nil, err
		}
	}

	return &payload, nil
}

type Error string

func (err Error) Error() string {
	return string(err)
}

func (err Error) Join(errs ...error) error {
	if len(errs) == 0 {
		return nil
	}
	var buf bytes.Buffer
	for _, err := range errs {
		if err != nil {
			buf.WriteString(err.Error())
			buf.WriteString("\n")
		}
	}
	return errors.New(buf.String())
}
