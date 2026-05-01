export default defineEventHandler(async () => {
  const config = useRuntimeConfig();
  try {
    const res = await fetch(`${config.backendUrl}/health`);
    if (!res.ok) {
      return { status: "down", providers: {}, timestamp: Date.now() };
    }
    return await res.json();
  } catch {
    return { status: "down", providers: {}, timestamp: Date.now() };
  }
});
