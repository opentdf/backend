package handlers

import (
	ctx "context"
	"encoding/json"
	"io"
	"net/http"

	log "github.com/sirupsen/logrus"
	"go.opentelemetry.io/otel"
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

// EntitlementsRequest defines the body for the /entitlements endpoint
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
	SecondaryEntityIds []string `json:"secondary_entity_ids,omitempty" example:"4f6636ca-c60c-40d1-9f3f-015086303f74"`
	// Optional, may be left empty.
	// A free-form, (valid, escaped) JSON object in string format, containing any additional IdP/input context around and from
	// the entity authentication process. This JSON object will be checked as a valid, generic JSON document,
	// and then passed to the PDP engine as-is, as an input document.
	EntitlementContextObject string `json:"entitlement_context_obj,omitempty" example:"{\"somekey\":\"somevalue\"}"`
}

type PDPEngine interface {
	ApplyEntitlementPolicy(primaryEntity string, secondaryEntities []string, entitlementContextJSON string, parentCtx ctx.Context) ([]EntityEntitlement, error)
}

type Entitlements struct {
	Pdp PDPEngine
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
func (e Entitlements) ServeHTTP(w http.ResponseWriter, req *http.Request) {
	log.Debugf("entitlemnts request %s", req.URL)
	spanCtx := req.Context()
	handlerCtx, span := tracer.Start(spanCtx, "GetEntitlementsHandler")
	defer span.End()

	if req.Method != http.MethodPost {
		log.Error("Rejected request, invalid HTTP verb")
		http.Error(w, "Method Not Allowed", http.StatusMethodNotAllowed)
		return
	}

	log.Debug("GetEntitlementsHandler - reading request body")

	// Read + consume body
	bodBytes, err := io.ReadAll(req.Body)
	defer func(Body io.ReadCloser) {
		err := Body.Close()
		if err != nil {
			log.Error(err)
		}
	}(req.Body)
	if err != nil {
		log.Errorf("Couldn't read client request! Error was %s", err)
		w.WriteHeader(http.StatusBadRequest)
		return
	}

	payload, err := getRequestPayload(handlerCtx, bodBytes)
	if err != nil {
		log.Errorf("Couldn't deserialize client request! Error was %s", err)
		w.WriteHeader(http.StatusBadRequest)
		return
	}

	entitlements, err := e.Pdp.ApplyEntitlementPolicy(
		payload.PrimaryEntityId,
		payload.SecondaryEntityIds,
		payload.EntitlementContextObject,
		handlerCtx)

	if err != nil {
		log.Errorf("Policy engine returned error! Error was %s", err)
		w.WriteHeader(http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	err = json.NewEncoder(w).Encode(entitlements)
	if err != nil {
		log.Errorf("Error encoding entitlements in response! Error was %s", err)
		http.Error(w, "Server Error", http.StatusInternalServerError)
		return
	}
}

func getRequestPayload(parentCtx ctx.Context, bodBytes []byte) (*EntitlementsRequest, error) {
	_, span := tracer.Start(parentCtx, "getRequestPayload")
	defer span.End()

	log.Debugf("Parsing request payload: %s", string(bodBytes))
	// Unmarshal
	var payload EntitlementsRequest
	err := json.Unmarshal(bodBytes, &payload)
	if err != nil {
		log.Warn("Error parsing Exchange request body")
		return nil, ErrJoin(ErrPayloadUnmarshal, err)
	}

	// If context supplied, must be in JSON format
	if payload.EntitlementContextObject != "" {
		if !json.Valid([]byte(payload.EntitlementContextObject)) {
			err := ErrJoin(ErrPayloadInvalid, err)
			log.Warn(err)
			return nil, err
		}
	}

	return &payload, nil
}

type Error string

func (err Error) Error() string {
	return string(err)
}

// ErrJoin needed for Go 1.19, replace with errors.Join
// code from https://cs.opensource.google/go/go/+/master:src/errors/join.go
func ErrJoin(errs ...error) error {
	n := 0
	for _, err := range errs {
		if err != nil {
			n++
		}
	}
	if n == 0 {
		return nil
	}
	e := &joinError{
		errs: make([]error, 0, n),
	}
	for _, err := range errs {
		if err != nil {
			e.errs = append(e.errs, err)
		}
	}
	return e
}

type joinError struct {
	errs []error
}

func (e *joinError) Error() string {
	var b []byte
	for i, err := range e.errs {
		if i > 0 {
			b = append(b, '\n')
		}
		b = append(b, err.Error()...)
	}
	return string(b)
}

func (e *joinError) Unwrap() []error {
	return e.errs
}
