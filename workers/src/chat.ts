import { checkCrisis, crisisResponse } from "./safety";
import { composeReply } from "./prompt";
import { routeMessage } from "./tagger";

type Lang = "zh-Hant" | "zh-Hans" | "en";

type CorpusChunk = {
  id: string;
  title: string;
  source: "wiki" | "notes" | string;
  slug?: string;
  text: string;
};

function normalizeLang(raw: unknown): Lang {
  if (raw === "zh-Hans" || raw === "en") return raw;
  return "zh-Hant";
}

function sseEvent(event: string, data: unknown): string {
  return `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
}

function queryTerms(message: string): string[] {
  return message
    .toLowerCase()
    .split(/[^\p{L}\p{N}]+/u)
    .filter((t) => t.length > 1);
}

function scoreChunk(chunk: CorpusChunk, terms: string[]): number {
  const hay = `${chunk.title} ${chunk.text}`.toLowerCase();
  let s = 0;
  for (const t of terms) {
    if (hay.includes(t)) s += Math.min(t.length, 10);
  }
  if (chunk.source === "wiki") s *= 1.1;
  return s;
}

function excerpt(text: string, max = 420): string {
  const t = text.replace(/\s+/g, " ").trim();
  if (t.length <= max) return t;
  return `${t.slice(0, max).trim()}…`;
}

function composeFromHits(hits: CorpusChunk[], lang: Lang): string {
  const blocks = hits.map((h) => {
    const kind = h.source === "notes" ? "notes" : "wiki";
    return `### ${h.title} (${kind})\n${excerpt(h.text)}`;
  });
  if (lang === "en") {
    return `What wiki/ and notes/ (raw) say:\n\n${blocks.join("\n\n")}`;
  }
  if (lang === "zh-Hans") {
    return `wiki/ 与 notes/（raw）里的原文：\n\n${blocks.join("\n\n")}`;
  }
  return `wiki/ 與 notes/（raw）裡的原文：\n\n${blocks.join("\n\n")}`;
}

function noneFound(lang: Lang): string {
  if (lang === "en") return "No matching passage in wiki/ or notes/. Try a theme name from the index.";
  if (lang === "zh-Hans") return "wiki/ 与 notes/ 里没有对上的段落。试试 Index 上的主题名。";
  return "wiki/ 與 notes/ 裡沒有對上的段落。試試 Index 上的主題名。";
}

async function loadCorpus(request: Request): Promise<CorpusChunk[]> {
  const url = new URL("/corpus.json", request.url);
  const res = await fetch(url);
  if (!res.ok) return [];
  return (await res.json()) as CorpusChunk[];
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

  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      const searching =
        lang === "en"
          ? "Checking wiki and notes…"
          : lang === "zh-Hans"
            ? "正在对照 wiki 与 notes…"
            : "正在對照 wiki 與 notes…";
      controller.enqueue(encoder.encode(sseEvent("status", { message: searching })));

      const corpus = await loadCorpus(request);
      const terms = queryTerms(message);
      const ranked = corpus
        .map((c) => ({ c, s: terms.length ? scoreChunk(c, terms) : 0 }))
        .filter((x) => x.s > 0)
        .sort((a, b) => b.s - a.s)
        .slice(0, 5)
        .map((x) => x.c);

      for (const c of ranked) {
        controller.enqueue(
          encoder.encode(
            sseEvent("citation", {
              id: c.id,
              title: c.slug ?? c.title,
              source: c.source,
              score: 1,
            }),
          ),
        );
      }

      let reply: string;
      if (ranked.length) {
        reply = composeFromHits(ranked, lang);
      } else {
        const [emotion, mode] = routeMessage(message);
        reply = `${noneFound(lang)}\n\n${composeReply(message, { lang, mode, emotion, weakContext: true })}`;
      }

      for (let i = 0; i < reply.length; i += 12) {
        controller.enqueue(encoder.encode(sseEvent("token", { text: reply.slice(i, i + 12) })));
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
    mode: "wiki-notes",
    chunk_count: 0,
    llm_provider: "corpus",
  });
}
