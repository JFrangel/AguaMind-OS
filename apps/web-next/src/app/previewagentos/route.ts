export const runtime = "nodejs";

// Legacy alias. The canonical URL is now /preview. Issue a permanent
// redirect so search engines and clients update their bookmarks. Use a
// relative Location header so the redirect respects whichever host the
// app is served from (vercel preview, prod, localhost).
export function GET() {
  return new Response(null, {
    status: 301,
    headers: { Location: "/preview" },
  });
}
