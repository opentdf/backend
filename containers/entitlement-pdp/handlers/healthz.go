package handlers

import (
	"net/http"

	log "github.com/sirupsen/logrus"
)

type Healthz struct {
	ready bool
}

func (h *Healthz) ServeHTTP(w http.ResponseWriter, _ *http.Request) {
	if !h.ready {
		log.Info("service not ready!")
		http.Error(w, http.StatusText(http.StatusServiceUnavailable), http.StatusServiceUnavailable)
		return
	}
	w.WriteHeader(http.StatusOK)
}

func (h *Healthz) MarkHealthy() {
	log.Info("Marking service healthy")
	h.ready = true
}
