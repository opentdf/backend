package handlers

import (
	"fmt"
	"net/http"
)

var isReady bool = false

func MarkHealthy() {
	fmt.Println("Marking service healthy")
	isReady = true
}

// GetHealthz godoc
// @Summary      Check service status
// @Tags         Service Health
// @Success      200
// @Failure      503 {string} http.StatusServiceUnavailable
// @Router       /healthz [get]
func GetHealthzHandler() http.Handler {
	healthzHandler := func(w http.ResponseWriter, req *http.Request) {
		if !isReady {
			fmt.Println("service not ready!")
			http.Error(w, http.StatusText(http.StatusServiceUnavailable), http.StatusServiceUnavailable)
			return
		}
		w.WriteHeader(http.StatusOK)
	}

	return http.HandlerFunc(healthzHandler)
}
