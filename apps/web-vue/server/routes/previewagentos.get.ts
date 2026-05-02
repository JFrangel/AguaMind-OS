// Legacy alias. The canonical URL is now /preview. Issue a permanent
// redirect so search engines and clients update their bookmarks.
export default defineEventHandler((event) => {
  return sendRedirect(event, "/preview", 301);
});
