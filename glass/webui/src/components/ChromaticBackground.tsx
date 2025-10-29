import { memo } from "react";

import "../styles/background.css";

const ChromaticBackground = memo(() => (
  <div className="chromatic-stage" aria-hidden>
    <div className="chromatic-orb orb-one" />
    <div className="chromatic-orb orb-two" />
    <div className="chromatic-orb orb-three" />
    <div className="chromatic-grid" />
  </div>
));

ChromaticBackground.displayName = "ChromaticBackground";

export default ChromaticBackground;
