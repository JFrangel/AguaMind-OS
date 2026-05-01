/// <reference path="../pb_data/types.d.ts" />

// Bumps the parent chat_sessions.updated whenever a chat_messages row is created.
// Keeps the sidebar's "recent sessions" list in correct order without an extra query.
onRecordCreate((e) => {
  if (e.record.collection().name !== "chat_messages") return e.next();

  const sessionId = e.record.get("session");
  if (!sessionId) return e.next();

  try {
    const session = $app.findRecordById("chat_sessions", sessionId);
    session.set("updated", new Date().toISOString());
    $app.save(session);
  } catch (err) {
    $app.logger().warn("touch_session: " + err);
  }

  return e.next();
});
