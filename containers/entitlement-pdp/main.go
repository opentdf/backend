package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/opentdf/v2/entitlement-pdp/handlers"

	"github.com/opentdf/v2/entitlement-pdp/pdp"

	"github.com/virtru/oteltracer"
	"go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"

	"github.com/caarlos0/env"
	"go.uber.org/zap"
)

var svcName = "entitlement-pdp"

var cfg EnvConfig

// EnvConfig environment variable struct.
type EnvConfig struct {
	ListenPort          string `env:"LISTEN_PORT" envDefault:"3355"`
	ExternalHost        string `env:"EXTERNAL_HOST" envDefault:""`
	Verbose             bool   `env:"VERBOSE" envDefault:"false"`
	DisableTracing      bool   `env:"DISABLE_TRACING" envDefault:"false"`
	OPAConfigPath       string `env:"OPA_CONFIG_PATH" envDefault:"/etc/opa/config/opa-config.yaml"`
	OPAPolicyPullSecret string `env:"OPA_POLICYBUNDLE_PULLCRED" envDefault:"YOURPATHERE"`
}

// @title entitlement-pdp
// @version 0.0.1
// @description An implementation of a Policy Decision Point

// @contact.name OpenTDF
// @contact.url https://www.opentdf.io

// @license.name BSD 3-Clause
// @license.url https://opensource.org/licenses/BSD-3-Clause
func main() {
	var zapLog *zap.Logger
	var logErr error

	// Parse env
	if err := env.Parse(&cfg); err != nil {
		log.Fatal(err.Error())
	}

	if cfg.Verbose {
		log.Print("Enabling verbose logging")
		zapLog, logErr = zap.NewDevelopment() // or NewProduction, or NewDevelopment
	} else {
		log.Print("Enabling production logging")
		zapLog, logErr = zap.NewProduction()
	}

	if logErr != nil {
		log.Fatalf("Logger initialization failed!")
	}

	defer func() {
		err := zapLog.Sync()
		if err != nil {
			log.Fatal("Error flushing zap log!")
		}
	}()

	logger := zapLog.Sugar()

	logger.Infof("%s init", svcName)

	if !cfg.DisableTracing {
		tracerCancel, err := oteltracer.InitTracer(svcName)
		if err != nil {
			logger.Errorf("Error initializing tracer: %v", err)
		}
		defer tracerCancel()
	}

	opaPDP, opaPDPCancel := pdp.InitOPAPDP(cfg.OPAConfigPath, cfg.OPAPolicyPullSecret, logger, context.Background())
	defer opaPDPCancel()

	const timeout = 30
	server := &http.Server{
		Addr:              fmt.Sprintf("%s:%s", cfg.ExternalHost, cfg.ListenPort),
		ReadTimeout:       time.Second * timeout,
		WriteTimeout:      time.Second * timeout,
		ReadHeaderTimeout: time.Second * timeout,
	}

	healthz := new(handlers.Healthz)
	// This otel HTTP handler middleware simply traces all handled request for you - DD needs it
	http.Handle("/healthz", otelhttp.NewHandler(healthz, "HealthZHandler"))
	entitlements := handlers.Entitlements{
		Pdp:    &opaPDP,
		Logger: logger,
	}
	http.Handle("/entitlements", otelhttp.NewHandler(entitlements, "EntitlementsHandler"))
	swagger := handlers.Swagger{
		Address: server.Addr,
	}
	http.Handle("/docs/", swagger)

	logger.Info("Starting server", zap.String("address", server.Addr))
	healthz.MarkHealthy()
	if err := server.ListenAndServe(); err != nil {
		logger.Fatal("Error on serve!", zap.Error(err))
	}
}
