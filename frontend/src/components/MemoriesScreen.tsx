import { TabBar } from "./TabBar";
import { Badge } from "./ui/badge";

interface MemoriesScreenProps {
  onNavigate: (page: string) => void;
  onTabChange: (tab: string) => void;
}

export function MemoriesScreen({ onNavigate, onTabChange }: MemoriesScreenProps) {
  const timelineEntries = [
    {
      date: "17日 周日",
      title: "阳光下的周末野餐时光",
      thumbnail: "https://images.unsplash.com/photo-1592976370975-dcc9e764374f?w=400",
      hasDiary: true,
    },
    {
      date: "16日 周六",
      title: "",
      thumbnail: "",
      hasDiary: false,
    },
    {
      date: "15日 周五",
      title: "秋日咖啡馆的下午茶",
      thumbnail: "https://images.unsplash.com/photo-1518057111178-44a106bad636?w=400",
      hasDiary: true,
    },
    {
      date: "14日 周四",
      title: "",
      thumbnail: "",
      hasDiary: false,
    },
    {
      date: "12日 周二",
      title: "朋友聚会的欢乐时光",
      thumbnail: "https://images.unsplash.com/photo-1758523981466-f138fe0bad69?w=400",
      hasDiary: true,
    },
  ];

  return (
    <div className="min-h-screen bg-[#FAF3E0] pb-24">
      {/* Header */}
      <div className="p-6 border-b border-[#E0E0E0] bg-white">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-[24px] font-bold" style={{ fontFamily: 'var(--font-heading)' }}>
            时光回顾
          </h1>
          <div className="flex rounded-lg overflow-hidden border border-[#E0E0E0]">
            <button className="px-4 py-1 bg-[#FFA726] text-white text-sm">
              列表
            </button>
            <button className="px-4 py-1 bg-white text-[#757575] text-sm">
              日历
            </button>
          </div>
        </div>
      </div>

      {/* Stats Card */}
      <div className="mx-6 my-6">
        <div className="bg-gradient-to-br from-[#FFA726] to-[#FFB74D] rounded-2xl p-6 text-white">
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold mb-1">12</div>
              <div className="text-sm opacity-90">本月已记录</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold mb-1">45</div>
              <div className="text-sm opacity-90">累计日记</div>
            </div>
            <div className="text-center">
              <div className="text-2xl mb-1">😊</div>
              <div className="text-sm opacity-90">最常情绪</div>
            </div>
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="px-6">
        <div className="bg-white rounded-2xl p-4 mb-4">
          <h2 className="text-[18px] font-bold mb-4">2025年11月</h2>
          <div className="relative">
            {/* Timeline Line */}
            <div className="absolute left-[30px] top-0 bottom-0 w-0.5 bg-[#E0E0E0]" />

            {/* Timeline Entries */}
            <div className="space-y-4">
              {timelineEntries.map((entry, index) => (
                <div key={index} className="relative flex items-center gap-4">
                  {/* Dot */}
                  <div
                    className={`w-3 h-3 rounded-full flex-shrink-0 z-10 ${
                      entry.hasDiary ? "bg-[#FFA726]" : "bg-[#E0E0E0]"
                    }`}
                    style={{ marginLeft: "24px" }}
                  />

                  {/* Date */}
                  <div className="w-[80px] text-sm text-[#757575] flex-shrink-0">
                    {entry.date}
                  </div>

                  {/* Content */}
                  {entry.hasDiary ? (
                    <button
                      onClick={() => onNavigate("diary-detail")}
                      className="flex-1 flex items-center gap-3 bg-[#FAF3E0] rounded-lg p-2 hover:bg-[#F5F5DC] transition-colors"
                    >
                      <div className="w-[60px] h-[60px] rounded-lg overflow-hidden flex-shrink-0">
                        <img
                          src={entry.thumbnail}
                          alt={entry.title}
                          className="w-full h-full object-cover"
                        />
                      </div>
                      <div className="flex-1 min-w-0 text-left">
                        <p className="text-sm font-semibold truncate">
                          {entry.title}
                        </p>
                      </div>
                      <svg
                        className="w-5 h-5 text-[#9E9E9E] flex-shrink-0"
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
                    </button>
                  ) : (
                    <div className="flex-1 text-sm text-[#9E9E9E]">
                      未记录
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Tab Bar */}
      <TabBar activeTab="memories" onTabChange={onTabChange} />
    </div>
  );
}
