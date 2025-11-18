import { Search, Filter } from "lucide-react";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { TabBar } from "./TabBar";

interface DiaryListScreenProps {
  onNavigate: (page: string) => void;
  onTabChange: (tab: string) => void;
}

export function DiaryListScreen({ onNavigate, onTabChange }: DiaryListScreenProps) {
  const diaries = [
    {
      id: 1,
      day: "17",
      month: "十一月",
      title: "阳光下的周末野餐时光",
      snippet: "今天的天气格外晴朗，阳光透过树叶洒在草地上...",
      thumbnail: "https://images.unsplash.com/photo-1592976370975-dcc9e764374f?w=400",
      emotions: ["快乐", "温馨"],
    },
    {
      id: 2,
      day: "15",
      month: "十一月",
      title: "秋日咖啡馆的下午茶",
      snippet: "找到了一家很有氛围的咖啡馆，阳光透过玻璃窗...",
      thumbnail: "https://images.unsplash.com/photo-1518057111178-44a106bad636?w=400",
      emotions: ["平静", "惬意"],
    },
    {
      id: 3,
      day: "12",
      month: "十一月",
      title: "朋友聚会的欢乐时光",
      snippet: "好久不见的朋友们终于聚在一起，大家有说有笑...",
      thumbnail: "https://images.unsplash.com/photo-1758523981466-f138fe0bad69?w=400",
      emotions: ["兴奋", "怀念"],
    },
  ];

  return (
    <div className="min-h-screen bg-[#FAF3E0] pb-24">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-[#E0E0E0] bg-white">
        <h1 className="text-[24px] font-bold" style={{ fontFamily: 'var(--font-heading)' }}>
          我的日记
        </h1>
        <div className="flex gap-3">
          <Button variant="ghost" size="icon" className="text-[#424242]">
            <Search className="w-6 h-6" />
          </Button>
          <Button variant="ghost" size="icon" className="text-[#424242]">
            <Filter className="w-6 h-6" />
          </Button>
        </div>
      </div>

      {/* Diary List */}
      <div className="p-6 space-y-4">
        {diaries.map((diary) => (
          <button
            key={diary.id}
            onClick={() => onNavigate("diary-detail")}
            className="w-full bg-white rounded-2xl p-4 shadow-sm hover:shadow-md transition-shadow flex gap-4 text-left"
          >
            {/* Date */}
            <div className="flex flex-col items-center justify-center w-[60px] flex-shrink-0">
              <span className="text-[32px] font-bold text-[#424242]">
                {diary.day}
              </span>
              <span className="text-xs text-[#9E9E9E]">{diary.month}</span>
            </div>

            {/* Thumbnail */}
            <div className="w-20 h-20 rounded-lg overflow-hidden flex-shrink-0">
              <img
                src={diary.thumbnail}
                alt={diary.title}
                className="w-full h-full object-cover"
              />
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0 flex flex-col justify-center">
              <h3 className="text-[16px] font-semibold mb-1 truncate">
                {diary.title}
              </h3>
              <p className="text-sm text-[#757575] line-clamp-2 mb-2">
                {diary.snippet}
              </p>
              <div className="flex gap-2">
                {diary.emotions.map((emotion, index) => (
                  <Badge
                    key={index}
                    className="bg-[#FFA726]/20 text-[#FFA726] text-xs hover:bg-[#FFA726]/30"
                  >
                    {emotion}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Arrow */}
            <div className="flex items-center">
              <svg
                className="w-5 h-5 text-[#9E9E9E]"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </div>
          </button>
        ))}
      </div>

      {/* Tab Bar */}
      <TabBar activeTab="diary" onTabChange={onTabChange} />
    </div>
  );
}
