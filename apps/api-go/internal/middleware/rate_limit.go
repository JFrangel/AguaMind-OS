package middleware

import (
	"net/http"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
)

// RateLimit returns a sliding-window per-IP limiter. The state is in-memory
// and process-local — fine for a single Koyeb nano instance, swap for Redis
// when scaling horizontally.
func RateLimit(requestsPerMinute int) gin.HandlerFunc {
	if requestsPerMinute <= 0 {
		requestsPerMinute = 60
	}
	window := time.Minute

	type bucket struct {
		mu    sync.Mutex
		times []time.Time
	}
	buckets := sync.Map{}

	return func(c *gin.Context) {
		if c.FullPath() == "/health" {
			c.Next()
			return
		}

		key := clientIP(c)
		v, _ := buckets.LoadOrStore(key, &bucket{})
		b := v.(*bucket)

		b.mu.Lock()
		now := time.Now()
		cutoff := now.Add(-window)
		fresh := b.times[:0]
		for _, t := range b.times {
			if t.After(cutoff) {
				fresh = append(fresh, t)
			}
		}
		b.times = fresh

		if len(b.times) >= requestsPerMinute {
			retryAfter := int(window.Seconds() - now.Sub(b.times[0]).Seconds())
			if retryAfter < 1 {
				retryAfter = 1
			}
			b.mu.Unlock()
			c.Header("Retry-After", strconv.Itoa(retryAfter))
			c.AbortWithStatusJSON(http.StatusTooManyRequests, gin.H{
				"data":  nil,
				"error": "rate_limit_exceeded",
				"meta":  gin.H{"retry_after": retryAfter},
			})
			return
		}
		b.times = append(b.times, now)
		remaining := requestsPerMinute - len(b.times)
		b.mu.Unlock()

		c.Header("X-RateLimit-Limit", strconv.Itoa(requestsPerMinute))
		c.Header("X-RateLimit-Remaining", strconv.Itoa(remaining))
		c.Next()
	}
}

func clientIP(c *gin.Context) string {
	if fwd := c.GetHeader("X-Forwarded-For"); fwd != "" {
		return strings.TrimSpace(strings.Split(fwd, ",")[0])
	}
	return c.ClientIP()
}
