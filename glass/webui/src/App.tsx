import { useCallback, useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";

import {
  fetchDailyReport,
  fetchStatus,
  fetchUploadLimits,
  saveDailyReport,
  uploadVideo,
} from "./api";
import type { DailyReport, UploadLimits } from "./types";
import type { TimelineEntry } from "./components/TimelineBoard";
import Header from "./components/Header";
import UploadPanel from "./components/UploadPanel";
import TimelineBoard from "./components/TimelineBoard";
import ReportComposer from "./components/ReportComposer";
import HighlightCarousel from "./components/HighlightCarousel";
import VisualMosaic from "./components/VisualMosaic";
import StatusToast from "./components/StatusToast";

import "./styles/app.css";

const POLL_DELAYS = [3000, 6000, 12000, 24000, 36000];

type ToastTone = "muted" | "info" | "success" | "warning" | "error";

const App = (): JSX.Element => {
  const [limits, setLimits] = useState<UploadLimits | null>(null);
  const [uploads, setUploads] = useState<TimelineEntry[]>([]);
  const [selectedTimeline, setSelectedTimeline] = useState<string | null>(null);
  const [report, setReport] = useState<DailyReport | null>(null);
  const [manualMarkdown, setManualMarkdown] = useState("");
  const [toast, setToast] = useState<{ message: string; tone: ToastTone } | null>(null);
  const [saving, setSaving] = useState(false);

  const pollingHandles = useRef<Map<string, number>>(new Map());

  const showToast = useCallback((message: string, tone: ToastTone = "info") => {
    setToast({ message, tone });
  }, []);

  const clearToast = useCallback(() => setToast(null), []);

  useEffect(() => {
    void (async () => {
      try {
        const data = await fetchUploadLimits();
        setLimits(data);
      } catch (error) {
        console.error(error);
        showToast((error as Error).message ?? "无法获取上传限制", "error");
      }
    })();
    return () => {
      pollingHandles.current.forEach((id) => clearTimeout(id));
      pollingHandles.current.clear();
    };
  }, [showToast]);

  useEffect(() => {
    if (!selectedTimeline && uploads.length > 0) {
      setSelectedTimeline(uploads[0].timelineId);
    }
  }, [uploads, selectedTimeline]);

  useEffect(() => {
    if (!selectedTimeline) {
      setReport(null);
      return;
    }
    const entry = uploads.find((item) => item.timelineId === selectedTimeline);
    if (!entry || entry.status !== "completed") {
      setReport(null);
      return;
    }
    void (async () => {
      try {
        const data = await fetchDailyReport(selectedTimeline);
        setReport(data);
        setManualMarkdown(data.manual_markdown ?? data.auto_markdown ?? "");
      } catch (error) {
        console.error(error);
        showToast((error as Error).message ?? "无法加载日报", "warning");
      }
    })();
  }, [selectedTimeline, uploads, showToast]);

  const updateEntry = useCallback((timelineId: string, patch: Partial<TimelineEntry>) => {
    setUploads((prev) =>
      prev.map((entry) => (entry.timelineId === timelineId ? { ...entry, ...patch } : entry)),
    );
  }, []);

  const schedulePoll = useCallback(
    (timelineId: string, attempt = 0) => {
      const delay = POLL_DELAYS[Math.min(attempt, POLL_DELAYS.length - 1)];
      const handle = window.setTimeout(async () => {
        try {
          const status = await fetchStatus(timelineId);
          updateEntry(timelineId, { status });
          if (status === "completed") {
            pollingHandles.current.delete(timelineId);
            showToast("处理完成，正在加载日报", "success");
            if (timelineId === selectedTimeline) {
              try {
                const data = await fetchDailyReport(timelineId);
                setReport(data);
                setManualMarkdown(data.manual_markdown ?? data.auto_markdown ?? "");
              } catch (error) {
                console.error(error);
                showToast((error as Error).message ?? "无法加载日报", "warning");
              }
            }
          } else if (status === "failed") {
            pollingHandles.current.delete(timelineId);
            showToast("处理失败，请检查服务器日志", "error");
          } else {
            schedulePoll(timelineId, attempt + 1);
          }
        } catch (error) {
          console.error(error);
          pollingHandles.current.delete(timelineId);
          showToast((error as Error).message ?? "查询状态失败", "error");
        }
      }, delay);
      const previous = pollingHandles.current.get(timelineId);
      if (previous) {
        clearTimeout(previous);
      }
      pollingHandles.current.set(timelineId, handle);
    },
    [selectedTimeline, showToast, updateEntry],
  );

  const handleFilesPicked = useCallback(
    async (files: FileList | File[]) => {
      const list = Array.from(files);
      for (const file of list) {
        const placeholderId = `pending-${Date.now()}-${Math.random().toString(16).slice(2, 6)}`;
        setUploads((prev) => [
          {
            timelineId: placeholderId,
            filename: file.name,
            status: "uploading",
            startedAt: Date.now(),
          },
          ...prev,
        ]);
        try {
          const response = await uploadVideo(file);
          setUploads((prev) =>
            prev.map((entry) =>
              entry.timelineId === placeholderId
                ? {
                    timelineId: response.timeline_id,
                    filename: entry.filename,
                    status: response.status,
                    startedAt: entry.startedAt,
                  }
                : entry,
            ),
          );
          if (response.status === "completed") {
            showToast("处理完成，正在加载日报", "success");
            setSelectedTimeline(response.timeline_id);
          } else if (response.status === "failed") {
            showToast("处理失败，请检查日志", "error");
          } else {
            schedulePoll(response.timeline_id);
            showToast("上传成功，进入处理队列", "info");
          }
        } catch (error) {
          console.error(error);
          setUploads((prev) => prev.filter((entry) => entry.timelineId !== placeholderId));
          showToast((error as Error).message ?? "上传失败", "error");
        }
      }
    },
    [schedulePoll, showToast],
  );

  const handleSave = useCallback(async () => {
    if (!selectedTimeline || !report) return;
    setSaving(true);
    try {
      const updated = await saveDailyReport(selectedTimeline, manualMarkdown, report.manual_metadata ?? {});
      setReport(updated);
      setManualMarkdown(updated.manual_markdown ?? updated.auto_markdown ?? "");
      showToast("日报已保存", "success");
    } catch (error) {
      console.error(error);
      showToast((error as Error).message ?? "保存失败", "error");
    } finally {
      setSaving(false);
    }
  }, [manualMarkdown, report, selectedTimeline, showToast]);

  const autoMarkdown = report?.auto_markdown ?? "";

  const highlights = report?.highlights ?? [];
  const visualCards = report?.visual_cards ?? [];

  return (
    <main className="glass-shell">
      <Header />
      <UploadPanel limits={limits} disabled={false} onFilesPicked={handleFilesPicked} />

      <section className="glass-dashboard">
        <motion.div className="glass-dashboard__column" initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }}>
          <TimelineBoard entries={uploads} selectedTimeline={selectedTimeline} onSelect={setSelectedTimeline} />
          <HighlightCarousel
            highlights={highlights}
            onInsert={(item) =>
              setManualMarkdown((prev) => {
                const base = prev.trimEnd();
                const lines = [`- ${item.title}`, item.summary?.trim() ? `  - ${item.summary.trim()}` : null].filter(
                  Boolean,
                );
                return `${base ? `${base}\n\n` : ""}${lines.join("\n")}`;
              })
            }
          />
          <VisualMosaic cards={visualCards} />
        </motion.div>

        <motion.div
          className="glass-dashboard__column glass-dashboard__column--wide"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <ReportComposer
            manualMarkdown={manualMarkdown}
            autoMarkdown={autoMarkdown}
            onChange={setManualMarkdown}
            onSave={handleSave}
            onReset={() => setManualMarkdown(autoMarkdown)}
            saving={saving}
          />
        </motion.div>
      </section>

      {toast ? <StatusToast message={toast.message} tone={toast.tone} onClose={clearToast} /> : null}
    </main>
  );
};

export default App;
