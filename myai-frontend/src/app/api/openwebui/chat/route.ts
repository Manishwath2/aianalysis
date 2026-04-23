import { NextResponse } from "next/server";

function getOpenWebUIConfig() {
  const baseUrl = process.env.OPENWEBUI_BASE_URL;
  const apiKey = process.env.OPENWEBUI_API_KEY;

  if (!baseUrl) {
    return {
      ok: false as const,
      error: "OPENWEBUI_BASE_URL is not set",
    };
  }

  return {
    ok: true as const,
    baseUrl,
    apiKey,
  };
}

export async function POST(req: Request) {
  const config = getOpenWebUIConfig();
  if (!config.ok) {
    return NextResponse.json(
      { error: config.error },
      {
        status: 501,
      }
    );
  }

  const url = new URL("/api/chat/completions", config.baseUrl);
  const body = await req.text();

  const upstream = await fetch(url, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      ...(config.apiKey ? { Authorization: `Bearer ${config.apiKey}` } : {}),
    },
    body,
  });

  const headers = new Headers(upstream.headers);
  headers.set("cache-control", "no-cache, no-store, must-revalidate");
  headers.set("pragma", "no-cache");
  headers.set("expires", "0");

  // Some upstream headers can conflict when we proxy a streamed response.
  headers.delete("content-length");
  headers.delete("content-encoding");

  return new Response(upstream.body, {
    status: upstream.status,
    headers,
  });
}
