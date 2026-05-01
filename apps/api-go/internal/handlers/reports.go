package handlers

import (
	"io"
	"net/http"

	"github.com/gin-gonic/gin"
)

func GenerateReport(c *gin.Context) {
	resp, err := http.Post(backendURL()+"/reports/generate", "application/json", c.Request.Body)
	if err != nil {
		c.JSON(http.StatusBadGateway, gin.H{"error": "backend unavailable"})
		return
	}
	defer resp.Body.Close()

	if ct := resp.Header.Get("Content-Type"); ct != "" {
		c.Header("Content-Type", ct)
	}
	if cd := resp.Header.Get("Content-Disposition"); cd != "" {
		c.Header("Content-Disposition", cd)
	}
	c.Status(resp.StatusCode)
	io.Copy(c.Writer, resp.Body)
}
