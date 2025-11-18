import { useState, useEffect } from "react";
import { Button } from "./ui/button";
import { CircularProgress } from "./CircularProgress";
import { motion } from "motion/react";

interface ProcessingPageProps {
  fileName: string;
  onComplete: () => void;
  onCancel: () => void;
}

export function ProcessingPage({ fileName, onComplete, onCancel }: ProcessingPageProps) {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("正在分析画面情感线索");

  const statusMessages = [
    "正在分析画面情感线索",
    "正在提取关键时刻",
    "正在理解场景氛围",
    "正在编织文字故事",
    "正在润色日记内容",
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setTimeout(onComplete, 500);
          return 100;
        }
        return prev + 2;
      });
    }, 100);

    return () => clearInterval(interval);
  }, [onComplete]);

  useEffect(() => {
    const statusIndex = Math.floor((progress / 100) * statusMessages.length);
    if (statusIndex < statusMessages.length) {
      setStatus(statusMessages[statusIndex]);
    }
  }, [progress]);

  // 模拟记忆碎片
  const memoryFragments = [
    { id: 1, delay: 0, x: -20, y: -30 },
    { id: 2, delay: 0.5, x: 20, y: -10 },
    { id: 3, delay: 1, x: -30, y: 20 },
    { id: 4, delay: 1.5, x: 30, y: 10 },
    { id: 5, delay: 2, x: 0, y: -20 },
  ];

  return (
    <div className="min-h-screen bg-[#F1F5F9] flex items-center justify-center p-8 relative overflow-hidden">
      {/* 背景记忆碎片动画 */}
      <div className="absolute inset-0 pointer-events-none">
        {memoryFragments.map((fragment) => (
          <motion.div
            key={fragment.id}
            className="absolute w-32 h-32 rounded-lg opacity-10 gradient-primary"
            style={{
              left: `${20 + fragment.x}%`,
              top: `${20 + fragment.y}%`,
            }}
            animate={{
              y: [0, -20, 0],
              x: [0, fragment.x > 0 ? 10 : -10, 0],
              rotate: [0, 5, -5, 0],
            }}
            transition={{
              duration: 4,
              delay: fragment.delay,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />
        ))}
      </div>

      {/* 主内容 */}
      <div className="bg-white rounded-3xl p-12 shadow-xl max-w-md w-full relative z-10">
        <div className="flex flex-col items-center text-center">
          {/* 环形进度指示器 */}
          <div className="mb-8">
            <CircularProgress progress={progress} size={120} strokeWidth={8} />
          </div>

          {/* 状态文本 */}
          <div className="space-y-2 mb-8">
            <h2 className="text-gradient-primary">AI正在编织你的故事</h2>
            <p className="text-[#64748B]">{status}</p>
            <p className="caption">{Math.round(progress)}%</p>
          </div>

          {/* 文件信息 */}
          <div className="w-full bg-[#F1F5F9] rounded-lg p-4 mb-6">
            <p className="caption text-left">正在处理: {fileName}</p>
          </div>

          {/* 提示信息 */}
          <p className="caption mb-6">
            处理时间取决于素材长度，通常需要30秒-2分钟
          </p>

          {/* 取消按钮 */}
          <Button variant="ghost" onClick={onCancel} className="text-[#64748B]">
            取消处理
          </Button>
        </div>
      </div>
    </div>
  );
}
