package main

import (
	"log"
	"os"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"

	"github.com/agentos/api-go/internal/handlers"
	"github.com/agentos/api-go/internal/llm"
	"github.com/agentos/api-go/internal/middleware"
)

func main() {
	_ = godotenv.Load()

	port := os.Getenv("GO_API_PORT")
	if port == "" {
		port = "8080"
	}

	rateLimit := 60
	if v := os.Getenv("RATE_LIMIT_PER_MINUTE"); v != "" {
		if n, err := strconv.Atoi(v); err == nil && n > 0 {
			rateLimit = n
		}
	}

	llmClient := llm.New()

	r := gin.New()
	r.Use(gin.Recovery())
	r.Use(middleware.Logger())
	r.Use(middleware.CORS())
	r.Use(middleware.RateLimit(rateLimit))

	r.GET("/health", handlers.Health)

	api := r.Group("/api/v1")
	api.Use(middleware.JWTAuth())
	{
		api.POST("/chat", handlers.Chat)
		api.POST("/complete", handlers.Complete(llmClient))

		geo := api.Group("/geo")
		{
			geo.POST("/geocode", handlers.Geocode)
			geo.POST("/reverse", handlers.ReverseGeocode)
		}

		rag := api.Group("/rag")
		{
			rag.POST("/search", handlers.RagSearch)
			rag.POST("/ingest", handlers.RagIngest)
		}

		api.POST("/reports/generate", handlers.GenerateReport)
	}

	log.Printf("AgentOS Go API starting on :%s (rate=%d/min, direct=%v)", port, rateLimit, llmClient.Direct)
	if err := r.Run(":" + port); err != nil {
		log.Fatal(err)
	}
}
