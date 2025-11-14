import type { DailyReport, UploadLimits, UploadResponse, UploadStatus } from "./types";

const API_BASE = (import.meta.env.VITE_GLASS_API_BASE as string | undefined)?.replace(/\/$/, "") ?? "";

const jsonHeaders = {
  Accept: "application/json",
};

function buildUrl(path: string): string {
  return `${API_BASE}${path}`;
}

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = response.statusText;
    try {
      const payload = await response.json();
      if (payload?.message) {
        message = payload.message;
      }
    } catch {
      // ignore
    }
    throw new Error(message || "请求失败");
  }
  return response.json() as Promise<T>;
}

export async function fetchUploadLimits(): Promise<UploadLimits> {
  const response = await fetch(buildUrl("/glass/uploads/limits"), {
    headers: jsonHeaders,
    credentials: "include",
  });
  const payload = await parseJson<{ data: UploadLimits }>(response);
  return payload.data;
}

export async function uploadVideo(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(buildUrl("/glass/upload"), {
    method: "POST",
    body: formData,
    credentials: "include",
  });

  const payload = await parseJson<{ data: UploadResponse }>(response);
  return payload.data;
}

export async function fetchStatus(timelineId: string): Promise<UploadStatus> {
  const response = await fetch(buildUrl(`/glass/status/${timelineId}`), {
    headers: jsonHeaders,
    credentials: "include",
  });
  const payload = await parseJson<{ data: { status: UploadStatus } }>(response);
  return payload.data.status;
}

export async function fetchDailyReport(timelineId: string): Promise<DailyReport> {
  const response = await fetch(buildUrl(`/glass/report/${timelineId}`), {
    headers: jsonHeaders,
    credentials: "include",
  });
  const payload = await parseJson<{ data: DailyReport }>(response);
  return payload.data;
}

export async function saveDailyReport(
  timelineId: string,
  manualMarkdown: string,
  manualMetadata: Record<string, unknown>,
): Promise<DailyReport> {
  const response = await fetch(buildUrl(`/glass/report/${timelineId}`), {
    method: "PUT",
    headers: {
      ...jsonHeaders,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      manual_markdown: manualMarkdown,
      manual_metadata: manualMetadata,
    }),
    credentials: "include",
  });
  const payload = await parseJson<{ data: DailyReport }>(response);
  return payload.data;
}

export interface GenerateReportResponse {
  timeline_id: string;
  status: string;
}

export async function generateDailyReport(timelineId: string): Promise<GenerateReportResponse> {
  const response = await fetch(buildUrl(`/glass/report/${timelineId}/generate`), {
    method: "POST",
    headers: jsonHeaders,
    credentials: "include",
  });
  const payload = await parseJson<{ data: GenerateReportResponse }>(response);
  return payload.data;
}
