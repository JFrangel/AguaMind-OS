package handlers

import (
	"encoding/json"
	"io"
	"net/http"
	"os"
	"time"

	"github.com/gin-gonic/gin"
)

func Health(c *gin.Context) {
	backendURL := os.Getenv("BACKEND_URL")
	if backendURL == "" {
		backendURL = "http://localhost:8000"
	}

	client := &http.Client{Timeout: 3 * time.Second}
	resp, err := client.Get(backendURL + "/health")
	if err != nil {
		c.JSON(http.StatusOK, gin.H{
			"status":    "down",
			"service":   "agentos-go",
			"providers": gin.H{},
			"timestamp": time.Now().Unix(),
			"reason":    "backend unreachable",
		})
		return
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		c.JSON(http.StatusOK, gin.H{
			"status":    "degraded",
			"service":   "agentos-go",
			"timestamp": time.Now().Unix(),
		})
		return
	}

	var upstream map[string]any
	if err := json.Unmarshal(body, &upstream); err != nil {
		c.Data(resp.StatusCode, "application/json", body)
		return
	}
	upstream["service"] = "agentos-go"
	c.JSON(http.StatusOK, upstream)
}
