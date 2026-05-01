package handlers

import (
	"io"
	"net/http"

	"github.com/gin-gonic/gin"
)

func Chat(c *gin.Context) {
	resp, err := http.Post(backendURL()+"/chat/stream", "application/json", c.Request.Body)
	if err != nil {
		c.JSON(http.StatusBadGateway, gin.H{"error": "backend unavailable"})
		return
	}
	defer resp.Body.Close()

	c.Header("Content-Type", "text/event-stream")
	c.Header("Cache-Control", "no-cache")
	c.Header("Connection", "keep-alive")
	c.Header("X-Accel-Buffering", "no")
	c.Status(http.StatusOK)

	io.Copy(c.Writer, resp.Body)
}
