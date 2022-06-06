package main

import (
	"context"
	"fmt"
	"log"
	"net/http"

	"github.com/virtru/v2/entitlement-pdp/handlers"

	"github.com/virtru/v2/entitlement-pdp/pdp"

	"github.com/virtru/oteltracer"

	"github.com/caarlos0/env"
	"go.uber.org/zap"
)

var svcName = "entitlement-pdp"

var cfg EnvConfig

//Env config
type EnvConfig struct {
	ListenPort string `env:"LISTEN_PORT" envDefault:"3355"`
	ExternalHost string `env:"EXTERNAL_HOST" envDefault:""`
	Verbose bool `env:"VERBOSE" envDefault:"false"`
	DisableTracing bool `env:"DISABLE_TRACING" envDefault:"false"`
	OPAConfigPath string `env:"OPA_CONFIG_PATH" envDefault:"/etc/opa/config/opa-config.yaml"`
	OPAPolicyPullSecret string `env:"OPA_POLICYBUNDLE_PULLCRED" envDefault:"YOURPATHERE"`
}

// @title entitlement-pdp
// @version 0.0.1
// @description An implementation of a Policy Decision Point

// @contact.name Virtru
// @contact.url https://www.virtru.com

// @license.name BSD 3-Clause
// @license.url https://opensource.org/licenses/BSD-3-Clause

// @BasePath /v1
func main() {
	var zapLog *zap.Logger
	var logErr error

	// Parse env
	if err := env.Parse(&cfg); err != nil {
		log.Fatal(err.Error())
	}

	if cfg.Verbose {
		fmt.Print("Enabling verbose logging")
		zapLog, logErr = zap.NewDevelopment() // or NewProduction, or NewDevelopment
	} else {
		fmt.Print("Enabling production logging")
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

	server := &http.Server{
		Addr: fmt.Sprintf("%s:%s", cfg.ExternalHost, cfg.ListenPort),
	}

	http.Handle("/healthz", handlers.GetHealthzHandler())

	http.Handle("/entitlements", handlers.GetEntitlementsHandler(&opaPDP, logger))

	http.Handle("/swagger/", handlers.GetSwaggerHandler(server.Addr))

	logger.Info("Starting server", zap.String("address", server.Addr))
	handlers.MarkHealthy()
	if err := server.ListenAndServe(); err != nil {
		logger.Fatal("Error on serve!", zap.Error(err))
	}
}
