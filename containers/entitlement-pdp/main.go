package main

import (
	"context"
	"fmt"
	"github.com/caarlos0/env"
	"github.com/opentdf/v2/entitlement-pdp/handlers"
	"github.com/opentdf/v2/entitlement-pdp/pdp"
	log "github.com/sirupsen/logrus"
	"github.com/uptrace/opentelemetry-go-extra/otellogrus"
	"go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/exporters/jaeger"
	"go.opentelemetry.io/otel/exporters/stdout/stdoutmetric"
	"go.opentelemetry.io/otel/exporters/stdout/stdouttrace"
	"go.opentelemetry.io/otel/propagation"
	sdkmetric "go.opentelemetry.io/otel/sdk/metric"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.17.0"
	"net/http"
	"os"
	"os/signal"
	"time"
)

const (
	service = "entitlement-pdp"

	ErrOpenapiNotFound = "openapi not found"
)

func init() {
	log.SetOutput(os.Stdout)
	// Instrument logrus.
	log.AddHook(otellogrus.NewHook(otellogrus.WithLevels(
		log.PanicLevel,
		log.FatalLevel,
		log.ErrorLevel,
		log.WarnLevel,
	)))
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
	DisableTracing      bool   `env:"DISABLE_TRACING" envDefault:"false"`
	OPAConfigPath       string `env:"OPA_CONFIG_PATH" envDefault:"/etc/opa/config/opa-config.yaml"`
	OPAPolicyPullSecret string `env:"OPA_POLICYBUNDLE_PULLCRED" envDefault:""`
}

func main() {
	log.WithFields(log.Fields{
		service: Version,
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
	// otel tracer
	// TODO if no OTEL_JAEGER or OTEL_PROMETHEUS
	// TODO ref https://github.com/open-telemetry/opentelemetry-go/tree/main/exporters
	// TODO https://docs.datadoghq.com/tracing/trace_collection/opentracing/go/
	//tp, err := initTracer()
	//if err != nil {
	//	log.Fatal(err)
	//}
	//defer func() {
	//	if err := tp.Shutdown(context.Background()); err != nil {
	//		log.Printf("Error shutting down tracer provider: %v", err)
	//	}
	//}()
	// TODO if os.Getenv("OTEL_JAEGER") then
	tp, err := tracerProvider("http://localhost:14268/api/traces")
	if err != nil {
		log.Fatal(err)
	}
	// Register our TracerProvider as the global so any imported
	// instrumentation in the future will default to using it.
	otel.SetTracerProvider(tp)
	// otel meter
	mp, err := initMeter()
	if err != nil {
		log.Fatal(err)
	}
	defer func() {
		if err := mp.Shutdown(context.Background()); err != nil {
			log.Printf("Error shutting down meter provider: %v", err)
		}
	}()
	// healthz
	healthz := handlers.Healthz{}
	http.Handle("/healthz", &healthz)
	// openapi
	openapiHandler := OpenapiHandler{
		Address: fmt.Sprintf("https://%s", os.Getenv("SERVER_PUBLIC_NAME")),
		Openapi: openapi,
	}
	http.Handle("/docs/", &openapiHandler)
	http.Handle("/openapi.json", &openapiHandler)
	// opa
	opaPDP, opaPDPCancel := pdp.InitOPAPDP(cfg.OPAConfigPath, cfg.OPAPolicyPullSecret, context.Background())
	// entitlements
	entitlements := handlers.Entitlements{
		Pdp: &opaPDP,
	}
	http.Handle("/entitlements", otelhttp.NewHandler(&entitlements, "Entitlements"))
	//http.Handle("/entitlements", &entitlements)
	// ready - TODO don't block above on OPA startup, but once complete mark healthy
	healthz.MarkHealthy()
	// os interrupt
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt)
	// server
	const timeout = 30 * time.Second
	port := os.Getenv("SERVER_PORT")
	if port == "" {
		port = "3355"
	}
	server := &http.Server{
		Addr:              fmt.Sprintf("0.0.0.0:%s", port),
		ReadTimeout:       timeout,
		WriteTimeout:      timeout,
		ReadHeaderTimeout: timeout,
	}
	// start server
	go func() {
		log.Printf("listening on http://%s", server.Addr)
		if err := server.ListenAndServe(); err != nil {
			log.Printf("shutting on http://%s", server.Addr)
			opaPDPCancel()
			log.Fatal(err)
		}
	}()
	<-stop
	err = server.Shutdown(context.Background())
	if err != nil {
		log.Println(err)
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

func initTracer() (*sdktrace.TracerProvider, error) {
	// Create stdout exporter to be able to retrieve
	// the collected spans.
	exporter, err := stdouttrace.New(stdouttrace.WithPrettyPrint())
	if err != nil {
		return nil, err
	}

	//prv, err := sdktrace.NewProvider(sdktrace.ProviderConfig{
	//	JaegerEndpoint: "http://localhost:14268/api/traces",
	//	ServiceName:    "server",
	//	ServiceVersion: "2.0.0",
	//	Environment:    "dev",
	//	Disabled:       false,
	//})
	//if err != nil {
	//	log.Fatalln(err)
	//}
	//defer prv.Close(ctx)
	// For the demonstration, use sdktrace.AlwaysSample sampler to sample all traces.
	// In a production application, use sdktrace.ProbabilitySampler with a desired probability.
	tp := sdktrace.NewTracerProvider(
		sdktrace.WithSampler(sdktrace.AlwaysSample()),
		sdktrace.WithBatcher(exporter),
		sdktrace.WithResource(resource.NewWithAttributes(semconv.SchemaURL, semconv.ServiceName("ExampleService"))),
	)
	otel.SetTracerProvider(tp)
	otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(propagation.TraceContext{}, propagation.Baggage{}))
	return tp, err
}

func initMeter() (*sdkmetric.MeterProvider, error) {
	exp, err := stdoutmetric.New()
	if err != nil {
		return nil, err
	}

	mp := sdkmetric.NewMeterProvider(sdkmetric.WithReader(sdkmetric.NewPeriodicReader(exp)))
	otel.SetMeterProvider(mp)
	return mp, nil
}

const (
	environment = "production"
	id          = 1
)

// tracerProvider returns an OpenTelemetry TracerProvider configured to use
// the Jaeger exporter that will send spans to the provided url. The returned
// TracerProvider will also use a Resource configured with all the information
// about the application.
func tracerProvider(url string) (*sdktrace.TracerProvider, error) {
	// Create the Jaeger exporter
	exp, err := jaeger.New(jaeger.WithCollectorEndpoint(jaeger.WithEndpoint(url)))
	if err != nil {
		return nil, err
	}
	tp := sdktrace.NewTracerProvider(
		// Always be sure to batch in production.
		sdktrace.WithBatcher(exp),
		// Record information about this application in a Resource.
		sdktrace.WithResource(resource.NewWithAttributes(
			semconv.SchemaURL,
			semconv.ServiceName(service),
			attribute.String("environment", environment),
			attribute.Int64("ID", id),
		)),
	)
	return tp, nil
}
