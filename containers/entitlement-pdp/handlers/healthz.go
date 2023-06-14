package handlers

import (
	"net/http"

	"go.uber.org/zap"
)

type Healthz struct {
	ready  bool
	ZapLog *zap.Logger
}

func (h *Healthz) ServeHTTP(w http.ResponseWriter, _ *http.Request) {
	if !h.ready {
		h.ZapLog.Info("service not ready!")
		http.Error(w, http.StatusText(http.StatusServiceUnavailable), http.StatusServiceUnavailable)
		return
	}
	w.WriteHeader(http.StatusOK)
}

func (h *Healthz) MarkHealthy() {
	h.ZapLog.Info("Marking service healthy")
	h.ready = true
}
