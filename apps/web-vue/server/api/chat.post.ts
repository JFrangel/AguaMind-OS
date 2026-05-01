export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig();
  const body = await readBody<Record<string, unknown>>(event);

  const upstreamPayload = {
    message: body?.message,
    context_type: body?.context_type ?? "chat",
    language: body?.language ?? "es",
    use_rag: Boolean(body?.use_rag),
    use_web: Boolean(body?.use_web),
  };

  const upstream = await fetch(`${config.backendUrl}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(upstreamPayload),
  });

  if (!upstream.ok || !upstream.body) {
    throw createError({
      statusCode: upstream.status || 502,
      statusMessage: `Backend error: ${upstream.status}`,
    });
  }

  setResponseHeaders(event, {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    Connection: "keep-alive",
    "X-Accel-Buffering": "no",
  });

  return sendStream(event, upstream.body);
});
