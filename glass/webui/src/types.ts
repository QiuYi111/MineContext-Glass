export type UploadStatus = "pending" | "uploading" | "processing" | "completed" | "failed";

export interface UploadLimits {
  max_size_mb: number;
  allowed_types: string[];
  max_concurrent: number;
}

export interface UploadResponse {
  timeline_id: string;
  status: UploadStatus;
}

export interface TimelineHighlight {
  title: string;
  summary?: string | null;
  modality: string;
  timestamp?: number | null;
  segment_start?: number | null;
  segment_end?: number | null;
  context_id?: string | null;
}

export interface VisualCard {
  image_url: string;
  caption?: string | null;
  segment_start?: number | null;
  segment_end?: number | null;
}

export interface DailyReport {
  timeline_id: string;
  source?: string | null;
  auto_markdown?: string | null;
  manual_markdown?: string | null;
  rendered_html?: string | null;
  highlights: TimelineHighlight[];
  visual_cards: VisualCard[];
  manual_metadata: Record<string, unknown>;
  updated_at?: string | null;
}
