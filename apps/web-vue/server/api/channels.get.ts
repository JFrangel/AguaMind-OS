export default defineEventHandler(async () => {
  const config = useRuntimeConfig();
  try {
    const res = await fetch(`${config.backendUrl}/notify/channels`);
    if (!res.ok) {
      return { data: { configured: [], all: [] }, error: null };
    }
    return await res.json();
  } catch {
    return { data: { configured: [], all: [] }, error: null };
  }
});
