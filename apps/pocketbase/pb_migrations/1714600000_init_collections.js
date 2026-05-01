/// <reference path="../pb_data/types.d.ts" />

migrate(
  (app) => {
    const sessions = new Collection({
      type: "base",
      name: "chat_sessions",
      fields: [
        { name: "title", type: "text", required: false },
        { name: "user", type: "relation", required: false, options: { collectionId: "_pb_users_auth_" } },
        { name: "created", type: "autodate", onCreate: true },
        { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
      ],
      listRule: "@request.auth.id != ''",
      viewRule: "@request.auth.id != ''",
      createRule: "@request.auth.id != ''",
      updateRule: "@request.auth.id = user.id",
      deleteRule: "@request.auth.id = user.id",
    });
    app.save(sessions);

    const messages = new Collection({
      type: "base",
      name: "chat_messages",
      fields: [
        { name: "session", type: "relation", required: true, options: { collectionId: sessions.id, cascadeDelete: true } },
        { name: "role", type: "select", required: true, options: { values: ["user", "assistant", "system"] } },
        { name: "content", type: "text", required: true },
        { name: "metadata", type: "json" },
        { name: "created", type: "autodate", onCreate: true },
      ],
      indexes: ["CREATE INDEX idx_session_created ON chat_messages (session, created)"],
      listRule: "@request.auth.id != ''",
      viewRule: "@request.auth.id != ''",
      createRule: "@request.auth.id != ''",
      updateRule: null,
      deleteRule: "@request.auth.id != '' && session.user = @request.auth.id",
    });
    app.save(messages);

    const documents = new Collection({
      type: "base",
      name: "rag_documents",
      fields: [
        { name: "title", type: "text", required: true },
        { name: "source", type: "text", required: false },
        { name: "owner", type: "relation", required: false, options: { collectionId: "_pb_users_auth_" } },
        { name: "created", type: "autodate", onCreate: true },
      ],
      listRule: "@request.auth.id != ''",
      viewRule: "@request.auth.id != ''",
      createRule: "@request.auth.id != ''",
      updateRule: "@request.auth.id = owner.id",
      deleteRule: "@request.auth.id = owner.id",
    });
    app.save(documents);
  },
  (app) => {
    for (const name of ["chat_messages", "chat_sessions", "rag_documents"]) {
      const c = app.findCollectionByNameOrId(name);
      if (c) app.delete(c);
    }
  },
);
