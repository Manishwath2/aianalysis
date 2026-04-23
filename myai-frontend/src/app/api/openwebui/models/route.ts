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

export async function GET() {
  const config = getOpenWebUIConfig();
  if (!config.ok) {
    return NextResponse.json(
      { error: config.error },
      {
        status: 501,
      }
    );
  }

  const url = new URL("/api/models", config.baseUrl);

  const upstream = await fetch(url, {
    method: "GET",
    headers: {
      ...(config.apiKey ? { Authorization: `Bearer ${config.apiKey}` } : {}),
    },
    cache: "no-store",
  });

  const contentType = upstream.headers.get("content-type") ?? "application/json";
  const text = await upstream.text();

  return new Response(text, {
    status: upstream.status,
    headers: {
      "content-type": contentType,
      "cache-control": "no-store",
    },
  });
}
