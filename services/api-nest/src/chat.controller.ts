import { Body, Controller, HttpException, Post, Res } from "@nestjs/common";
import type { Response } from "express";

import { ProxyService } from "./proxy.service.js";

interface ChatBody {
  message: string;
  context_type?: string;
}

@Controller("chat")
export class ChatController {
  constructor(private readonly proxy: ProxyService) {}

  @Post("stream")
  async stream(@Body() body: ChatBody, @Res() res: Response): Promise<void> {
    const upstream = await this.proxy.streamPost("/chat/stream", body);

    if (!upstream.ok || !upstream.body) {
      throw new HttpException(
        `Backend error: ${upstream.status}`,
        upstream.status || 502,
      );
    }

    res.setHeader("Content-Type", "text/event-stream");
    res.setHeader("Cache-Control", "no-cache");
    res.setHeader("Connection", "keep-alive");
    res.setHeader("X-Accel-Buffering", "no");

    const reader = upstream.body.getReader();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      if (value) res.write(Buffer.from(value));
    }
    res.end();
  }
}
