import "reflect-metadata";

import { NestFactory } from "@nestjs/core";

import { AppModule } from "./app.module.js";

async function bootstrap(): Promise<void> {
  const app = await NestFactory.create(AppModule, { cors: true });
  const port = Number(process.env.PORT ?? 8002);
  await app.listen(port);
  console.log(`AgentOS Nest API listening on :${port}`);
}

bootstrap();
