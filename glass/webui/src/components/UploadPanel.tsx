import { useCallback, useMemo, useState } from "react";
import { motion } from "framer-motion";
import type { UploadLimits } from "../types";

import "../styles/upload-panel.css";

export interface UploadPanelProps {
  limits: UploadLimits | null;
  disabled?: boolean;
  onFilesPicked: (files: FileList | File[]) => Promise<void>;
}

const UploadPanel = ({ limits, disabled, onFilesPicked }: UploadPanelProps): JSX.Element => {
  const [isActive, setIsActive] = useState(false);

  const description = useMemo(() => {
    if (!limits) {
      return "读取上传配额中…";
    }
    const size = limits.max_size_mb ? `${limits.max_size_mb}MB` : "无限制";
    return `单文件 ≤ ${size} · 并发 ${limits.max_concurrent} · ${limits.allowed_types.join(", ")}`;
  }, [limits]);

  const handleDrop = useCallback(
    async (event: React.DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      if (disabled) return;
      setIsActive(false);
      if (event.dataTransfer.files?.length) {
        await onFilesPicked(event.dataTransfer.files);
      }
    },
    [disabled, onFilesPicked],
  );

  const handleBrowse = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      if (event.target.files?.length) {
        await onFilesPicked(event.target.files);
        event.target.value = "";
      }
    },
    [onFilesPicked],
  );

  return (
    <motion.section
      className={`upload-panel ${isActive ? "upload-panel--active" : ""}`}
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2, duration: 0.5 }}
      onDragOver={(event) => {
        event.preventDefault();
        if (!disabled) {
          setIsActive(true);
        }
      }}
      onDragLeave={() => setIsActive(false)}
      onDrop={handleDrop}
    >
      <div className="upload-panel__glow" />
      <div className="upload-panel__content">
        <div className="upload-panel__icon" aria-hidden>
          <motion.span
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.25, type: "spring", stiffness: 140, damping: 12 }}
          >
            ⬆
          </motion.span>
        </div>
        <h2>Drop your Glass timeline</h2>
        <p>{description}</p>
        <div className="upload-panel__actions">
          <label className="upload-panel__browse">
            <input type="file" accept="video/*" multiple onChange={handleBrowse} disabled={disabled} />
            选择视频
          </label>
          <span>或将文件拖拽到此处</span>
        </div>
      </div>
    </motion.section>
  );
};

export default UploadPanel;
