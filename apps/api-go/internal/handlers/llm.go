package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"

	"github.com/agentos/api-go/internal/llm"
)

// CompleteRequest is the public Go-API shape for a sync completion call.
type CompleteRequest struct {
	Prompt  string `json:"prompt" binding:"required"`
	System  string `json:"system,omitempty"`
	Cascade string `json:"cascade,omitempty"`
}

// Complete is a low-latency sync completion endpoint. It routes through the
// FastAPI LLMFactory by default (so cascade + circuit breaker apply) but
// can be flipped to direct provider calls with LLM_DIRECT=true.
func Complete(client *llm.Client) gin.HandlerFunc {
	return func(c *gin.Context) {
		var req CompleteRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"data": nil, "error": err.Error()})
			return
		}

		messages := []llm.Message{}
		if req.System != "" {
			messages = append(messages, llm.Message{Role: "system", Content: req.System})
		}
		messages = append(messages, llm.Message{Role: "user", Content: req.Prompt})

		resp, err := client.Complete(c.Request.Context(), llm.CompleteRequest{
			Messages: messages,
			Cascade:  req.Cascade,
		})
		if err != nil {
			c.JSON(http.StatusBadGateway, gin.H{"data": nil, "error": err.Error()})
			return
		}

		c.JSON(http.StatusOK, gin.H{"data": resp, "error": nil})
	}
}
