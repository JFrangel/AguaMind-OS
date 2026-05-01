package handlers

import "github.com/gin-gonic/gin"

func RagSearch(c *gin.Context) {
	proxyJSON(c, "/rag/search")
}

func RagIngest(c *gin.Context) {
	proxyMultipart(c, "/rag/ingest")
}
