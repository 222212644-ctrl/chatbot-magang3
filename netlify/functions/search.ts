import type { Handler } from "@netlify/functions";
import type { SearchRequest, SearchResult, SearchResponse } from "../../shared/api";

// Import JSON indeks saat build (pastikan resolveJsonModule true di tsconfig)
import indexJson from "../../public/bps_index.json";

type Record = {
  url: string;
  title: string;
  description: string;
  text: string;
};

const INDEX: Record[] = (indexJson as any).records || [];

function tokenize(s: string): string[] {
  return (s || "")
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s]/gu, " ")
    .split(/\s+/)
    .filter(Boolean);
}

function scoreRecord(qTokens: string[], r: Record): number {
  const title = r.title?.toLowerCase() || "";
  const desc = r.description?.toLowerCase() || "";
  const text = r.text?.toLowerCase() || "";

  let score = 0;
  for (const t of qTokens) {
    // bobot judul > deskripsi > isi
    if (title.includes(t)) score += 5;
    if (desc.includes(t)) score += 3;
    if (text.includes(t)) score += 1;
  }
  // Bonus: kecocokan tahun (angka 4 digit)
  const years = qTokens.filter((t) => /^\d{4}$/.test(t));
  for (const y of years) {
    if (title.includes(y)) score += 2;
    if (desc.includes(y)) score += 1;
    if (text.includes(y)) score += 0.5;
  }
  return score;
}

function makeSnippet(qTokens: string[], text: string, maxLen = 220): string {
  if (!text) return "";
  const lower = text.toLowerCase();
  let pos = 0;
  for (const t of qTokens) {
    const i = lower.indexOf(t);
    if (i >= 0) {
      pos = i;
      break;
    }
  }
  const start = Math.max(0, pos - 80);
  const end = Math.min(text.length, start + maxLen);
  const snippet = text.slice(start, end).trim();
  return (start > 0 ? "…" : "") + snippet + (end < text.length ? "…" : "");
}

export const handler: Handler = async (event) => {
  // CORS untuk dipakai lintas domain bila perlu
  const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
  };
  if (event.httpMethod === "OPTIONS") {
    return { statusCode: 200, headers: corsHeaders, body: "" };
  }

  try {
    let query = "";
    if (event.httpMethod === "GET") {
      const q = event.queryStringParameters?.q || "";
      query = q;
    } else if (event.httpMethod === "POST") {
      const body = JSON.parse(event.body || "{}") as SearchRequest;
      query = body.query || body.message || "";
    }

    query = (query || "").trim();
    if (!query) {
      const resp: SearchResponse = { query, results: [] };
      return { statusCode: 200, headers: corsHeaders, body: JSON.stringify(resp) };
    }

    const qTokens = tokenize(query);
    const scored = INDEX.map((r) => ({
      r,
      s: scoreRecord(qTokens, r),
    }))
      .filter((x) => x.s > 0)
      .sort((a, b) => b.s - a.s)
      .slice(0, 10)
      .map(({ r, s }) => {
        const snippet = makeSnippet(qTokens, r.description || r.text || "");
        const out: SearchResult = {
          url: r.url,
          title: r.title || r.url,
          snippet,
          score: Math.round(s * 100) / 100,
          source: "BPS Kota Medan",
        };
        return out;
      });

    const resp: SearchResponse = {
      query,
      results: scored,
    };
    return { statusCode: 200, headers: corsHeaders, body: JSON.stringify(resp) };
  } catch (e: any) {
    return { statusCode: 500, headers: corsHeaders, body: JSON.stringify({ error: e?.message || "error" }) };
  }
};