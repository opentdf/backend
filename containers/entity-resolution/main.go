package main

import (
	"fmt"
	"log"
	"time"
	"net/http"

	"github.com/caarlos0/env"
	"github.com/opentdf/v2/entity-resolution/handlers"

	"go.uber.org/zap"

	"github.com/virtru/oteltracer"
	"go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
)

var cfg EnvConfig
var svcName = "entity-resolution"

type EnvConfig struct {
	KeycloakUrl          string `env:"KEYCLOAK_URL" envDefault:"http://localhost:8080"`
	KeycloakRealm        string `env:"KEYCLOAK_REALM" envDefault:"tdf"`
	KeycloakClientId     string `env:"KEYCLOAK_CLIENT_ID" envDefault:"tdf-entity-resolution-service"`
	KeycloakClientSecret string `env:"KEYCLOAK_CLIENT_SECRET"`
	//See https://github.com/Nerzal/gocloak/issues/346
	LegacyKeycloak bool   `env:"KEYCLOAK_LEGACY" envDefault:"false"`
	ServerPort     string `env:"SERVER_PORT" envDefault:"7070"`
	ExternalHost   string `env:"EXTERNAL_HOST" envDefault:""`
	Verbose        bool   `env:"VERBOSE" envDefault:"false"`
	DisableTracing bool   `env:"DISABLE_TRACING" envDefault:"false"`
}

// @title entitlement-resolution-service
// @version 0.0.1
// @description An implementation of a an entity resolution service for keycloak

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

	server := &http.Server{
		Addr:              fmt.Sprintf("%s:%s", cfg.ExternalHost, cfg.ServerPort),
		ReadTimeout:       time.Second * 30,
		WriteTimeout:      time.Second * 30,
		ReadHeaderTimeout: time.Second * 30,
	}

	http.Handle("/docs/", handlers.GetSwaggerHandler(server.Addr))
	http.Handle("/healthz", otelhttp.NewHandler(handlers.GetHealthzHandler(), "HealthZHandler"))
	http.Handle("/resolve", otelhttp.NewHandler(handlers.GetEntityResolutionHandler(
		handlers.KeyCloakConfg{
			Url:            cfg.KeycloakUrl,
			Realm:          cfg.KeycloakRealm,
			LegacyKeycloak: cfg.LegacyKeycloak,
			ClientId:       cfg.KeycloakClientId,
			ClientSecret:   cfg.KeycloakClientSecret}, logger), "EntityResolutionHandler"))

	logger.Info("Starting server", zap.String("address", server.Addr))

	handlers.MarkHealthy()

	if err := server.ListenAndServe(); err != nil {
		logger.Fatal("Error on serve!", zap.Error(err))
	}
}
