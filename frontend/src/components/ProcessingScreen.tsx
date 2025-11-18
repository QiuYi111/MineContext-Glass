import { useState, useEffect } from "react";
import { Button } from "./ui/button";
import { ArrowLeft, Sparkles } from "lucide-react";
import { motion } from "motion/react";
import { glassApi, ProcessingStatus } from "../services/glassApi";
import { toast } from "sonner";

interface ProcessingScreenProps {
  fileName: string;
  fileCount: number;
  taskId?: string | null;
  onComplete: () => void;
  onCancel: () => void;
  onBackgroundProcess?: (taskId: string) => void;
}

export function ProcessingScreen({
  fileName,
  fileCount,
  taskId,
  onComplete,
  onCancel,
  onBackgroundProcess,
}: ProcessingScreenProps) {
  const [progress, setProgress] = useState(0);
  const [currentTip, setCurrentTip] = useState(0);
  const [processingStatus, setProcessingStatus] = useState<ProcessingStatus | null>(null);
  const [isRealProcessing, setIsRealProcessing] = useState(!!taskId);

  const tips = [
    "AI正在回忆你的美好瞬间...",
    "正在为你的故事添加情感色彩...",
    "马上就好，好的内容值得等待...",
    "正在分析场景和情感细节...",
    "提取视频关键帧...",
    "转录语音内容...",
    "生成时间线上下文...",
    "分析情感和场景...",
  ];

  // Real backend processing with polling
  useEffect(() => {
    if (!taskId || !isRealProcessing) {
      // Fallback to demo mode if no taskId
      const interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 100) {
            clearInterval(interval);
            setTimeout(onComplete, 500);
            return 100;
          }
          return prev + 1.5;
        });
      }, 100);
      return () => clearInterval(interval);
    }

    // Real processing with backend polling
    const pollStatus = async () => {
      try {
        const status = await glassApi.getProcessingStatus(taskId);
        setProcessingStatus(status);
        setProgress(status.progress);

        // Update status text based on current step
        if (status.current_step) {
          console.log(`Processing: ${status.current_step} (${status.progress}%)`);
        }

        // Check if processing is complete and data is ready
        if (status.status === 'completed') {
          toast.success("视频处理完成！正在生成日记...");
          setTimeout(onComplete, 1000);
          return;
        }

        // Check if processing failed
        if (status.status === 'failed') {
          toast.error(`处理失败: ${status.message}`);
          onCancel(); // Go back to home on failure
          return;
        }

        // Handle finalizing stage - this is normal processing, not failure
        if (status.status === 'finalizing') {
          console.log(`Finalizing: ${status.current_step} (${status.progress}%)`);
          return; // Continue polling, don't treat as error
        }

      } catch (error) {
        console.error('Status polling failed:', error);
        // Continue with demo mode on error
        setIsRealProcessing(false);
      }
    };

    // Initial status check
    pollStatus();

    // Poll every 3 seconds (reduce frequency to avoid overwhelming backend)
    const pollingInterval = setInterval(pollStatus, 3000);

    return () => clearInterval(pollingInterval);
  }, [taskId, isRealProcessing, onComplete, onCancel]);

  useEffect(() => {
    const tipInterval = setInterval(() => {
      setCurrentTip((prev) => (prev + 1) % tips.length);
    }, 3000);

    return () => clearInterval(tipInterval);
  }, []);

  // Handle background processing
  const handleBackgroundProcess = () => {
    if (taskId && onBackgroundProcess) {
      // Start background processing
      onBackgroundProcess(taskId);
      toast.success("已转为后台处理，完成后将通知您");
    } else {
      // If no background processing callback, just cancel
      onCancel();
    }
  };

  const radius = 92;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (progress / 100) * circumference;

  return (
    <div className="min-h-screen bg-[#FAF3E0] flex flex-col">
      {/* Header */}
      <div className="flex items-center p-4 border-b border-[#E0E0E0]">
        <Button
          variant="ghost"
          size="icon"
          onClick={onCancel}
          className="text-[#424242]"
        >
          <ArrowLeft className="w-6 h-6" />
        </Button>
        <h2 className="flex-1 text-center text-[20px] font-semibold">
          正在生成日记
        </h2>
        <div className="w-10" />
      </div>

      {/* Media Preview */}
      <div className="px-6 pt-6">
        <div className="flex gap-2 overflow-x-auto pb-2">
          {Array.from({ length: fileCount }).map((_, i) => (
            <div
              key={i}
              className="w-20 h-20 rounded-lg bg-gradient-to-br from-[#FFA726]/20 to-[#FFB74D]/20 flex-shrink-0 flex items-center justify-center"
            >
              <span className="text-2xl">📷</span>
            </div>
          ))}
        </div>
        <p className="text-sm text-[#757575] text-center mt-3">
          正在处理 {fileName} {isRealProcessing ? "(实时进度)" : "(演示模式)"}
        </p>
      </div>

      {/* Progress Indicator */}
      <div className="flex-1 flex flex-col items-center justify-center px-6">
        {/* Circular Progress */}
        <div className="relative mb-6">
          <svg width="200" height="200" className="transform -rotate-90">
            <circle
              cx="100"
              cy="100"
              r={radius}
              stroke="#E0E0E0"
              strokeWidth="8"
              fill="none"
            />
            <circle
              cx="100"
              cy="100"
              r={radius}
              stroke="url(#gradient)"
              strokeWidth="8"
              fill="none"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              strokeLinecap="round"
              className="transition-all duration-300"
            />
            <defs>
              <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#FFA726" />
                <stop offset="100%" stopColor="#FFB74D" />
              </linearGradient>
            </defs>
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-5xl font-bold text-[#FFA726]">
              {Math.round(progress)}%
            </span>
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            >
              <Sparkles className="w-6 h-6 text-[#FFA726] mt-2" />
            </motion.div>
          </div>
        </div>

        {/* Status Text */}
        <h3 className="text-[20px] font-semibold mb-2 text-center">
          {processingStatus?.current_step || "AI正在分析场景和情感..."}
        </h3>
        <p className="text-sm text-[#9E9E9E] mb-6">
          {isRealProcessing && processingStatus ?
            `步骤 ${processingStatus.total_steps > 0 ? Math.floor((progress / 100) * processingStatus.total_steps) : 1} / ${processingStatus.total_steps || 'N/A'}` :
            `预计还需 ${Math.round((100 - progress) * 0.6)} 秒`
          }
        </p>

        {/* Dynamic Tips */}
        <motion.div
          key={currentTip}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          className="bg-white rounded-xl p-4 max-w-sm"
        >
          <p className="text-sm italic text-[#757575] text-center">
            {tips[currentTip]}
          </p>
        </motion.div>
      </div>

      {/* Footer */}
      <div className="p-6 space-y-3">
        <Button
          variant="ghost"
          onClick={onCancel}
          className="w-full text-[#9E9E9E]"
        >
          取消生成
        </Button>
        <Button
          variant="outline"
          onClick={handleBackgroundProcess}
          className="w-full border-[#FFA726] text-[#FFA726] hover:bg-[#FFA726] hover:text-white"
        >
          后台处理
        </Button>
      </div>
    </div>
  );
}
