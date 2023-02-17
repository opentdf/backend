package main

import (
	"context"
	"fmt"
	"github.com/go-redis/redis"
	"log"
	"net/http"
	"os"
	"os/signal"
	"time"
)

func main() {
	log.Println("Configuration service starting")

	openapi, err := os.ReadFile("./openapi.json")
	if err != nil {
		log.Fatal(err)
	}

	client := redis.NewClient(&redis.Options{
		Addr:     "localhost:6379",
		Password: os.Getenv("REDIS_PASSWORD"),
		DB:       0,
	})

	pong, err := client.Ping().Result()
	fmt.Println(pong, err)

	// os interrupt
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt)

	// server
	server := http.Server{
		Addr:         "127.0.0.1:8080",
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  120 * time.Second,
	}
	http.Handle("/", &ConfigurationHandler{
		openapi: openapi,
		client:  client,
	})
	go func() {
		log.Printf("listening on http://%s", server.Addr)
		log.Printf(os.Getenv("SERVICE"))
		if err := server.ListenAndServe(); err != nil {
			log.Fatal(err)
		}
	}()
	<-stop
	err = server.Shutdown(context.Background())
	if err != nil {
		log.Println(err)
	}
}

type ConfigurationHandler struct {
	openapi []byte
	client  *redis.Client
}

func (h ConfigurationHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	log.Println(r.URL)
	if r.URL.Path == "/openapi.json" {
		_, err := w.Write(h.openapi)
		if err != nil {
			log.Println(err)
			return
		}
		return
	}
}
