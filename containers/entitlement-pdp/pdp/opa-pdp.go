package pdp

import (
	"bytes"
	ctx "context"
	"encoding/json"
	"os"
	"strings"
	"time"

	opalog "github.com/open-policy-agent/opa/logging"
	"github.com/open-policy-agent/opa/metrics"
	"github.com/open-policy-agent/opa/profiler"
	"github.com/open-policy-agent/opa/sdk"
	"github.com/opentdf/v2/entitlement-pdp/handlers"
	log "github.com/sirupsen/logrus"
	"go.opentelemetry.io/otel"
)

const (
	ErrOpaDecision            = Error("OPA decision")
	ErrOpaResultDeserialize   = Error("deserializing OPA result")
	ErrFinalJson              = Error("deserialize final JSON result document")
	ErrInputDocumentUnmarshal = Error("deserialize generic entitlement context JSON input document")
	ErrInputDocumentMarshal   = Error("re-marshalling input doc")
	ErrResultDocumentMarshal  = Error("re-marshalling result doc")
	ErrFinalDocumentUnmarshal = Error("deserialize final JSON input document")
)

var tracer = otel.Tracer("pdp")

type OPAPDPEngine struct {
	opa *sdk.OPA
}

type entitlementDecisionInputDocument struct {
	PrimaryEntity      string                 `json:"primary_entity"`
	SecondaryEntities  []string               `json:"secondary_entities"`
	EntitlementContext map[string]interface{} `json:"entitlement_context,omitempty"`
}

type Decision struct {
	ID     string                       `json:"ID"`
	Result []handlers.EntityEntitlement `json:"Result"`
}

func InitOPAPDP(parentCtx ctx.Context) (OPAPDPEngine, func()) {
	initOpaCtx, span := tracer.Start(parentCtx, "InitOPAPDP")
	defer span.End()

	opaConfigPath := os.Getenv("OPA_CONFIG_PATH")
	log.Debugf("Loading config file from from %s", opaConfigPath)
	opaConfig, err := os.ReadFile(opaConfigPath)
	if err != nil {
		log.Panicf("Error loading config file from from %s! Error was %s", opaConfigPath, err)
	}
	opaConfig = replaceOpaEnvVar(opaConfig)

	var shutdownFunc func()
	const timeout = 2 * time.Second
	opaCtx, opaCtxCancel := ctx.WithTimeout(initOpaCtx, timeout)
	// Annoyingly, OPA defines its own logging interface - so for now just wrap logger
	opaLogger := &OtelLogger{
		ctx: opaCtx,
	}
	opaOptions := sdk.Options{
		Config:        bytes.NewReader(opaConfig),
		Logger:        opaLogger,
		ConsoleLogger: opaLogger,
		Ready:         nil,
		Plugins:       nil,
		ID:            "EP-0",
	}
	opa, err := sdk.New(opaCtx, opaOptions)
	if err != nil {
		log.WithContext(opaCtx).Debug(err)
	}
	// assert opa state manager is setup and return nil
	if opa.Plugin("") != nil {
		log.Panic(ErrOpaDecision)
	}

	log.WithContext(opaCtx).Info("OPA Engine successfully started")

	// Return a shutdown func the caller can use to dispose OPA engine
	shutdownFunc = func() {
		log.WithContext(opaCtx).Info("Shutting down OPA engine")
		opa.Stop(opaCtx)
		// Cancel context - probably redundant in most cases
		opaCtxCancel()
	}

	return OPAPDPEngine{opa}, shutdownFunc
}

// replaceOpaEnvVar replace environment variables that begin with OPA_
func replaceOpaEnvVar(opaConfig []byte) []byte {
	// Get all environment variables that begin with OPA_
	var opaEnvVars []string
	for _, key := range os.Environ() {
		if strings.HasPrefix(key, "OPA_") {
			opaEnvVars = append(opaEnvVars, key)
		}
	}
	// Replace the environment variables in the string
	configString := string(opaConfig)
	for _, keyVal := range opaEnvVars {
		kv := strings.Split(keyVal, "=")
		envVarValue := os.Getenv(kv[0])
		configString = strings.ReplaceAll(configString, "${"+kv[0]+"}", envVarValue)
	}
	// backwards compatible
	configString = strings.ReplaceAll(configString, "${CR_PAT}", os.Getenv("OPA_POLICYBUNDLE_PULLCRED"))
	return []byte(configString)
}

func (pdp *OPAPDPEngine) ApplyEntitlementPolicy(primaryEntity string, secondaryEntities []string, entitlementContextJSON string, parentCtx ctx.Context) ([]handlers.EntityEntitlement, error) {
	log.Debug("ApplyEntitlementPolicy")
	evalCtx, evalSpan := tracer.Start(parentCtx, "ApplyEntitlementPolicy")
	defer evalSpan.End()

	log.Debugf("ENTITLEMENT CONTEXT JSON: %s", entitlementContextJSON)

	inputDoc, err := pdp.buildInputDoc(primaryEntity, secondaryEntities, entitlementContextJSON)
	if err != nil {
		log.Errorf("Error constructing input document, error was %s", err)
		return nil, err
	}

	log.Debugf("INPUT DOC is %s", inputDoc)

	decisionReq := sdk.DecisionOptions{
		Now:                 time.Now(),
		Path:                "opentdf/entitlement/generated_entitlements",
		Input:               inputDoc,
		NDBCache:            nil,
		StrictBuiltinErrors: false,
		Tracer:              nil,
		Metrics:             metrics.New(),
		Profiler:            profiler.New(),
		Instrument:          false,
	}

	result, err := pdp.opa.Decision(evalCtx, decisionReq)
	if err != nil {
		log.Errorf("Got OPA decision error: %s", err)
		return nil, ErrJoin(ErrOpaDecision, err)
	}

	decis, err := pdp.deserializeEntitlementsFromResult(result)
	if err != nil {
		log.Errorf("Error deserializing OPA result, error was %s", err)
		return nil, ErrJoin(ErrOpaResultDeserialize, err)
	}

	log.Debugf("Got unmarshalled entitlements: %+v", decis.Result)

	return decis.Result, err
}

func (pdp *OPAPDPEngine) deserializeEntitlementsFromResult(rawResult *sdk.DecisionResult) (*Decision, error) {
	log.Debugf("Got OPA raw result: %s", rawResult)

	// Marshal that entire doc BACK to a string.
	resDoc, err := json.Marshal(rawResult)
	if err != nil {
		log.Errorf("Error re-marshalling result doc! Error was %s", err)
		return nil, ErrJoin(ErrResultDocumentMarshal, err)
	}

	log.Debugf("Tmp string result is %s", string(resDoc))

	var decis Decision
	err = json.Unmarshal(resDoc, &decis)
	if err != nil {
		log.Errorf("Could not deserialize final JSON result document! Error was %s", err)
		return nil, ErrJoin(ErrFinalJson, err)
	}

	return &decis, nil
}

func (pdp *OPAPDPEngine) buildInputDoc(primaryEntity string, secondaryEntities []string, entitlementContextJSON string) (map[string]interface{}, error) {
	// The unstructured input must be first deserialized into a generic-but-concrete type, so we can embed it
	// as such as a subfield in the larger input document.
	//
	// Can't skip this step, because otherwise JSON encoding will rightly treat it as an escaped JSON string -
	// this, even though it feels redundant, is the safest and most foolproof approach.
	var entitlementContext map[string]interface{}

	// If this was not defined, use empty JSON object
	if entitlementContextJSON == "" {
		entitlementContextJSON = "{}"
	}

	err := json.Unmarshal([]byte(entitlementContextJSON), &entitlementContext)
	if err != nil {
		log.Errorf("Could not deserialize generic entitlement context JSON input document! Error was %s", err)
		return nil, ErrJoin(ErrInputDocumentUnmarshal, err)
	}

	// Build the toplevel input doc.
	inputDoc := entitlementDecisionInputDocument{primaryEntity, secondaryEntities, entitlementContext}

	// Marshal that entire doc BACK to a string.
	tmpDoc, err := json.Marshal(inputDoc)
	if err != nil {
		log.Errorf("Error re-marshalling input doc! Error was %s", err)
		return nil, ErrJoin(ErrInputDocumentMarshal, err)
	}

	log.Debugf("Tmp result is %s", string(tmpDoc))
	// OPA wants this as a generic map[string]interface{} and will not handle
	// deserializing to concrete structs
	// So, we deserialize the whole thing again into a generic `map[string]interface{}`
	var inputUnstructured map[string]interface{}
	err = json.Unmarshal(tmpDoc, &inputUnstructured)
	if err != nil {
		log.Errorf("Could not deserialize final JSON input document! Error was %s", err)
		return nil, ErrJoin(ErrFinalDocumentUnmarshal, err)
	}

	log.Debugf("Final doc is %+v", inputUnstructured)

	return inputUnstructured, nil
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

// OtelLogger with context for otel
type OtelLogger struct {
	ctx ctx.Context
}

func (l *OtelLogger) Debug(fmt string, a ...interface{}) {
	log.WithContext(l.ctx).Debug(fmt, a)
}
func (l *OtelLogger) Info(fmt string, a ...interface{}) {
	log.WithContext(l.ctx).Info(fmt, a)
}
func (l *OtelLogger) Error(fmt string, a ...interface{}) {
	log.WithContext(l.ctx).Error(fmt, a)
}
func (l *OtelLogger) Warn(fmt string, a ...interface{}) {
	log.WithContext(l.ctx).Warn(fmt, a)
}
func (l *OtelLogger) WithFields(fields map[string]interface{}) opalog.Logger {
	log.WithContext(l.ctx).WithFields(fields)
	return l
}
func (l *OtelLogger) GetLevel() opalog.Level {
	return opalog.Level(log.GetLevel())
}
func (l *OtelLogger) SetLevel(level opalog.Level) {
	log.Debugf("SetLevel %v", level)
}
