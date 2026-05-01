package middleware

import (
	"net/http"
	"os"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
)

// JWTAuth verifies a Supabase JWT (HS256) and exposes claims via context.
// When AUTH_REQUIRED is unset or false, requests without a token still pass
// through — useful for hackathon demos where login is optional.
func JWTAuth() gin.HandlerFunc {
	required := strings.EqualFold(os.Getenv("AUTH_REQUIRED"), "true")
	secret := os.Getenv("SUPABASE_JWT_SECRET")
	if secret == "" {
		secret = os.Getenv("SUPABASE_SERVICE_KEY")
	}

	return func(c *gin.Context) {
		header := c.GetHeader("Authorization")
		if header == "" {
			if required {
				c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "missing authorization"})
				return
			}
			c.Next()
			return
		}

		parts := strings.SplitN(header, " ", 2)
		if len(parts) != 2 || !strings.EqualFold(parts[0], "Bearer") {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "malformed authorization header"})
			return
		}

		token, err := jwt.Parse(parts[1], func(t *jwt.Token) (any, error) {
			if _, ok := t.Method.(*jwt.SigningMethodHMAC); !ok {
				return nil, jwt.ErrSignatureInvalid
			}
			return []byte(secret), nil
		}, jwt.WithoutClaimsValidation())

		if err != nil || !token.Valid {
			if required {
				c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "invalid token"})
				return
			}
			c.Next()
			return
		}

		if claims, ok := token.Claims.(jwt.MapClaims); ok {
			if sub, ok := claims["sub"].(string); ok {
				c.Set("user_id", sub)
			}
			if email, ok := claims["email"].(string); ok {
				c.Set("user_email", email)
			}
		}
		c.Next()
	}
}
