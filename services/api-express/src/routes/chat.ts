import { Router } from "express";

export const chatRouter = Router();

chatRouter.post("/stream", async (req, res) => {
  const backend = req.app.locals.backendUrl as string;

  let upstream: Response;
  try {
    upstream = await fetch(`${backend}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req.body),
    });
  } catch (err) {
    res.status(502).json({ error: `Backend unreachable: ${(err as Error).message}` });
    return;
  }

  if (!upstream.ok || !upstream.body) {
    res.status(upstream.status).send(`Backend error: ${upstream.status}`);
    return;
  }

  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.setHeader("X-Accel-Buffering", "no");
  res.flushHeaders?.();

  const reader = upstream.body.getReader();
  const closed = new Promise<void>((resolve) => req.on("close", resolve));

  try {
    while (true) {
      const { done, value } = await Promise.race([
        reader.read(),
        closed.then(() => ({ done: true, value: undefined })),
      ]);
      if (done) break;
      if (value) res.write(Buffer.from(value));
    }
  } finally {
    res.end();
  }
});
