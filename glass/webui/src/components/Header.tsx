import { motion } from "framer-motion";

import "../styles/header.css";

const Header = (): JSX.Element => (
  <header className="glass-header">
    <motion.div
      className="glass-header__badge"
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
    >
      GLASS · Immersive Context
    </motion.div>
    <motion.h1
      className="glass-header__title"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.35, duration: 0.6 }}
    >
      Build spectacular daily reports from first-person video.
    </motion.h1>
    <motion.p
      className="glass-header__subtitle"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5, duration: 0.6 }}
    >
      Drop in a timeline, watch the multimodal pipeline align transcripts, frames, and highlights, then sculpt your
      narrative with live Markdown editing.
    </motion.p>
  </header>
);

export default Header;
