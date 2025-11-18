import { useState } from "react";
import { ArrowLeft, Check, Image as ImageIcon, Smile } from "lucide-react";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";
import { Input } from "./ui/input";
import { Badge } from "./ui/badge";
import { toast } from "sonner@2.0.3";

interface DiaryEditScreenProps {
  onBack: () => void;
  onSave: (data: DiaryData) => void;
  initialData?: DiaryData;
}

export interface DiaryData {
  title: string;
  content: string;
  emotions: string[];
  images?: string[];
}

export function DiaryEditScreen({ onBack, onSave, initialData }: DiaryEditScreenProps) {
  const [title, setTitle] = useState(initialData?.title || "阳光下的周末野餐时光");
  const [content, setContent] = useState(
    initialData?.content ||
      `今天的天气格外晴朗，阳光透过树叶洒在草地上，形成斑驳的光影。我们一家人来到公园，铺开野餐垫，享受这难得的周末时光。

孩子们在草地上欢快地奔跑，笑声在空气中回荡。我准备的三明治和水果都很受欢迎，大家吃得津津有味。微风轻拂，带来一丝清凉，让这个午后显得格外惬意。

看着家人们脸上洋溢的笑容，我深深感受到了生活的美好。这些简单而纯粹的时刻，才是我们最珍贵的财富。希望能永远记住今天的阳光、笑声和温暖。`
  );
  const [selectedEmotions, setSelectedEmotions] = useState<string[]>(
    initialData?.emotions || ["快乐", "温馨", "充实"]
  );

  const emotionOptions = [
    "快乐", "温馨", "充实", "平静", "兴奋",
    "感动", "怀念", "期待", "满足", "放松",
    "惊喜", "感激", "幸福", "自由", "宁静"
  ];

  const handleEmotionToggle = (emotion: string) => {
    if (selectedEmotions.includes(emotion)) {
      setSelectedEmotions(selectedEmotions.filter((e) => e !== emotion));
    } else {
      if (selectedEmotions.length >= 5) {
        toast.error("最多只能选择5个情绪标签");
        return;
      }
      setSelectedEmotions([...selectedEmotions, emotion]);
    }
  };

  const handleSave = () => {
    if (!title.trim()) {
      toast.error("请输入日记标题");
      return;
    }
    if (!content.trim()) {
      toast.error("请输入日记内容");
      return;
    }
    if (selectedEmotions.length === 0) {
      toast.error("请至少选择一个情绪标签");
      return;
    }

    onSave({
      title: title.trim(),
      content: content.trim(),
      emotions: selectedEmotions,
    });
    toast.success("日记保存成功");
  };

  const wordCount = content.trim().length;

  return (
    <div className="min-h-screen bg-[#FAF3E0]">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-white border-b border-[#E0E0E0]">
        <div className="flex items-center justify-between p-4">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ArrowLeft className="w-6 h-6" />
          </Button>
          <h2 className="text-[18px] font-semibold">编辑日记</h2>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleSave}
            className="text-[#FFA726]"
          >
            <Check className="w-6 h-6" />
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 pb-24 space-y-6">
        {/* Date Display */}
        <div className="flex items-center gap-2 text-sm text-[#757575]">
          <span>📅</span>
          <span>2025年11月17日 星期日</span>
          <span>☀️</span>
        </div>

        {/* Title Input */}
        <div>
          <label className="block text-sm font-semibold text-[#424242] mb-2">
            标题
          </label>
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="给这篇日记起个标题..."
            className="text-lg font-semibold border-[#E0E0E0] focus:border-[#FFA726]"
          />
        </div>

        {/* Emotion Tags */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <label className="text-sm font-semibold text-[#424242]">
              <Smile className="w-4 h-4 inline mr-1" />
              情绪标签
            </label>
            <span className="text-xs text-[#9E9E9E]">
              {selectedEmotions.length}/5
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {emotionOptions.map((emotion) => {
              const isSelected = selectedEmotions.includes(emotion);
              return (
                <Badge
                  key={emotion}
                  onClick={() => handleEmotionToggle(emotion)}
                  className={`cursor-pointer transition-all ${
                    isSelected
                      ? "bg-[#FFA726] text-white hover:bg-[#FF9800]"
                      : "bg-white text-[#757575] border border-[#E0E0E0] hover:bg-[#FAF3E0]"
                  }`}
                >
                  {emotion}
                </Badge>
              );
            })}
          </div>
        </div>

        {/* Content Input */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-semibold text-[#424242]">
              内容
            </label>
            <span className="text-xs text-[#9E9E9E]">{wordCount} 字</span>
          </div>
          <Textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="写下你的故事..."
            className="min-h-[400px] text-[17px] leading-[1.8] border-[#E0E0E0] focus:border-[#FFA726] resize-none"
          />
        </div>

        {/* Images Section */}
        <div>
          <label className="text-sm font-semibold text-[#424242] mb-3 block">
            照片
          </label>
          <div className="grid grid-cols-3 gap-3">
            <div className="aspect-square rounded-xl overflow-hidden">
              <img
                src="https://images.unsplash.com/photo-1592976370975-dcc9e764374f?w=400"
                alt="Diary photo"
                className="w-full h-full object-cover"
              />
            </div>
            <button className="aspect-square rounded-xl border-2 border-dashed border-[#E0E0E0] bg-white flex items-center justify-center hover:bg-[#FAF3E0] transition-colors">
              <ImageIcon className="w-8 h-8 text-[#9E9E9E]" />
            </button>
          </div>
        </div>

        {/* Tips */}
        <div className="bg-[#FFF8E1] rounded-xl p-4">
          <p className="text-sm font-semibold mb-2">✏️ 编辑小贴士</p>
          <ul className="text-xs text-[#757575] space-y-1">
            <li>• 标题简洁明了，能概括日记主题</li>
            <li>• 情绪标签帮助记录当时的心情</li>
            <li>• 内容真实记录，未来回看更有意义</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
