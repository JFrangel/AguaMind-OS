import { Controller, Get } from "@nestjs/common";

import { ProxyService } from "./proxy.service.js";

@Controller("health")
export class HealthController {
  constructor(private readonly proxy: ProxyService) {}

  @Get()
  async health(): Promise<unknown> {
    const data = await this.proxy.fetchJson("/health");
    return data ?? { status: "down", providers: {}, timestamp: Date.now() };
  }
}
