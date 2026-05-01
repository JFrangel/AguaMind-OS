package handlers

import "github.com/gin-gonic/gin"

func Geocode(c *gin.Context) {
	proxyJSON(c, "/geo/geocode")
}

func ReverseGeocode(c *gin.Context) {
	proxyJSON(c, "/geo/reverse")
}
