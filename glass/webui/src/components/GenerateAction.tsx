import { memo, useMemo } from "react";
import { motion } from "framer-motion";

import type { UploadStatus } from "../types";
import "../styles/generate-action.css";

export interface GenerateActionProps {
  timelineName?: string | null;
  status?: UploadStatus | null;
  disabled?: boolean;
  generating?: boolean;
  onGenerate: () => void;
}

const STATUS_HINT: Record<UploadStatus, string> = {
  pending: "等待上传完成后才能生成日报。",
  uploading: "上传尚未完成，请继续等待。",
  processing: "当前任务已在处理队列中，请稍候。",
  completed: "重新生成将覆盖自动摘要并刷新高光内容。",
  failed: "上次处理失败，可以尝试重新生成。",
};

const GenerateAction = ({
  timelineName,
  status = null,
  disabled = false,
  generating = false,
  onGenerate,
}: GenerateActionProps): JSX.Element => {
  const statusMessage = useMemo(() => {
    if (!timelineName) {
      return "选择一条时间线后即可手动触发生成流程。";
    }
    if (!status) {
      return "准备就绪，可尝试生成日报。";
    }
    return STATUS_HINT[status];
  }, [status, timelineName]);

  const title = timelineName ? `为 ${timelineName} 生成日报` : "手动生成日报";

  return (
    <motion.section
      className="generate-action"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.05, duration: 0.4 }}
    >
      <div className="generate-action__copy">
        <h2>{title}</h2>
        <p>{statusMessage}</p>
      </div>
      <button
        type="button"
        className="generate-action__button"
        disabled={disabled || generating}
        onClick={onGenerate}
      >
        <span>{generating ? "生成中…" : "生成日报"}</span>
      </button>
    </motion.section>
  );
};

export default memo(GenerateAction);
