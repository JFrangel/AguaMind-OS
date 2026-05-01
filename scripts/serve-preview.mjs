#!/usr/bin/env node
// Lightweight static server for scripts/preview.html. Used by the IDE
// "Launch preview" panel so the user lands on a chooser page rather than
// having to remember which port runs each frontend.

import { readFile } from "node:fs/promises";
import { createServer } from "node:http";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const HTML_PATH = join(here, "preview.html");
const PORT = Number(process.env.PORT ?? 4173);

const server = createServer(async (req, res) => {
  try {
    const html = await readFile(HTML_PATH, "utf8");
    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    res.end(html);
  } catch (err) {
    res.writeHead(500, { "Content-Type": "text/plain" });
    res.end(`preview server error: ${err}`);
  }
});

server.listen(PORT, () => {
  process.stdout.write(`AgentOS preview chooser → http://localhost:${PORT}\n`);
});
