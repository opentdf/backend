package pdp

import (
	"bytes"
	ctx "context"
	"encoding/json"
	"os"
	"strings"
	"time"

	opalog "github.com/open-policy-agent/opa/logging"
	"github.com/open-policy-agent/opa/sdk"
	"go.opentelemetry.io/otel"
	"go.uber.org/zap"

	"github.com/virtru/v2/entitlement-pdp/handlers"
)

var tracer = otel.Tracer("pdp")

type OPAPDPEngine struct {
	logger *zap.SugaredLogger
	opa    *sdk.OPA
}

type entitlementDecisionInputDocument struct {
	PrimaryEntity     string                 `json:"primary_entity"`
	SecondaryEntities []string               `json:"secondary_entities"`
	IdpContext        map[string]interface{} `json:"idp_context,omitempty"`
}

type Decision struct {
	ID     string                       `json:"ID"`
	Result []handlers.EntityEntitlement `json:"Result"`
}

func InitOPAPDP(opaConfigPath, opaPolicyPullSecret string, logger *zap.SugaredLogger, parentCtx ctx.Context) (OPAPDPEngine, func()) {
	initOpaCtx, span := tracer.Start(parentCtx, "InitOPAPDP")
	defer span.End()

	var shutdownFunc func()
	opaCtx, opaCtxCancel := ctx.WithTimeout(initOpaCtx, time.Second*10)

	logger.Debugf("Loading config file from from %s", opaConfigPath)
	opaConfig, err := os.ReadFile(opaConfigPath)
	if err != nil {
		logger.Fatalf("Error loading config file from from %s! Error was %s", opaConfigPath, err)
	}

	//TODO HACK
	//OPA in SDK mode doesn't support env-var substitution or overrides for the config file
	//BOO
	//so inject env secrets by hand with this nonsense
	configString := string(opaConfig)
	configString = strings.Replace(configString, "${CR_PAT}", opaPolicyPullSecret, 1)
	opaConfig = []byte(configString)

	//Annoyingly, OPA defines its own (incompatible with both Zap AND Go std logger)
	// logging interface - so for now just create a second logger and match logging level with zap.
	// TODO redirect this into zap logger stream for structured logging.
	logLevel := opalog.Info
	if zapDebug := logger.Desugar().Check(zap.DebugLevel, "debugging"); zapDebug != nil {
		logLevel = opalog.Debug
	}
	opaLogger := opalog.New()
	opaLogger.SetLevel(logLevel)

	opa, err := sdk.New(opaCtx, sdk.Options{Config: bytes.NewReader(opaConfig), Logger: opaLogger})
	if err != nil {
		logger.Fatal(err)
	}

	logger.Info("OPA Engine successfully started")

	// Return a shutdown func the caller can use to dispose OPA engine
	shutdownFunc = func() {
		logger.Info("Shutting down OPA engine")
		opa.Stop(opaCtx)
		// Cancel context - probably redundant in most cases
		opaCtxCancel()
	}

	return OPAPDPEngine{logger, opa}, shutdownFunc
}

func (pdp *OPAPDPEngine) ApplyEntitlementPolicy(primaryEntity string, secondaryEntities []string, idpContextJSON string, parentCtx ctx.Context) ([]handlers.EntityEntitlement, error) {
	pdp.logger.Debug("ApplyEntitlementPolicy")
	evalCtx, evalSpan := tracer.Start(parentCtx, "ApplyEntitlementPolicy")
	defer evalSpan.End()

	pdp.logger.Debug("IDP CONTEXT JSON: %s", idpContextJSON)

	inputDoc, err := pdp.buildInputDoc(primaryEntity, secondaryEntities, idpContextJSON)
	if err != nil {
		pdp.logger.Errorf("Error constructing input document, error was %s", err)
		return nil, err
	}

	pdp.logger.Debug("INPUT DOC is %s", inputDoc)

	decisionReq := sdk.DecisionOptions{
		Now:   time.Now(),
		Path:  "virtru/entitlement/generated_entitlements",
		Input: inputDoc,
	}

	result, err := pdp.opa.Decision(evalCtx, decisionReq)
	if err != nil {
		pdp.logger.Errorf("Got OPA decision error: %s", err)
		return nil, err
	}

	decis, err := pdp.deserializeEntitlementsFromResult(result)
	if err != nil {
		pdp.logger.Errorf("Error deserializing OPA result, error was %s", err)
		return nil, err
	}

	pdp.logger.Debug("Got unmarshalled entitlements: %+v", decis.Result)

	return decis.Result, err
}

func (pdp *OPAPDPEngine) deserializeEntitlementsFromResult(rawResult *sdk.DecisionResult) (*Decision, error) {
	pdp.logger.Debugf("Got OPA raw result: %s", rawResult)

	//Marshal that entire doc BACK to a string.
	resDoc, err := json.Marshal(rawResult)
	if err != nil {
		pdp.logger.Errorf("Error re-marshalling result doc! Error was %s", err)
		return nil, err
	}

	pdp.logger.Debug("Tmp string result is %s", string(resDoc))

	var decis Decision
	err = json.Unmarshal([]byte(resDoc), &decis)
	if err != nil {
		pdp.logger.Errorf("Could not deserialize final JSON result document! Error was %s", err)
		return nil, err
	}

	return &decis, nil
}

func (pdp *OPAPDPEngine) buildInputDoc(primaryEntity string, secondaryEntities []string, idpContextJSON string) (map[string]interface{}, error) {
	//The unstructured input must be first deserialized into a generic-but-concrete type, so we can embed it
	// as such as a subfield in the larger input document.
	//
	// Can't skip this step, because otherwise JSON encoding will rightly treat it as an escaped JSON string -
	// this, even though it feels redundant, is the safest and most foolproof approach.
	var idpContext map[string]interface{}

	//If this was not defined, use empty JSON object
	if idpContextJSON == "" {
		idpContextJSON = "{}"
	}

	err := json.Unmarshal([]byte(idpContextJSON), &idpContext)
	if err != nil {
		pdp.logger.Errorf("Could not deserialize generic IdP context JSON input document! Error was %s", err)
		return nil, err
	}

	//Build the toplevel input doc.
	inputDoc := entitlementDecisionInputDocument{primaryEntity, secondaryEntities, idpContext}

	//Marshal that entire doc BACK to a string.
	tmpDoc, err := json.Marshal(inputDoc)
	if err != nil {
		pdp.logger.Errorf("Error re-marshalling input doc! Error was %s", err)
		return nil, err
	}

	pdp.logger.Debug("Tmp result is %s", string(tmpDoc))
	//OPA wants this as a generic map[string]interface{} and will not handle
	//deserializing to concrete structs
	//So, we deserialize the whole thing again into a generic `map[string]interface{}`
	var inputUnstructured map[string]interface{}
	err = json.Unmarshal([]byte(tmpDoc), &inputUnstructured)
	if err != nil {
		pdp.logger.Errorf("Could not deserialize final JSON input document! Error was %s", err)
		return nil, err
	}

	pdp.logger.Debug("Final doc is %+v", inputUnstructured)

	return inputUnstructured, nil
}
