import { Plus, Clock, Heart, Settings, Home } from "lucide-react";
import { Button } from "./ui/button";
import { Avatar } from "./ui/avatar";
import { DiaryCard } from "./DiaryCard";
import { ImageWithFallback } from "./figma/ImageWithFallback";

interface DashboardProps {
  onNavigate: (page: string) => void;
  currentPage: string;
}

export function Dashboard({ onNavigate, currentPage }: DashboardProps) {
  const mockDiaries = [
    {
      id: 1,
      title: "夏日午后的回忆",
      preview: "那是一个阳光明媚的下午，微风轻拂过脸颊，带来一丝清凉。我坐在咖啡馆的窗边，看着外面来来往往的行人...",
      date: "2024年11月10日 14:30",
      thumbnail: "https://images.unsplash.com/photo-1518057111178-44a106bad636?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxjb2ZmZWUlMjBtb3JuaW5nfGVufDF8fHx8MTc2MzA3NzE1MHww&ixlib=rb-4.1.0&q=80&w=1080",
      emotions: [
        { label: "平静", color: "#3B82F6" },
        { label: "喜悦", color: "#FACC15" },
      ],
      isFavorite: true,
    },
    {
      id: 2,
      title: "落日余晖下的思考",
      preview: "傍晚时分，我独自走在海边的小路上。远处的天空被染成了橙红色，海浪轻轻拍打着岸边...",
      date: "2024年11月8日 18:45",
      thumbnail: "https://images.unsplash.com/flagged/photo-1556527906-5a697e9bee90?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxzdW5zZXQlMjBwZWFjZWZ1bHxlbnwxfHx8fDE3NjMwODAwMTh8MA&ixlib=rb-4.1.0&q=80&w=1080",
      emotions: [
        { label: "感悟", color: "#A855F7" },
        { label: "宁静", color: "#3B82F6" },
      ],
      isFavorite: false,
    },
    {
      id: 3,
      title: "时光的痕迹",
      preview: "翻开旧相册，看到那些泛黄的照片，记忆如潮水般涌来。每一张照片都承载着一段故事...",
      date: "2024年11月5日 21:20",
      thumbnail: "https://images.unsplash.com/photo-1761973193217-4908920fcad5?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtZW1vcnklMjBub3N0YWxnaWElMjB2aW50YWdlfGVufDF8fHx8MTc2MzE5ODg0OHww&ixlib=rb-4.1.0&q=80&w=1080",
      emotions: [
        { label: "怀念", color: "#E94E77" },
      ],
      isFavorite: true,
    },
  ];

  const menuItems = [
    { icon: Home, label: "首页", page: "dashboard" },
    { icon: Clock, label: "历史记录", page: "history" },
    { icon: Heart, label: "收藏日记", page: "favorites" },
    { icon: Settings, label: "设置", page: "settings" },
  ];

  return (
    <div className="flex h-screen bg-[#F1F5F9]">
      {/* 左侧功能区 */}
      <aside className="w-60 bg-white border-r border-[#F1F5F9] flex flex-col p-4 gap-6">
        <div className="flex items-center gap-3 px-2">
          <div className="w-10 h-10 rounded-lg gradient-primary flex items-center justify-center">
            <span className="text-white">📔</span>
          </div>
          <span className="text-gradient-primary" style={{ fontSize: '18px', fontWeight: 600 }}>
            AI日记本
          </span>
        </div>

        <Button
          className="w-full h-12 rounded-3xl gradient-primary text-white shadow-lg hover:shadow-xl transition-all"
          onClick={() => onNavigate("upload")}
        >
          <Plus className="w-5 h-5 mr-2" />
          新建日记
        </Button>

        <nav className="flex flex-col gap-1">
          {menuItems.map((item) => (
            <button
              key={item.page}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all relative ${
                currentPage === item.page
                  ? "bg-[#F1F5F9] text-[#E94E77]"
                  : "text-[#64748B] hover:bg-[#F1F5F9]/50"
              }`}
              onClick={() => onNavigate(item.page)}
            >
              {currentPage === item.page && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 gradient-primary rounded-r" />
              )}
              <item.icon className="w-5 h-5" />
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
      </aside>

      {/* 主内容区 */}
      <main className="flex-1 overflow-auto">
        <div className="max-w-6xl mx-auto p-8">
          {/* 欢迎卡片 */}
          <div className="bg-white rounded-2xl p-6 mb-8 shadow-sm">
            <div className="flex items-center gap-4">
              <Avatar className="w-16 h-16">
                <div className="w-full h-full gradient-primary flex items-center justify-center text-white text-xl">
                  用
                </div>
              </Avatar>
              <div>
                <h2 className="mb-1">下午好，欢迎回来！👋</h2>
                <p className="caption">今天想记录些什么呢？</p>
              </div>
            </div>
          </div>

          {/* 最近日记 */}
          <div className="mb-6">
            <h2 className="mb-4">最近的日记</h2>
          </div>

          <div className="grid gap-4">
            {mockDiaries.map((diary) => (
              <DiaryCard
                key={diary.id}
                title={diary.title}
                preview={diary.preview}
                date={diary.date}
                thumbnail={diary.thumbnail}
                emotions={diary.emotions}
                isFavorite={diary.isFavorite}
                onClick={() => onNavigate("result")}
              />
            ))}
          </div>

          {/* 空状态 */}
          {mockDiaries.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <div className="w-32 h-32 mb-6 opacity-20">
                <ImageWithFallback
                  src="https://images.unsplash.com/photo-1571916234808-adf437ac1644?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxkaWFyeSUyMGpvdXJuYWwlMjB3cml0aW5nfGVufDF8fHx8MTc2MzEwOTI3M3ww&ixlib=rb-4.1.0&q=80&w=1080"
                  alt="Empty state"
                  className="w-full h-full object-cover rounded-2xl"
                />
              </div>
              <h3 className="mb-2">还没有日记</h3>
              <p className="caption mb-6">点击"新建日记"按钮开始记录你的生活吧</p>
              <Button
                className="gradient-primary text-white"
                onClick={() => onNavigate("upload")}
              >
                <Plus className="w-5 h-5 mr-2" />
                创建第一篇日记
              </Button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
