import cors from "cors";
import express from "express";

import { chatRouter } from "./routes/chat.js";
import { healthRouter } from "./routes/health.js";

const PORT = Number(process.env.PORT ?? 8001);
const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

const app = express();
app.use(cors());
app.use(express.json({ limit: "10mb" }));

app.locals.backendUrl = BACKEND_URL;

app.use("/health", healthRouter);
app.use("/chat", chatRouter);

app.listen(PORT, () => {
  console.log(`AgentOS Express API listening on :${PORT} (proxying to ${BACKEND_URL})`);
});
