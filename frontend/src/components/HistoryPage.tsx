import { ArrowLeft, Search, Calendar, Filter } from "lucide-react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { DiaryCard } from "./DiaryCard";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";

interface HistoryPageProps {
  onNavigate: (page: string) => void;
}

export function HistoryPage({ onNavigate }: HistoryPageProps) {
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
    {
      id: 4,
      title: "城市的夜晚",
      preview: "华灯初上，城市开始展现出它另一面的魅力。霓虹灯闪烁，街道上的人群熙熙攘攘...",
      date: "2024年11月3日 22:15",
      emotions: [
        { label: "兴奋", color: "#FACC15" },
        { label: "活力", color: "#E94E77" },
      ],
      isFavorite: false,
    },
  ];

  return (
    <div className="min-h-screen bg-[#F1F5F9]">
      {/* 顶部导航 */}
      <header className="bg-white border-b border-[#F1F5F9] h-16 flex items-center px-8 sticky top-0 z-10">
        <Button
          variant="ghost"
          onClick={() => onNavigate("dashboard")}
          className="mr-4"
        >
          <ArrowLeft className="w-5 h-5 mr-2" />
          返回
        </Button>
        <h2>历史记录</h2>
      </header>

      {/* 主内容区 */}
      <main className="max-w-6xl mx-auto p-8">
        {/* 搜索和筛选栏 */}
        <div className="bg-white rounded-2xl p-6 mb-6 shadow-sm">
          <div className="flex gap-4 flex-wrap">
            <div className="flex-1 min-w-[300px] relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#94A3B8]" />
              <Input
                placeholder="搜索日记标题、内容..."
                className="pl-10 bg-[#F1F5F9] border-none"
              />
            </div>
            
            <Select defaultValue="all">
              <SelectTrigger className="w-[160px] bg-[#F1F5F9] border-none">
                <Calendar className="w-4 h-4 mr-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部时间</SelectItem>
                <SelectItem value="today">今天</SelectItem>
                <SelectItem value="week">本周</SelectItem>
                <SelectItem value="month">本月</SelectItem>
                <SelectItem value="year">今年</SelectItem>
              </SelectContent>
            </Select>

            <Select defaultValue="all">
              <SelectTrigger className="w-[160px] bg-[#F1F5F9] border-none">
                <Filter className="w-4 h-4 mr-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部情感</SelectItem>
                <SelectItem value="joy">喜悦</SelectItem>
                <SelectItem value="calm">平静</SelectItem>
                <SelectItem value="nostalgia">怀念</SelectItem>
                <SelectItem value="excitement">兴奋</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* 统计信息 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <p className="caption mb-2">总日记数</p>
            <p className="text-gradient-primary" style={{ fontSize: '32px', fontWeight: 600 }}>
              {mockDiaries.length}
            </p>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <p className="caption mb-2">本周新增</p>
            <p className="text-gradient-primary" style={{ fontSize: '32px', fontWeight: 600 }}>
              3
            </p>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-sm">
            <p className="caption mb-2">收藏数量</p>
            <p className="text-gradient-primary" style={{ fontSize: '32px', fontWeight: 600 }}>
              {mockDiaries.filter(d => d.isFavorite).length}
            </p>
          </div>
        </div>

        {/* 日记列表 */}
        <div className="mb-4">
          <h3 className="mb-4">所有日记 ({mockDiaries.length})</h3>
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
      </main>
    </div>
  );
}
