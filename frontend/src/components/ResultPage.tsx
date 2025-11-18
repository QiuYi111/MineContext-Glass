import { useState } from "react";
import { ArrowLeft, Heart, Share2, Download, Copy, Wand2, Play } from "lucide-react";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { toast } from "sonner@2.0.3";

interface ResultPageProps {
  onNavigate: (page: string) => void;
}

export function ResultPage({ onNavigate }: ResultPageProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [isFavorite, setIsFavorite] = useState(false);
  const [title, setTitle] = useState("夏日午后的回忆");
  const [content, setContent] = useState(
    `那是一个阳光明媚的下午，微风轻拂过脸颊，带来一丝清凉。我坐在咖啡馆的窗边，看着外面来来往往的行人，每个人都有自己的故事。

手中的咖啡还冒着热气，淡淡的香味弥漫在空气中。窗外的阳光透过树叶的缝隙，在地面上投下斑驳的影子，就像时光在这一刻静止了一般。

我拿起相机，记录下这个平凡却美好的瞬间。也许多年以后，当我再次看到这张照片时，会想起今天的心情，想起那份宁静与美好。

生活就是由这样一个个小小的瞬间组成的，它们或许微不足道，但却构成了我们独一无二的人生故事。`
  );

  const emotions = [
    { label: "平静", color: "#3B82F6" },
    { label: "喜悦", color: "#FACC15" },
    { label: "怀念", color: "#E94E77" },
  ];

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    toast.success("已复制到剪贴板");
  };

  const handleSave = () => {
    toast.success("日记已保存");
    setTimeout(() => onNavigate("dashboard"), 1000);
  };

  const handleRegenerate = () => {
    toast.info("正在重新生成日记...");
  };

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
        <h2>日记详情</h2>
        
        <div className="ml-auto flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsFavorite(!isFavorite)}
          >
            <Heart className={`w-5 h-5 ${isFavorite ? "fill-[#E94E77] text-[#E94E77]" : ""}`} />
          </Button>
          
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <Share2 className="w-5 h-5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem>
                <Download className="w-4 h-4 mr-2" />
                导出为PDF
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Share2 className="w-4 h-4 mr-2" />
                分享到社交媒体
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleCopy}>
                <Copy className="w-4 h-4 mr-2" />
                复制文本
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      {/* 主内容区 */}
      <main className="max-w-7xl mx-auto p-8">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
          {/* 左侧素材区 */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-2xl p-6 shadow-sm sticky top-24">
              {/* 素材预览 */}
              <div className="aspect-video bg-gradient-to-br from-[#E94E77]/20 to-[#A855F7]/20 rounded-lg mb-4 relative overflow-hidden group cursor-pointer">
                <img
                  src="https://images.unsplash.com/photo-1518057111178-44a106bad636?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxjb2ZmZWUlMjBtb3JuaW5nfGVufDF8fHx8MTc2MzA3NzE1MHww&ixlib=rb-4.1.0&q=80&w=1080"
                  alt="Diary media"
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <div className="w-16 h-16 rounded-full bg-white/90 flex items-center justify-center">
                    <Play className="w-8 h-8 text-[#E94E77]" />
                  </div>
                </div>
              </div>

              {/* 素材信息 */}
              <div className="space-y-3 mb-4">
                <div className="flex justify-between caption">
                  <span>文件名称</span>
                  <span>summer_coffee.jpg</span>
                </div>
                <div className="flex justify-between caption">
                  <span>文件大小</span>
                  <span>2.4 MB</span>
                </div>
                <div className="flex justify-between caption">
                  <span>分辨率</span>
                  <span>1920 × 1080</span>
                </div>
              </div>

              {/* 情感分析标签 */}
              <div className="border-t border-[#F1F5F9] pt-4">
                <p className="caption mb-3">情感分析</p>
                <div className="flex flex-wrap gap-2">
                  {emotions.map((emotion, index) => (
                    <Badge
                      key={index}
                      className="rounded-full"
                      style={{ backgroundColor: emotion.color, color: "#fff" }}
                    >
                      {emotion.label}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* 右侧文本区 */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-2xl p-8 shadow-sm">
              {/* 日记标题 */}
              <div className="mb-4">
                {isEditing ? (
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className="w-full border-none outline-none bg-transparent"
                    style={{ fontSize: '24px', fontWeight: 600 }}
                  />
                ) : (
                  <h1>{title}</h1>
                )}
              </div>

              {/* 日期时间 */}
              <p className="caption mb-6">2024年11月10日 14:30</p>

              {/* 日记内容 */}
              <div className="bg-white rounded-xl p-6 mb-6 border border-[#F1F5F9] relative group">
                {isEditing ? (
                  <textarea
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    className="w-full min-h-[400px] border-none outline-none resize-none diary-font"
                    style={{ fontSize: '18px', lineHeight: '32px' }}
                  />
                ) : (
                  <div className="diary-font whitespace-pre-line" style={{ fontSize: '18px', lineHeight: '32px' }}>
                    {content}
                  </div>
                )}

                {/* 编辑工具栏 */}
                <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
                  <div className="bg-white rounded-lg shadow-lg border border-[#F1F5F9] p-2 flex gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setIsEditing(!isEditing)}
                    >
                      {isEditing ? "完成" : "编辑"}
                    </Button>
                    <Button variant="ghost" size="sm" onClick={handleCopy}>
                      <Copy className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>

              {/* 情感风格切换 */}
              <div className="mb-6">
                <p className="caption mb-3">情感风格</p>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm">理性</Button>
                  <Button variant="outline" size="sm" className="border-[#E94E77] text-[#E94E77]">感性</Button>
                  <Button variant="outline" size="sm">简洁</Button>
                  <Button variant="outline" size="sm">细腻</Button>
                </div>
              </div>

              {/* 底部操作栏 */}
              <div className="flex gap-4">
                <Button
                  className="flex-1 h-12 gradient-primary text-white shadow-lg hover:shadow-xl transition-all"
                  onClick={handleSave}
                >
                  保存日记
                </Button>
                <Button
                  variant="outline"
                  className="h-12 border-[#94A3B8]"
                  onClick={handleRegenerate}
                >
                  <Wand2 className="w-5 h-5 mr-2" />
                  重新生成
                </Button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
