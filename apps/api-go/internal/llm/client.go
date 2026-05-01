// Package llm provides a thin Go client that delegates to AgentOS FastAPI
// LLMFactory (preferred) or falls back to direct provider calls when the
// backend is unavailable. Used by api-go for endpoints that need a sync
// completion without going through the SSE chat path.
package llm

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"
)

// Client is a Go-side abstraction over the LLM cascade. By default it
// proxies to FastAPI so the cascade + circuit breaker logic stays in one
// place. Set DIRECT=true to bypass FastAPI and call Groq directly (useful
// for low-latency Go-only deployments).
type Client struct {
	BackendURL string
	HTTP       *http.Client
	Direct     bool
	GroqKey    string
}

// New constructs a Client from environment variables.
func New() *Client {
	return &Client{
		BackendURL: getenv("BACKEND_URL", "http://localhost:8000"),
		HTTP:       &http.Client{Timeout: 30 * time.Second},
		Direct:     getenv("LLM_DIRECT", "false") == "true",
		GroqKey:    os.Getenv("GROQ_API_KEY"),
	}
}

type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type CompleteRequest struct {
	Messages []Message `json:"messages"`
	Cascade  string    `json:"cascade,omitempty"`
}

type CompleteResponse struct {
	Content   string         `json:"content"`
	Provider  string         `json:"provider"`
	Model     string         `json:"model"`
	Usage     map[string]any `json:"usage,omitempty"`
	LatencyMs float64        `json:"latency_ms,omitempty"`
}

// Complete returns a single completion. When Direct is false, the request
// is forwarded to FastAPI's /agents/complete endpoint. When Direct is
// true, calls Groq directly using OpenAI-compatible chat completions.
func (c *Client) Complete(ctx context.Context, req CompleteRequest) (*CompleteResponse, error) {
	if !c.Direct {
		return c.completeViaBackend(ctx, req)
	}
	return c.completeDirectGroq(ctx, req)
}

func (c *Client) completeViaBackend(ctx context.Context, req CompleteRequest) (*CompleteResponse, error) {
	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("marshal: %w", err)
	}
	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, c.BackendURL+"/agents/complete", bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := c.HTTP.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("backend unreachable: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		raw, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("backend %d: %s", resp.StatusCode, string(raw))
	}

	// FastAPI returns {data, error, meta}; unwrap `data`.
	var envelope struct {
		Data  *CompleteResponse `json:"data"`
		Error *string           `json:"error"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&envelope); err != nil {
		return nil, fmt.Errorf("decode: %w", err)
	}
	if envelope.Error != nil && *envelope.Error != "" {
		return nil, fmt.Errorf("backend error: %s", *envelope.Error)
	}
	if envelope.Data == nil {
		return nil, fmt.Errorf("backend returned no data")
	}
	return envelope.Data, nil
}

func (c *Client) completeDirectGroq(ctx context.Context, req CompleteRequest) (*CompleteResponse, error) {
	if c.GroqKey == "" {
		return nil, fmt.Errorf("LLM_DIRECT mode requires GROQ_API_KEY")
	}

	payload := map[string]any{
		"model":    "llama-3.3-70b-versatile",
		"messages": req.Messages,
	}
	body, _ := json.Marshal(payload)

	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, "https://api.groq.com/openai/v1/chat/completions", bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	httpReq.Header.Set("Authorization", "Bearer "+c.GroqKey)
	httpReq.Header.Set("Content-Type", "application/json")

	start := time.Now()
	resp, err := c.HTTP.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("groq unreachable: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		raw, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("groq %d: %s", resp.StatusCode, string(raw))
	}

	var groqResp struct {
		Choices []struct {
			Message Message `json:"message"`
		} `json:"choices"`
		Model string `json:"model"`
		Usage map[string]any `json:"usage"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&groqResp); err != nil {
		return nil, fmt.Errorf("decode: %w", err)
	}
	if len(groqResp.Choices) == 0 {
		return nil, fmt.Errorf("groq returned no choices")
	}
	return &CompleteResponse{
		Content:   groqResp.Choices[0].Message.Content,
		Provider:  "groq",
		Model:     groqResp.Model,
		Usage:     groqResp.Usage,
		LatencyMs: float64(time.Since(start).Milliseconds()),
	}, nil
}

func getenv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
