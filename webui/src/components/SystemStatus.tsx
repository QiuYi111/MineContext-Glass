import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { fetchSystemStatus, SystemStatus } from "../api";

import "./SystemStatus.css";

const SystemStatus = (): JSX.Element => {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadStatus = async () => {
      try {
        setLoading(true);
        const systemStatus = await fetchSystemStatus();
        setStatus(systemStatus);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "获取系统状态失败");
      } finally {
        setLoading(false);
      }
    };

    // 立即加载一次
    loadStatus();

    // 每30秒刷新一次
    const interval = setInterval(loadStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (componentStatus: string) => {
    switch (componentStatus) {
      case "ready":
        return "✅";
      case "downloading":
        return "⏳";
      case "not_started":
        return "⏸️";
      case "not_installed":
        return "❌";
      default:
        return "❓";
    }
  };

  const getStatusText = (component: string, componentStatus: any) => {
    if (component === "chromadb") {
      switch (componentStatus.status) {
        case "ready":
          return `ChromaDB就绪 (模型大小: ${componentStatus.model_size_mb}MB)`;
        case "downloading":
          return "ChromaDB模型下载中...";
        case "not_started":
          return "ChromaDB未开始下载";
        default:
          return "ChromaDB状态未知";
      }
    } else if (component === "ffmpeg") {
      if (componentStatus.available) {
        return `FFmpeg就绪 (支持编解码器: ${componentStatus.codecs.join(", ")})`;
      } else {
        return "FFmpeg未安装";
      }
    }
    return "状态未知";
  };

  if (loading) {
    return (
      <motion.div
        className="system-status system-status--loading"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="system-status__loader"></div>
        <span>检查系统状态中...</span>
      </motion.div>
    );
  }

  if (error) {
    return (
      <motion.div
        className="system-status system-status--error"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <span className="system-status__icon">❌</span>
        <span className="system-status__text">{error}</span>
      </motion.div>
    );
  }

  if (!status) {
    return null;
  }

  const allReady = status.chromadb.status === "ready" && status.ffmpeg.status === "ready";

  return (
    <motion.div
      className={`system-status ${allReady ? "system-status--ready" : "system-status--warning"}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="system-status__header">
        <span className="system-status__title">
          {allReady ? "🟢 系统就绪" : "🟡 系统未完全就绪"}
        </span>
      </div>

      <div className="system-status__components">
        <div className="system-status__component">
          <span className="system-status__icon">
            {getStatusIcon(status.chromadb.status)}
          </span>
          <div className="system-status__details">
            <div className="system-status__name">ChromaDB</div>
            <div className="system-status__text">
              {getStatusText("chromadb", status.chromadb)}
            </div>
            {status.chromadb.status === "ready" && (
              <div className="system-status__subtext">
                模型: {status.chromadb.model_name}
              </div>
            )}
          </div>
        </div>

        <div className="system-status__component">
          <span className="system-status__icon">
            {getStatusIcon(status.ffmpeg.status)}
          </span>
          <div className="system-status__details">
            <div className="system-status__name">FFmpeg</div>
            <div className="system-status__text">
              {getStatusText("ffmpeg", status.ffmpeg)}
            </div>
            {status.ffmpeg.version && (
              <div className="system-status__subtext">
                版本: {status.ffmpeg.version.split(" ")[2]}
              </div>
            )}
            {!status.ffmpeg.available && status.ffmpeg.install_guide && (
              <div className="system-status__install-guide">
                <details>
                  <summary>安装指导</summary>
                  <pre>{status.ffmpeg.install_guide}</pre>
                </details>
              </div>
            )}
          </div>
        </div>
      </div>

      {!allReady && (
        <div className="system-status__actions">
          <button
            className="system-status__refresh-btn"
            onClick={() => window.location.reload()}
          >
            刷新状态
          </button>
        </div>
      )}
    </motion.div>
  );
};

export default SystemStatus;