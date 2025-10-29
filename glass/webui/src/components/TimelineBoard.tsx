import { memo } from "react";
import { motion } from "framer-motion";
import type { UploadStatus } from "../types";

import "../styles/timeline-board.css";

export interface TimelineEntry {
  timelineId: string;
  filename: string;
  status: UploadStatus;
  startedAt: number;
}

export interface TimelineBoardProps {
  entries: TimelineEntry[];
  selectedTimeline: string | null;
  onSelect: (timelineId: string) => void;
}

const statusAccent: Record<UploadStatus, string> = {
  pending: "var(--accent-pending)",
  uploading: "var(--accent-uploading)",
  processing: "var(--accent-processing)",
  completed: "var(--accent-completed)",
  failed: "var(--accent-failed)",
};

const TimelineBoard = memo(({ entries, selectedTimeline, onSelect }: TimelineBoardProps) => (
  <section className="timeline-board">
    <header className="timeline-board__header">
      <h3>Active timelines</h3>
      <span>{entries.length}</span>
    </header>
    <div className="timeline-board__list">
      {entries.length === 0 ? (
        <div className="timeline-board__empty">还没有上传任务。</div>
      ) : (
        entries.map((entry, index) => (
          <motion.button
            key={entry.timelineId}
            className={`timeline-card ${entry.timelineId === selectedTimeline ? "timeline-card--active" : ""}`}
            style={{
              borderColor: statusAccent[entry.status],
            }}
            onClick={() => onSelect(entry.timelineId)}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.06 }}
          >
            <div className="timeline-card__top">
              <span className="timeline-card__status" data-status={entry.status}>
                {entry.status.toUpperCase()}
              </span>
              <span className="timeline-card__time">{formatRelative(entry.startedAt)}</span>
            </div>
            <div className="timeline-card__middle">{entry.filename}</div>
            <div className="timeline-card__bottom">Timeline · {entry.timelineId}</div>
          </motion.button>
        ))
      )}
    </div>
  </section>
));

TimelineBoard.displayName = "TimelineBoard";

export default TimelineBoard;

function formatRelative(timestamp: number): string {
  const delta = Date.now() - timestamp;
  const minutes = Math.floor(delta / 60000);
  if (minutes <= 0) return "刚刚";
  if (minutes < 60) return `${minutes} 分钟前`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} 小时前`;
  return `${Math.floor(hours / 24)} 天前`;
}
