import { NextResponse } from "next/server";

const LOOPBACK_HOSTNAMES = new Set(["localhost", "127.0.0.1", "0.0.0.0", "::1"]);

function getBackendBaseUrl() {
  const fallbackBaseUrl =
    process.env.NODE_ENV === "production" ? "http://backend:8000" : "http://127.0.0.1:8000";
  const rawBaseUrl = process.env.BACKEND_BASE_URL?.trim() || fallbackBaseUrl;

  let parsedBaseUrl: URL;
  try {
    parsedBaseUrl = new URL(rawBaseUrl);
  } catch {
    parsedBaseUrl = new URL(fallbackBaseUrl);
  }

  const baseUrl =
    process.env.NODE_ENV === "production" && LOOPBACK_HOSTNAMES.has(parsedBaseUrl.hostname)
      ? fallbackBaseUrl
      : parsedBaseUrl.toString();

  return {
    ok: true as const,
    baseUrl: baseUrl.replace(/\/+$/, ""),
  };
}

async function proxyRequest(request: Request, path: string[]) {
  const config = getBackendBaseUrl();
  const incomingUrl = new URL(request.url);
  const targetUrl = new URL(`${config.baseUrl}/${path.join("/")}${incomingUrl.search}`);

  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  if (contentType) {
    headers.set("content-type", contentType);
  }

  const init: RequestInit = {
    method: request.method,
    headers,
    cache: "no-store",
  };

  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = await request.text();
  }

  let upstream: Response;
  try {
    upstream = await fetch(targetUrl, init);
  } catch (error) {
    console.error("Backend proxy request failed", {
      targetUrl: targetUrl.toString(),
      error,
    });

    return NextResponse.json(
      {
        error: "backend_unavailable",
        detail: "Backend service is unavailable",
      },
      { status: 503 },
    );
  }
  const responseHeaders = new Headers(upstream.headers);
  responseHeaders.set("cache-control", "no-store");
  responseHeaders.delete("content-length");
  responseHeaders.delete("content-encoding");

  return new Response(upstream.body, {
    status: upstream.status,
    headers: responseHeaders,
  });
}

export async function GET(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return proxyRequest(request, path);
}

export async function POST(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return proxyRequest(request, path);
}

export async function PUT(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return proxyRequest(request, path);
}

export async function PATCH(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return proxyRequest(request, path);
}

export async function DELETE(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return proxyRequest(request, path);
}
