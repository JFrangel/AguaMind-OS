import { Router } from "express";

export const healthRouter = Router();

healthRouter.get("/", async (req, res) => {
  const backend = req.app.locals.backendUrl as string;
  try {
    const upstream = await fetch(`${backend}/health`);
    if (!upstream.ok) {
      res.status(200).json({ status: "down", providers: {}, timestamp: Date.now() });
      return;
    }
    res.status(200).json(await upstream.json());
  } catch {
    res.status(200).json({ status: "down", providers: {}, timestamp: Date.now() });
  }
});
