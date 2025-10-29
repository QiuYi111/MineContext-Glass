import { memo } from "react";
import { motion } from "framer-motion";
import type { VisualCard } from "../types";

import "../styles/visual-mosaic.css";

export interface VisualMosaicProps {
  cards: VisualCard[];
}

const VisualMosaic = memo(({ cards }: VisualMosaicProps) => (
  <section className="visual-mosaic">
    <header>
      <h3>Visual Storyboard</h3>
      <span>{cards.length}</span>
    </header>
    <div className="visual-mosaic__grid">
      {cards.length === 0 ? (
        <div className="visual-mosaic__empty">等待视觉摘要生成，可稍后刷新。</div>
      ) : (
        cards.map((card, index) => (
          <motion.figure
            key={`${card.image_url}-${index}`}
            className="visual-mosaic__frame"
            initial={{ opacity: 0, scale: 0.92 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.08, type: "spring", stiffness: 120, damping: 18 }}
          >
            <img src={card.image_url} alt={card.caption ?? "Captured frame"} loading="lazy" />
            <motion.figcaption initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: index * 0.1 + 0.2 }}>
              <span>{card.caption ?? "Captured frame"}</span>
              <small>{renderSegment(card.segment_start, card.segment_end)}</small>
            </motion.figcaption>
          </motion.figure>
        ))
      )}
    </div>
  </section>
));

VisualMosaic.displayName = "VisualMosaic";

export default VisualMosaic;

function renderSegment(start?: number | null, end?: number | null): string {
  if (start == null && end == null) {
    return "--:--";
  }
  const s = start ?? 0;
  const e = end ?? s;
  return `${formatTime(s)} → ${formatTime(e)}`;
}

function formatTime(value: number): string {
  const minutes = Math.floor(value / 60);
  const seconds = Math.floor(value % 60);
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}
