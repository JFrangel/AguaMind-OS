# PocketBase — AgentOS lightweight backend

Lightweight backend for sessions, messages, and ephemeral RAG document metadata. Schema lives in `pb_migrations/` and one JS hook in `pb_hooks/`.

## Local

```bash
docker build -t agentos-pocketbase .
docker run -p 8090:8090 -v pb_data:/pb/pb_data agentos-pocketbase
```

Open `http://localhost:8090/_/` for the admin UI. First boot prompts to create an admin.

## Deploy to PocketHost (free)

1. Sign up at <https://pockethost.io/> (free, no credit card)
2. Create a new instance — it gives you `<name>.pockethost.io`
3. From the dashboard, open the file manager and upload:
   - `pb_migrations/1714600000_init_collections.js`
   - `pb_hooks/touch_session.pb.js`
4. Restart the instance — migrations apply on next boot
5. Set the frontend env var:
   ```env
   PUBLIC_POCKETBASE_URL=https://<name>.pockethost.io
   ```

## Schema

| Collection | Purpose |
|-----------|---------|
| `chat_sessions` | One row per conversation. `user_id` (auth) + `title` + timestamps |
| `chat_messages` | Append-only log linked to a session. Has `role`, `content`, `metadata` |
| `rag_documents` | RAG document metadata (the actual chunks live in pgvector/FAISS) |

## Hooks

- `touch_session.pb.js` — bumps `chat_sessions.updated_at` on every message insert so the sidebar sort order stays correct without an extra query.

## Auth flow

Frontend → PocketBase auth → JWT → forwarded to FastAPI (`Authorization: Bearer ...`) → FastAPI's `auth_dependency` validates with the same Supabase JWT secret OR a separate `POCKETBASE_JWT_SECRET` if you keep them isolated.

For hackathon-speed: leave `AUTH_REQUIRED=false` on FastAPI and treat PocketBase as the source of truth for session ownership. Tighten before shipping to real users.
