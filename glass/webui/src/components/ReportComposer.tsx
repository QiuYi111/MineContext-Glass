import { useMemo } from "react";
import { motion } from "framer-motion";
import MarkdownIt from "markdown-it";

import "../styles/report-composer.css";

const mdPreview = new MarkdownIt({ html: false, linkify: true, breaks: true });

export interface ReportComposerProps {
  manualMarkdown: string;
  autoMarkdown: string;
  onChange: (value: string) => void;
  onSave: () => Promise<void>;
  onReset: () => void;
  saving: boolean;
}

const ReportComposer = ({ manualMarkdown, autoMarkdown, onChange, onSave, onReset, saving }: ReportComposerProps) => {
  const rendered = useMemo(() => mdPreview.render(manualMarkdown || ""), [manualMarkdown]);
  const autoRendered = useMemo(() => mdPreview.render(autoMarkdown || ""), [autoMarkdown]);

  return (
    <section className="report-composer">
      <motion.div className="report-composer__pane" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <header>
          <div>
            <h3>手动编辑</h3>
            <p>Markdown 将实时转换为渲染视图。</p>
          </div>
          <div className="report-composer__actions">
            <button type="button" className="button ghost" onClick={onReset}>
              恢复自动摘要
            </button>
            <button type="button" className="button primary" onClick={() => void onSave()} disabled={saving}>
              {saving ? "保存中…" : "保存日报"}
            </button>
          </div>
        </header>
        <textarea
          className="report-composer__editor"
          value={manualMarkdown}
          onChange={(event) => onChange(event.target.value)}
          placeholder="使用 Markdown 描述你的一天…"
        />
      </motion.div>
      <motion.div
        className="report-composer__pane report-composer__pane--preview"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <header>
          <div>
            <h3>预览</h3>
            <p>最终展示效果（自动应用安全过滤）。</p>
          </div>
        </header>
        <article className="report-composer__markdown" dangerouslySetInnerHTML={{ __html: rendered }} />
      </motion.div>
      <motion.div
        className="report-composer__pane report-composer__pane--auto"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
      >
        <header>
          <div>
            <h3>系统自动摘要</h3>
            <p>生成的初稿，可随时复制或作为对比参考。</p>
          </div>
        </header>
        <article className="report-composer__markdown" dangerouslySetInnerHTML={{ __html: autoRendered }} />
      </motion.div>
    </section>
  );
};

export default ReportComposer;
