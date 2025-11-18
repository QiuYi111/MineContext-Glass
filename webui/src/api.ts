import type { DailyReport, UploadLimits, UploadResponse, UploadStatus } from "./types";

// 从URL参数获取后端端口，用于Electron环境
function getBackendBase(): string {
  if (typeof window !== "undefined") {
    const urlParams = new URLSearchParams(window.location.search);
    const backendPort = urlParams.get("backend_port");
    if (backendPort) {
      // Electron环境：直接使用后端端口，绕过Vite代理
      console.log(`Electron环境检测到，使用后端端口: ${backendPort}`);
      return `http://127.0.0.1:${backendPort}`;
    }
  }
  // 开发环境：使用Vite代理
  return "";
}

// 检测是否在Electron环境中
function isElectronEnvironment(): boolean {
  if (typeof window === "undefined") return false;
  return window.location.search.includes("backend_port");
}

function buildUrl(path: string): string {
  if (isElectronEnvironment()) {
    // Electron环境：直接请求后端
    const backendBase = getBackendBase();
    return `${backendBase}${path}`;
  } else {
    // 开发环境：通过Vite代理
    return path;
  }
}

const jsonHeaders = {
  Accept: "application/json",
};

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

export interface TimelineEntry {
  timeline_id: string;
  filename: string;
  status: string;
  started_at: number;
  has_report?: boolean;
  context_type?: string;
}

export async function fetchTimelines(): Promise<TimelineEntry[]> {
  const response = await fetch(buildUrl("/glass/timelines"), {
    headers: jsonHeaders,
    credentials: "include",
  });
  const payload = await parseJson<{ data: TimelineEntry[] }>(response);
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

export interface ChromaDBStatus {
  model_name: string;
  model_dir: string;
  downloaded: boolean;
  preloading: boolean;
  model_size_mb: number;
  status: "ready" | "downloading" | "not_started";
}

export interface FFmpegStatus {
  available: boolean;
  version: string | null;
  codecs: string[];
  error: string | null;
  status: "ready" | "not_installed";
  install_guide?: string;
}

export interface SystemStatus {
  chromadb: ChromaDBStatus;
  ffmpeg: FFmpegStatus;
}

export async function fetchChromaDBStatus(): Promise<ChromaDBStatus> {
  const response = await fetch(buildUrl("/api/monitoring/chromadb-status"), {
    headers: jsonHeaders,
    credentials: "include",
  });
  const payload = await parseJson<{ data: ChromaDBStatus }>(response);
  return payload.data;
}

export async function fetchFFmpegStatus(): Promise<FFmpegStatus> {
  const response = await fetch(buildUrl("/api/monitoring/ffmpeg-status"), {
    headers: jsonHeaders,
    credentials: "include",
  });
  const payload = await parseJson<{ data: FFmpegStatus }>(response);
  return payload.data;
}

export async function fetchSystemStatus(): Promise<SystemStatus> {
  const [chromadb, ffmpeg] = await Promise.all([
    fetchChromaDBStatus(),
    fetchFFmpegStatus(),
  ]);
  return { chromadb, ffmpeg };
}
