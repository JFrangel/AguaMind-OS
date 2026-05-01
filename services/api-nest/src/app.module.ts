import { Module } from "@nestjs/common";

import { ChatController } from "./chat.controller.js";
import { HealthController } from "./health.controller.js";
import { ProxyService } from "./proxy.service.js";

@Module({
  controllers: [HealthController, ChatController],
  providers: [ProxyService],
})
export class AppModule {}
