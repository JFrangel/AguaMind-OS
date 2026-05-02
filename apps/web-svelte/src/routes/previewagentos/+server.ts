import type { RequestHandler } from "./$types";

// Legacy alias kept for backwards compatibility with old bookmarks. The
// canonical URL is now /preview. We 301 so search engines and clients
// update their references.
export const GET: RequestHandler = async () => {
  return new Response(null, {
    status: 301,
    headers: { Location: "/preview" },
  });
};
