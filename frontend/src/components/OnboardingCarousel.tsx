import { useState } from "react";
import { Button } from "./ui/button";
import { Upload, Sparkles, BookOpen } from "lucide-react";

interface OnboardingCarouselProps {
  onComplete: () => void;
  onSkip: () => void;
}

export function OnboardingCarousel({ onComplete, onSkip }: OnboardingCarouselProps) {
  const [currentPage, setCurrentPage] = useState(0);

  const pages = [
    {
      icon: Upload,
      title: "上传你的素材",
      description: "支持多张照片或一段视频\n让AI读懂你的每个瞬间",
      color: "#FFA726",
    },
    {
      icon: Sparkles,
      title: "AI 智能分析",
      description: "自动识别场景、人物和情感\n为你生成专属的故事叙事",
      color: "#64B5F6",
    },
    {
      icon: BookOpen,
      title: "生成精美日记",
      description: "情感丰富的叙事内容\n随时回顾你的珍贵记忆",
      color: "#81C784",
    },
  ];

  const handleNext = () => {
    if (currentPage < pages.length - 1) {
      setCurrentPage(currentPage + 1);
    } else {
      onComplete();
    }
  };

  const CurrentIcon = pages[currentPage].icon;

  return (
    <div className="min-h-screen bg-[#FAF3E0] flex flex-col">
      {/* Header */}
      <div className="flex justify-end p-4">
        <Button
          variant="ghost"
          onClick={onSkip}
          className="text-[#9E9E9E]"
        >
          跳过
        </Button>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col items-center justify-center px-8">
        {/* Illustration */}
        <div className="w-[280px] h-[200px] mb-8 flex items-center justify-center">
          <div className="relative">
            <div
              className="absolute inset-0 rounded-full blur-3xl opacity-20"
              style={{ background: pages[currentPage].color }}
            />
            <CurrentIcon
              className="w-32 h-32 relative z-10"
              style={{ color: pages[currentPage].color }}
              strokeWidth={1.5}
            />
          </div>
        </div>

        {/* Headline */}
        <h2 className="text-[24px] font-bold mb-3 text-center" style={{ fontFamily: 'var(--font-heading)' }}>
          {pages[currentPage].title}
        </h2>

        {/* Description */}
        <p className="text-[16px] text-[#757575] text-center max-w-[280px] leading-relaxed whitespace-pre-line">
          {pages[currentPage].description}
        </p>
      </div>

      {/* Footer */}
      <div className="flex flex-col items-center pb-12 px-8">
        {/* Page Indicator */}
        <div className="flex gap-2 mb-6">
          {pages.map((_, index) => (
            <div
              key={index}
              className={`w-2 h-2 rounded-full transition-all ${
                index === currentPage
                  ? "bg-[#FFA726] w-6"
                  : "bg-[#E0E0E0]"
              }`}
            />
          ))}
        </div>

        {/* Next Button */}
        <Button
          onClick={handleNext}
          className="w-[200px] h-12 bg-[#FFA726] hover:bg-[#FF9800] text-white rounded-[24px]"
        >
          {currentPage === pages.length - 1 ? "开始使用" : "下一步"}
        </Button>
      </div>
    </div>
  );
}
