import { memo } from "react";
import { AnimatePresence, motion } from "framer-motion";
import type { TimelineHighlight } from "../types";

import "../styles/highlight-carousel.css";

export interface HighlightCarouselProps {
  highlights: TimelineHighlight[];
  onInsert: (highlight: TimelineHighlight) => void;
}

const HighlightCarousel = memo(({ highlights, onInsert }: HighlightCarouselProps) => (
  <section className="highlight-carousel">
    <header>
      <h3>Highlights</h3>
      <span>{highlights.length}</span>
    </header>
    <div className="highlight-carousel__track">
      <AnimatePresence initial={false}>
        {highlights.length === 0 ? (
          <motion.div
            className="highlight-carousel__empty"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
          >
            暂无高光片段，可等待处理完成或手动添加。
          </motion.div>
        ) : (
          highlights.map((highlight) => (
            <motion.article
              key={highlight.context_id ?? highlight.title}
              className="highlight-card"
              initial={{ opacity: 0, y: 22 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -18 }}
              transition={{ duration: 0.4 }}
            >
              <div className="highlight-card__header">
                <span className="highlight-card__modality">{highlight.modality.toUpperCase()}</span>
                <span className="highlight-card__timestamp">
                  {formatTimestamp(highlight.timestamp ?? highlight.segment_start)}
                </span>
              </div>
              <h4>{highlight.title}</h4>
              {highlight.summary ? <p>{highlight.summary}</p> : null}
              <button type="button" onClick={() => onInsert(highlight)}>
                插入日报
              </button>
            </motion.article>
          ))
        )}
      </AnimatePresence>
    </div>
  </section>
));

HighlightCarousel.displayName = "HighlightCarousel";

export default HighlightCarousel;

function formatTimestamp(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) {
    return "--:--";
  }
  const minutes = Math.floor(value / 60);
  const seconds = value % 60;
  return `${String(minutes).padStart(2, "0")}:${seconds.toFixed(1).padStart(4, "0")}`;
}
