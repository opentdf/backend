package handlers

import (
	"log"
	"net/http"
)

type Healthz struct {
	ready bool
}

func (h *Healthz) ServeHTTP(w http.ResponseWriter, _ *http.Request) {
	if !h.ready {
		log.Println("service not ready!")
		http.Error(w, http.StatusText(http.StatusServiceUnavailable), http.StatusServiceUnavailable)
		return
	}
	w.WriteHeader(http.StatusOK)
}

func (h *Healthz) MarkHealthy() {
	log.Println("Marking service healthy")
	h.ready = true
}
