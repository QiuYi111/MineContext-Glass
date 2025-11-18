import { Button } from "./ui/button";
import { Upload, Camera, ArrowRight, Video, Image } from "lucide-react";
import { TabBar } from "./TabBar";

interface HomeScreenProps {
  onNavigate: (page: string) => void;
  onTabChange: (tab: string) => void;
}

export function HomeScreen({ onNavigate, onTabChange }: HomeScreenProps) {
  const today = new Date();
  const dateString = `${today.getFullYear()}年${today.getMonth() + 1}月${today.getDate()}日`;

  return (
    <div className="min-h-screen bg-[#FAF3E0] pb-24">
      {/* Header */}
      <div className="p-6">
        <p className="text-sm text-[#9E9E9E] mb-2">今天是 {dateString}</p>
        <h2 className="text-[20px] font-semibold">
          Hi 小明, 今天有什么想记录的吗？
        </h2>
      </div>

      {/* Main Content */}
      <div className="px-6">
        {/* Upload Card */}
        <div className="bg-white rounded-[20px] border-2 border-dashed border-[#E0E0E0] p-8 mb-6 shadow-sm">
          <div className="flex flex-col items-center text-center">
            {/* Icon */}
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-[#FFA726] to-[#FFB74D] flex items-center justify-center mb-6">
              <Upload className="w-10 h-10 text-white" strokeWidth={2} />
            </div>

            {/* Title */}
            <h3 className="text-[20px] font-semibold mb-2">上传照片或视频</h3>

            {/* Subtitle */}
            <p className="text-caption text-[#757575] mb-6">
              支持多张照片或一段视频
            </p>

            {/* Buttons */}
            <div className="w-full space-y-3">
              <Button
                onClick={() => onNavigate("file-upload-photo")}
                className="w-full h-12 bg-[#FFA726] hover:bg-[#FF9800] text-white rounded-xl"
              >
                <Image className="w-5 h-5 mr-2" />
                上传照片
              </Button>
              <Button
                onClick={() => onNavigate("file-upload-video")}
                className="w-full h-12 bg-gradient-to-r from-[#64B5F6] to-[#42A5F5] hover:from-[#42A5F5] hover:to-[#1E88E5] text-white rounded-xl"
              >
                <Video className="w-5 h-5 mr-2" />
                上传视频
              </Button>
              <Button
                onClick={() => onNavigate("camera")}
                variant="outline"
                className="w-full h-12 border-[#E0E0E0] text-[#424242] rounded-xl"
              >
                <Camera className="w-5 h-5 mr-2" />
                拍摄新内容
              </Button>
            </div>
          </div>
        </div>

        {/* Recent Diary Quick Access */}
        <button
          onClick={() => onNavigate("diary-detail")}
          className="bg-white rounded-xl p-4 shadow-sm flex items-center gap-4 w-full hover:shadow-md transition-shadow mb-4"
        >
          <div className="w-[60px] h-[60px] rounded-lg bg-gradient-to-br from-[#FFA726]/20 to-[#FFB74D]/20 flex items-center justify-center flex-shrink-0">
            <span className="text-2xl">📖</span>
          </div>
          <div className="flex-1 min-w-0 text-left">
            <p className="text-xs text-[#9E9E9E] mb-1">最近生成</p>
            <p className="text-sm font-semibold text-[#424242] truncate">
              阳光下的周末野餐时光
            </p>
          </div>
          <ArrowRight className="w-5 h-5 text-[#9E9E9E] flex-shrink-0" />
        </button>

        
        {/* Bottom Hint */}
        <div className="mt-8 flex items-center justify-center gap-2">
          <span className="text-2xl">💡</span>
          <p className="text-xs text-[#9E9E9E]">
            小提示: 上传多张照片可以生成更丰富的故事
          </p>
        </div>
      </div>

      {/* Tab Bar */}
      <TabBar activeTab="home" onTabChange={onTabChange} />
    </div>
  );
}
