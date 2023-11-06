package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"time"

	"github.com/opentdf/v2/entitlement-pdp/handlers"
	"github.com/opentdf/v2/entitlement-pdp/pdp"
	log "github.com/sirupsen/logrus"
	"github.com/uptrace/opentelemetry-go-extra/otellogrus"
	"go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/exporters/jaeger"
	"go.opentelemetry.io/otel/exporters/stdout/stdoutmetric"
	"go.opentelemetry.io/otel/exporters/stdout/stdouttrace"
	"go.opentelemetry.io/otel/propagation"
	sdkmetric "go.opentelemetry.io/otel/sdk/metric"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.17.0"
)

const (
	service            = "entitlement-pdp"
	trueEmv            = "true"
	ErrOpenapiNotFound = Error("openapi not found")
	ErrTracer          = Error("tracer issue")
	ErrMeter           = Error("meter issue")
)

func init() {
	log.SetOutput(os.Stdout)
	// Instrument logrus.
	log.AddHook(otellogrus.NewHook(otellogrus.WithLevels(
		log.PanicLevel,
		log.FatalLevel,
		log.ErrorLevel,
		log.WarnLevel,
		log.InfoLevel,
	)))
	if os.Getenv("SERVER_LOG_JSON") == trueEmv {
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
	if os.Getenv("VERBOSE") == trueEmv {
		log.SetLevel(log.TraceLevel)
	}
}

var (
	Version string
)

func main() {
	log.WithFields(log.Fields{
		service: Version,
	}).Info("starting")
	// load openapi
	openapi, err := os.ReadFile("./openapi.json")
	if err != nil {
		log.Fatal(err)
	}
	// Register our TracerProvider as the global so any imported
	// instrumentation in the future will default to using it.
	if os.Getenv("DISABLE_TRACING") != trueEmv {
		// otel tracer
		tp, err := initTracer()
		if err != nil {
			log.Fatal(err)
		}
		defer func() {
			if err := tp.Shutdown(context.Background()); err != nil {
				log.Printf("Error shutting down tracer provider: %v", err)
			}
		}()
		otel.SetTracerProvider(tp)
		// otel meter
		mp, err := initMeter()
		if err != nil {
			log.Panic(err)
		}
		defer func() {
			if err := mp.Shutdown(context.Background()); err != nil {
				log.Printf("Error shutting down meter provider: %v", err)
			}
		}()
	}
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
	go func() {
		// opa
		opaPDP, opaPDPCancel, err := pdp.InitOPAPDP(context.Background())
		if err != nil {
			log.Panic(err)
		}
		defer opaPDPCancel()
		// entitlements
		entitlements := handlers.Entitlements{
			Pdp: &opaPDP,
		}
		http.Handle("/entitlements", otelhttp.NewHandler(&entitlements, "Entitlements"))
		// ready - TODO don't block above on OPA startup, but once complete mark healthy
		healthz.MarkHealthy()
	}()
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

// initTracer creates otel tracer based on env vars
// TODO if no OTEL_EXPORTER_JAEGER_AGENT_HOST or OTEL_PROMETHEUS
// TODO ref https://github.com/open-telemetry/opentelemetry-go/tree/main/exporters
// TODO https://docs.datadoghq.com/tracing/trace_collection/opentracing/go/
func initTracer() (*sdktrace.TracerProvider, error) {
	var exporter sdktrace.SpanExporter
	var err error
	jaegerHost := os.Getenv("OTEL_EXPORTER_JAEGER_AGENT_HOST")
	if jaegerHost != "" {
		exporter, err = jaeger.New(jaeger.WithCollectorEndpoint(jaeger.WithEndpoint(jaegerHost)))
		if err != nil {
			return nil, ErrJoin(ErrTracer, err)
		}
	} else {
		// Create stdout exporter to be able to retrieve
		// the collected spans.
		exporter, err = stdouttrace.New(stdouttrace.WithPrettyPrint())
		if err != nil {
			return nil, ErrJoin(ErrTracer, err)
		}
	}
	// For the demonstration, use sdktrace.AlwaysSample sampler to sample all traces.
	// In a production application, use sdktrace.ProbabilitySampler with a desired probability.
	tp := sdktrace.NewTracerProvider(
		sdktrace.WithSampler(sdktrace.AlwaysSample()),
		sdktrace.WithBatcher(exporter),
		sdktrace.WithResource(resource.NewWithAttributes(semconv.SchemaURL, semconv.ServiceName(service))),
	)
	otel.SetTracerProvider(tp)
	otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(propagation.TraceContext{}, propagation.Baggage{}))
	return tp, nil
}

func initMeter() (*sdkmetric.MeterProvider, error) {
	exp, err := stdoutmetric.New()
	if err != nil {
		return nil, ErrJoin(ErrMeter, err)
	}

	mp := sdkmetric.NewMeterProvider(sdkmetric.WithReader(sdkmetric.NewPeriodicReader(exp)))
	otel.SetMeterProvider(mp)
	return mp, nil
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
