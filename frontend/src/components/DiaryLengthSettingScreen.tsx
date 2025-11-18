import { useState } from "react";
import { ArrowLeft, FileText } from "lucide-react";
import { Button } from "./ui/button";
import { Slider } from "./ui/slider";
import { toast } from "sonner@2.0.3";

interface DiaryLengthSettingScreenProps {
  onBack: () => void;
}

export function DiaryLengthSettingScreen({ onBack }: DiaryLengthSettingScreenProps) {
  const [selectedLength, setSelectedLength] = useState("medium");

  const lengthOptions = [
    {
      id: "short",
      name: "简短",
      wordCount: "200-400字",
      description: "快速记录，适合忙碌的日常",
      duration: "约1分钟阅读",
      icon: "📝",
    },
    {
      id: "medium",
      name: "中篇",
      wordCount: "400-800字",
      description: "详细记录，内容丰富完整",
      duration: "约3分钟阅读",
      icon: "📖",
    },
    {
      id: "long",
      name: "长篇",
      wordCount: "800-1500字",
      description: "深度记录，细节丰富生动",
      duration: "约5分钟阅读",
      icon: "📚",
    },
  ];

  const handleSave = () => {
    const selected = lengthOptions.find((opt) => opt.id === selectedLength);
    toast.success(`日记长度已设置为「${selected?.name}」`);
    setTimeout(() => {
      onBack();
    }, 500);
  };

  return (
    <div className="min-h-screen bg-[#FAF3E0]">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-white border-b border-[#E0E0E0]">
        <div className="flex items-center justify-between p-4">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ArrowLeft className="w-6 h-6" />
          </Button>
          <h2 className="text-[18px] font-semibold">AI生成长度</h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleSave}
            className="text-[#FFA726] font-semibold"
          >
            保存
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
        <div className="bg-[#E3F2FD] rounded-xl p-4">
          <p className="text-sm text-[#424242]">
            💡 设置AI生成日记的默认长度，也可以在每次生成时单独调整
          </p>
        </div>

        {/* Length Options */}
        <div className="space-y-4">
          {lengthOptions.map((option) => (
            <button
              key={option.id}
              onClick={() => setSelectedLength(option.id)}
              className={`w-full bg-white rounded-2xl p-5 text-left transition-all ${
                selectedLength === option.id
                  ? "ring-2 ring-[#FFA726] shadow-md"
                  : "shadow-sm hover:shadow-md"
              }`}
            >
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#FFA726] to-[#FFB74D] flex items-center justify-center text-2xl flex-shrink-0">
                  {option.icon}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-lg">{option.name}</h3>
                    <span className="text-xs text-[#9E9E9E] bg-[#F5F5F5] px-2 py-1 rounded">
                      {option.wordCount}
                    </span>
                  </div>
                  <p className="text-sm text-[#757575] mb-2">
                    {option.description}
                  </p>
                  <div className="flex items-center gap-2 text-xs text-[#9E9E9E]">
                    <FileText className="w-3 h-3" />
                    <span>{option.duration}</span>
                  </div>
                </div>
                {selectedLength === option.id && (
                  <div className="w-6 h-6 rounded-full bg-[#FFA726] flex items-center justify-center">
                    <div className="w-2 h-2 rounded-full bg-white"></div>
                  </div>
                )}
              </div>
            </button>
          ))}
        </div>

        {/* Sample Preview */}
        <div className="bg-white rounded-2xl p-5">
          <h4 className="font-semibold mb-3 flex items-center gap-2">
            <span>预览示例</span>
            <span className="text-xs text-[#9E9E9E]">
              ({lengthOptions.find((o) => o.id === selectedLength)?.name})
            </span>
          </h4>
          <div className="bg-[#FAF3E0] rounded-xl p-4 space-y-3">
            {selectedLength === "short" && (
              <p className="text-sm leading-relaxed text-[#424242]">
                今天天气晴朗，和家人一起去公园野餐。孩子们玩得很开心，我们享受了美好的家庭时光。这样的周末让人感到温暖和满足。
              </p>
            )}
            {selectedLength === "medium" && (
              <>
                <p className="text-sm leading-relaxed text-[#424242]">
                  今天的天气格外晴朗，阳光透过树叶洒在草地上，形成斑驳的光影。我们一家人来到公园，铺开野餐垫，享受这难得的周末时光。
                </p>
                <p className="text-sm leading-relaxed text-[#424242]">
                  孩子们在草地上欢快地奔跑，笑声在空气中回荡。我准备的三明治和水果都很受欢迎，大家吃得津津有味。微风轻拂，带来一丝清凉，让这个午后显得格外惬意。
                </p>
              </>
            )}
            {selectedLength === "long" && (
              <>
                <p className="text-sm leading-relaxed text-[#424242]">
                  今天的天气格外晴朗，阳光透过树叶洒在草地上，形成斑驳的光影。清晨醒来，就听见窗外鸟儿清脆的鸣叫，仿佛在催促我们出门去享受这美好的一天。
                </p>
                <p className="text-sm leading-relaxed text-[#424242]">
                  我们一家人来到公园，铺开野餐垫，享受这难得的周末时光。孩子们兴奋地在草地上欢快奔跑，笑声在空气中回荡。我准备的三明治和水果都很受欢迎，大家吃得津津有味。
                </p>
                <p className="text-sm leading-relaxed text-[#424242]">
                  微风轻拂，带来一丝清凉，让这个午后显得格外惬意。看着家人们脸上洋溢的笑容，我深深感受到了生活的美好。这些简单而纯粹的时刻，才是我们最珍贵的财富。
                </p>
              </>
            )}
          </div>
        </div>

        {/* Tips */}
        <div className="bg-[#FFF8E1] rounded-xl p-4">
          <p className="text-sm font-semibold mb-2">💡 温馨提示</p>
          <ul className="text-xs text-[#757575] space-y-1">
            <li>• 简短模式适合快速浏览和每日记录</li>
            <li>• 中篇模式平衡内容和阅读时间</li>
            <li>• 长篇模式适合重要时刻的详细记录</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
