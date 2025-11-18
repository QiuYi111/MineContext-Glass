import { Button } from "./ui/button";
import { Heart } from "lucide-react";

interface WelcomeScreenProps {
  onStart: () => void;
}

export function WelcomeScreen({ onStart }: WelcomeScreenProps) {
  return (
    <div className="min-h-screen bg-[#FAF3E0] flex flex-col items-center justify-between p-8 pt-32 pb-12">
      {/* Logo */}
      <div className="flex flex-col items-center flex-1 justify-center">
        <div className="w-[120px] h-[120px] mb-4 relative">
          <div className="absolute inset-0 rounded-full bg-gradient-to-br from-[#FFA726] to-[#FFB74D] opacity-20 blur-2xl" />
          <div className="relative w-full h-full flex items-center justify-center">
            <div className="w-24 h-24 rounded-2xl border-4 border-[#FFA726] flex items-center justify-center bg-white/80 backdrop-blur">
              <Heart className="w-12 h-12 text-[#FFA726]" />
            </div>
          </div>
        </div>

        {/* App Name */}
        <h1 className="text-[36px] font-bold mb-3" style={{ fontFamily: 'var(--font-heading)' }}>
          心镜
        </h1>

        {/* Tagline */}
        <p className="text-body-large text-[#757575] mb-2 text-center">
          一键生成我的今日故事
        </p>

        {/* Subtitle */}
        <p className="text-caption text-[#9E9E9E] text-center max-w-[280px] leading-relaxed">
          让AI将你的照片和视频，变成有温度的日记
        </p>
      </div>

      {/* Primary Button */}
      <Button
        onClick={onStart}
        className="w-full max-w-md h-12 bg-[#FFA726] hover:bg-[#FF9800] text-white rounded-[24px] shadow-lg"
      >
        开始体验
      </Button>
    </div>
  );
}
