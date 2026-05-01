export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig();
  const body = await readRawBody(event);

  const upstream = await fetch(`${config.backendUrl}/reports/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ?? "{}",
  });
  if (!upstream.ok || !upstream.body) {
    throw createError({
      statusCode: upstream.status || 502,
      statusMessage: `Backend error: ${upstream.status}`,
    });
  }
  setResponseHeaders(event, {
    "Content-Type": upstream.headers.get("Content-Type") ?? "application/pdf",
    "Content-Disposition": "attachment; filename=agentos-response.pdf",
  });
  return sendStream(event, upstream.body);
});
