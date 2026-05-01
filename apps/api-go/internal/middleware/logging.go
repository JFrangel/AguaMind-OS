package middleware

import (
	"log"
	"time"

	"github.com/gin-gonic/gin"
)

// Logger emits a structured one-line entry per request:
//   GET  /api/v1/chat 200 124ms ip=1.2.3.4 user=abc
func Logger() gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		c.Next()

		userID, _ := c.Get("user_id")
		log.Printf(
			"%-6s %-30s %d %12s ip=%s user=%v",
			c.Request.Method,
			c.Request.URL.Path,
			c.Writer.Status(),
			time.Since(start).Round(time.Millisecond),
			c.ClientIP(),
			userID,
		)
	}
}
