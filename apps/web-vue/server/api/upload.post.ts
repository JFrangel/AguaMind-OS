export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig();
  const form = await readMultipartFormData(event);
  if (!form?.length) {
    throw createError({ statusCode: 400, statusMessage: "Missing file" });
  }

  const upstream = new FormData();
  for (const part of form) {
    if (part.name === "file") {
      const blob = new Blob([part.data], { type: part.type ?? "application/octet-stream" });
      upstream.append("file", blob, part.filename ?? "upload");
    }
  }

  const res = await fetch(`${config.backendUrl}/rag/ingest`, {
    method: "POST",
    body: upstream,
  });
  if (!res.ok) {
    throw createError({ statusCode: res.status, statusMessage: `Backend error: ${res.status}` });
  }
  return res.json();
});
