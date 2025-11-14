import { useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";

import "../styles/status-toast.css";

export interface StatusToastProps {
  message: string;
  tone: "muted" | "info" | "success" | "warning" | "error";
  onClose: () => void;
  duration?: number;
}

const StatusToast = ({ message, tone, onClose, duration = 3600 }: StatusToastProps): JSX.Element => {
  useEffect(() => {
    const timer = setTimeout(onClose, duration);
    return () => clearTimeout(timer);
  }, [duration, onClose]);

  return (
    <AnimatePresence>
      {message ? (
        <motion.div
          className={`status-toast status-toast--${tone}`}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 20 }}
        >
          {message}
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
};

export default StatusToast;
