import { ApiResponse } from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const DEFAULT_TIMEOUT_MS = 10000; // 10s timeout for resilient slow-network handling

export class ApiError extends Error {
  code: number;
  data: any;

  constructor(message: string, code: number = 500, data: any = null) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.data = data;
  }
}

export interface RequestOptions extends RequestInit {
  timeoutMs?: number;
  userId?: string; // Seeded user switcher header
}

/**
 * Standardized Fetch Client handling { code, message, data } envelopes,
 * timeout abortions, slow network handling, and HTTP error normalization.
 */
export async function apiRequest<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<ApiResponse<T>> {
  const { timeoutMs = DEFAULT_TIMEOUT_MS, userId, headers, ...customConfig } = options;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const url = endpoint.startsWith("http") ? endpoint : `${BASE_URL}${endpoint}`;

  const defaultHeaders: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (userId) {
    defaultHeaders["X-User-Id"] = userId;
  }

  try {
    const response = await fetch(url, {
      ...customConfig,
      headers: {
        ...defaultHeaders,
        ...headers,
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    const json: ApiResponse<T> = await response.json();

    if (!response.ok || json.code >= 400) {
      throw new ApiError(
        json.message || `Request failed with status ${response.status}`,
        json.code || response.status,
        json.data
      );
    }

    return json;
  } catch (error: any) {
    clearTimeout(timeoutId);

    if (error.name === "AbortError") {
      throw new ApiError("Network request timed out. Please check your connection.", 408);
    }

    if (error instanceof ApiError) {
      throw error;
    }

    throw new ApiError(
      error.message || "An unexpected network error occurred.",
      500
    );
  }
}
