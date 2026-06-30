import { checkCrisis, crisisResponse } from "./safety";
import { routeMessage } from "./tagger";
import { composeReply } from "./prompt";

type Lang = "zh-Hant" | "zh-Hans" | "en";

function normalizeLang(raw: unknown): Lang {
  if (raw === "zh-Hans" || raw === "en") return raw;
  return "zh-Hant";
}

function statusMessage(lang: Lang): string {
  if (lang === "en") return "Composing your reply…";
  if (lang === "zh-Hans") return "稳心整理回复中…";
  return "穩心整理回覆中…";
}

function sseEvent(event: string, data: unknown): string {
  return `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
}

export async function handleChat(request: Request): Promise<Response> {
  let body: { session_id?: string; message?: string; lang?: string };
  try {
    body = (await request.json()) as typeof body;
  } catch {
    return new Response(JSON.stringify({ error: "invalid json" }), { status: 400 });
  }

  const message = (body.message ?? "").trim();
  const lang = normalizeLang(body.lang);

  if (!message) {
    return new Response(JSON.stringify({ error: "message required" }), { status: 400 });
  }

  if (checkCrisis(message)) {
    const text = crisisResponse(lang);
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode(sseEvent("crisis", { message: text })));
        controller.enqueue(encoder.encode(sseEvent("done", {})));
        controller.close();
      },
    });
    return new Response(stream, {
      headers: { "Content-Type": "text/event-stream; charset=utf-8" },
    });
  }

  const [emotion, mode] = routeMessage(message);
  const reply = composeReply(message, { lang, mode, emotion });
  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      controller.enqueue(encoder.encode(sseEvent("status", { message: statusMessage(lang) })));
      for (let i = 0; i < reply.length; i += 8) {
        controller.enqueue(encoder.encode(sseEvent("token", { text: reply.slice(i, i + 8) })));
      }
      controller.enqueue(encoder.encode(sseEvent("done", {})));
      controller.close();
    },
  });

  return new Response(stream, {
    headers: { "Content-Type": "text/event-stream; charset=utf-8" },
  });
}

export function healthResponse(): Response {
  return Response.json({
    status: "ok",
    mode: "demo",
    chunk_count: 0,
    llm_provider: "template",
  });
}
