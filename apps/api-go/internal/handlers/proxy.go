package handlers

import (
	"io"
	"net/http"
	"os"

	"github.com/gin-gonic/gin"
)

func backendURL() string {
	if v := os.Getenv("BACKEND_URL"); v != "" {
		return v
	}
	return "http://localhost:8000"
}

// proxyJSON forwards a POST request to the FastAPI backend and copies the JSON response.
func proxyJSON(c *gin.Context, path string) {
	resp, err := http.Post(backendURL()+path, "application/json", c.Request.Body)
	if err != nil {
		c.JSON(http.StatusBadGateway, gin.H{"error": "backend unavailable"})
		return
	}
	defer resp.Body.Close()

	c.Header("Content-Type", "application/json")
	c.Status(resp.StatusCode)
	io.Copy(c.Writer, resp.Body)
}

// proxyMultipart forwards a multipart/form-data request (for file uploads).
func proxyMultipart(c *gin.Context, path string) {
	req, err := http.NewRequest(http.MethodPost, backendURL()+path, c.Request.Body)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	req.Header = c.Request.Header.Clone()

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		c.JSON(http.StatusBadGateway, gin.H{"error": "backend unavailable"})
		return
	}
	defer resp.Body.Close()

	c.Header("Content-Type", resp.Header.Get("Content-Type"))
	c.Status(resp.StatusCode)
	io.Copy(c.Writer, resp.Body)
}
