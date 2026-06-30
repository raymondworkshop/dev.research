import { handleChat, healthResponse } from "./chat";

export interface Env {
  ASSETS: Fetcher;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === "/api/health" && request.method === "GET") {
      return healthResponse();
    }

    if (url.pathname === "/api/chat" && request.method === "POST") {
      return handleChat(request);
    }

    return env.ASSETS.fetch(request);
  },
};
