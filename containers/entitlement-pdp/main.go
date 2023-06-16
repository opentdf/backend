package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"time"

	"github.com/caarlos0/env"

	"github.com/opentdf/v2/entitlement-pdp/handlers"
	"github.com/opentdf/v2/entitlement-pdp/pdp"

	log "github.com/sirupsen/logrus"
	"github.com/virtru/oteltracer"
	"go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
)

const (
	svcName = "entitlement-pdp"

	ErrOpenapiNotFound = "openapi not found"
)

func init() {
	log.SetOutput(os.Stdout)
	if os.Getenv("SERVER_LOG_JSON") == "true" {
		log.SetFormatter(&log.JSONFormatter{
			TimestampFormat:   "",
			DisableTimestamp:  false,
			DisableHTMLEscape: false,
			DataKey:           "",
			FieldMap:          nil,
			CallerPrettyfier:  nil,
			PrettyPrint:       false,
		})
	}
	if os.Getenv("VERBOSE") == "true" {
		log.SetLevel(log.TraceLevel)
	}
}

var (
	Version string
	cfg     EnvConfig
)

// EnvConfig environment variable struct.
type EnvConfig struct {
	Port                string `env:"SERVER_PORT" envDefault:"3355"`
	PublicName          string `env:"SERVER_PUBLIC_NAME" envDefault:""`
	Verbose             bool   `env:"VERBOSE" envDefault:"false"`
	DisableTracing      bool   `env:"DISABLE_TRACING" envDefault:"false"`
	OPAConfigPath       string `env:"OPA_CONFIG_PATH" envDefault:"/etc/opa/config/opa-config.yaml"`
	OPAPolicyPullSecret string `env:"OPA_POLICYBUNDLE_PULLCRED" envDefault:""`
}

// @title entitlement-pdp
// @version 0.0.1
// @description An implementation of a Policy Decision Point

// @contact.name OpenTDF
// @contact.url https://www.opentdf.io

// @license.name BSD 3-Clause
// @license.url https://opensource.org/licenses/BSD-3-Clause
func main() {
	log.WithFields(log.Fields{
		svcName: Version,
	}).Info("starting")
	// Parse env
	if err := env.Parse(&cfg); err != nil {
		log.Fatal(err.Error())
	}

	// load openapi
	openapi, err := os.ReadFile("./openapi.json")
	if err != nil {
		log.Fatal(err)
	}

	if !cfg.DisableTracing {
		tracerCancel, err := oteltracer.InitTracer(svcName)
		if err != nil {
			log.Errorf("Error initializing tracer: %v", err)
		}
		defer tracerCancel()
	}
	opaPDP, opaPDPCancel := pdp.InitOPAPDP(cfg.OPAConfigPath, cfg.OPAPolicyPullSecret, context.Background())
	defer opaPDPCancel()

	const timeout = 30
	server := &http.Server{
		Addr:              fmt.Sprintf("%s:%s", cfg.PublicName, cfg.Port),
		ReadTimeout:       time.Second * timeout,
		WriteTimeout:      time.Second * timeout,
		ReadHeaderTimeout: time.Second * timeout,
	}

	healthz := handlers.Healthz{}
	// This otel HTTP handler middleware simply traces all handled request for you - DD needs it
	http.Handle("/healthz", otelhttp.NewHandler(&healthz, "HealthZHandler"))
	entitlements := handlers.Entitlements{
		Pdp: &opaPDP,
	}
	http.Handle("/entitlements", otelhttp.NewHandler(&entitlements, "EntitlementsHandler"))
	swagger := OpenapiHandler{
		Address: server.Addr,
		Openapi: openapi,
	}
	http.Handle("/docs/", &swagger)
	http.Handle("/openapi.json", &swagger)

	log.WithFields(log.Fields{"address": server.Addr}).Infof("Starting server")
	healthz.MarkHealthy()
	if err := server.ListenAndServe(); err != nil {
		log.Panic("Error on serve!", err)
	}
}

type OpenapiHandler struct {
	Address string
	Openapi []byte
}

func (h OpenapiHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	log.Debugf("openapi request %s", r.URL)
	// FIXME replace OpenAPI server with this
	// .URL(fmt.Sprintf("http://%s/docs/doc.json", h.Address)) // The url pointing to API definition
	if h.Openapi == nil {
		log.Error(ErrOpenapiNotFound)
		w.WriteHeader(http.StatusNotFound)
		_, err := w.Write([]byte(http.StatusText(http.StatusNotFound)))
		if err != nil {
			log.Error(err)
			return
		}
		return
	}
	w.Header().Set("Content-Type", "application/json")
	_, err := w.Write(h.Openapi)
	if err != nil || h.Openapi == nil {
		log.Error(err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
}
