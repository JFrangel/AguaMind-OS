import { Injectable } from "@nestjs/common";

@Injectable()
export class ProxyService {
  readonly backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";

  async fetchJson<T = unknown>(path: string): Promise<T | null> {
    try {
      const res = await fetch(`${this.backendUrl}${path}`);
      if (!res.ok) return null;
      return (await res.json()) as T;
    } catch {
      return null;
    }
  }

  async streamPost(path: string, body: unknown): Promise<Response> {
    return fetch(`${this.backendUrl}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  }
}
