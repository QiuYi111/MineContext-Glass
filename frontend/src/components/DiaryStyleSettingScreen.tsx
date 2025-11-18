import { useState, useEffect } from "react";
import { ArrowLeft, Check } from "lucide-react";
import { Button } from "./ui/button";
import { toast } from "sonner";
import { glassApi, UserPreferences } from "../services/glassApi";

interface DiaryStyleSettingScreenProps {
  onBack: () => void;
}

export function DiaryStyleSettingScreen({ onBack }: DiaryStyleSettingScreenProps) {
  const [selectedStyle, setSelectedStyle] = useState("casual");
  const [userPreferences, setUserPreferences] = useState<UserPreferences | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Map UI styles to backend API styles
  const styleMapping: Record<string, 'professional' | 'casual' | 'poetic' | 'humorous'> = {
    "温馨": "casual",
    "文艺": "poetic",
    "简洁": "professional",
    "怀旧": "casual",
    "活力": "humorous",
    "宁静": "poetic"
  };

  const reverseStyleMapping: Record<'professional' | 'casual' | 'poetic' | 'humorous', string> = {
    "professional": "简洁",
    "casual": "温馨",
    "poetic": "文艺",
    "humorous": "活力"
  };

  // Load user preferences on component mount
  useEffect(() => {
    const loadPreferences = async () => {
      try {
        const preferences = await glassApi.getUserPreferences();
        setUserPreferences(preferences);
        setSelectedStyle(reverseStyleMapping[preferences.diary_style] || "温馨");
      } catch (error) {
        console.error('Failed to load user preferences:', error);
        // Continue with default preferences
      }
    };

    loadPreferences();
  }, []);

  const styles = [
    {
      id: "温馨",
      name: "温馨",
      icon: "🌸",
      description: "温暖亲切的叙述风格，适合记录家庭和朋友相关的美好时光",
      color: "from-[#FFA726] to-[#FFB74D]",
    },
    {
      id: "文艺",
      name: "文艺",
      icon: "📖",
      description: "优雅细腻的文学风格，用诗意的语言记录生活点滴",
      color: "from-[#9C27B0] to-[#BA68C8]",
    },
    {
      id: "简洁",
      name: "简洁",
      icon: "✨",
      description: "干净利落的记录方式，重点突出，适合快节奏生活",
      color: "from-[#64B5F6] to-[#42A5F5]",
    },
    {
      id: "怀旧",
      name: "怀旧",
      icon: "🕰️",
      description: "复古温情的叙述风格，让回忆更有年代感和情怀",
      color: "from-[#8D6E63] to-[#A1887F]",
    },
    {
      id: "活力",
      name: "活力",
      icon: "🌈",
      description: "充满激情和能量的表达方式，适合记录运动和冒险",
      color: "from-[#FF5722] to-[#FF7043]",
    },
    {
      id: "宁静",
      name: "宁静",
      icon: "🍃",
      description: "平和舒缓的文字风格，适合记录冥想和内心感悟",
      color: "from-[#81C784] to-[#66BB6A]",
    },
  ];

  const handleSave = async () => {
    try {
      setIsLoading(true);

      // Map selected style to backend format
      const backendStyle = styleMapping[selectedStyle];

      // Update user preferences
      const newPreferences: UserPreferences = {
        diary_style: backendStyle,
        diary_length: userPreferences?.diary_length || 'detailed',
        notifications_enabled: userPreferences?.notifications_enabled ?? true,
        auto_generate_reports: userPreferences?.auto_generate_reports ?? true,
      };

      await glassApi.updateUserPreferences(newPreferences);
      setUserPreferences(newPreferences);

      toast.success(`日记风格已设置为「${selectedStyle}」`);

      // Save to localStorage for persistence
      localStorage.setItem('glass_diary_style', backendStyle);

      setTimeout(() => {
        onBack();
      }, 500);
    } catch (error) {
      console.error('Failed to save style preference:', error);
      toast.error('保存失败，请重试');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FAF3E0]">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-white border-b border-[#E0E0E0]">
        <div className="flex items-center justify-between p-4">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ArrowLeft className="w-6 h-6" />
          </Button>
          <h2 className="text-[18px] font-semibold">日记风格</h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleSave}
            disabled={isLoading}
            className="text-[#FFA726] font-semibold"
          >
            {isLoading ? '保存中...' : '保存'}
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-4">
        <div className="bg-[#E3F2FD] rounded-xl p-4 mb-2">
          <p className="text-sm text-[#424242]">
            💡 选择你喜欢的写作风格，AI会根据你的偏好生成日记内容
          </p>
        </div>

        {styles.map((style) => (
          <button
            key={style.id}
            onClick={() => setSelectedStyle(style.id)}
            className={`w-full bg-white rounded-2xl p-5 text-left transition-all ${
              selectedStyle === style.id
                ? "ring-2 ring-[#FFA726] shadow-md"
                : "shadow-sm hover:shadow-md"
            }`}
          >
            <div className="flex items-start gap-4">
              <div
                className={`w-14 h-14 rounded-xl bg-gradient-to-br ${style.color} flex items-center justify-center text-2xl flex-shrink-0`}
              >
                {style.icon}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-lg">{style.name}</h3>
                  {selectedStyle === style.id && (
                    <Check className="w-5 h-5 text-[#FFA726]" />
                  )}
                </div>
                <p className="text-sm text-[#757575] leading-relaxed">
                  {style.description}
                </p>
              </div>
            </div>
          </button>
        ))}

        {/* Sample Text */}
        <div className="mt-6 bg-white rounded-2xl p-5">
          <h4 className="font-semibold mb-3">示例文本</h4>
          <div className="bg-[#FAF3E0] rounded-xl p-4">
            {selectedStyle === "温馨" && (
              <p className="text-sm leading-relaxed text-[#424242]">
                今天的阳光格外温暖，照在身上暖洋洋的。和家人一起度过的周末，总是那么美好而难忘...
              </p>
            )}
            {selectedStyle === "文艺" && (
              <p className="text-sm leading-relaxed text-[#424242]">
                晨曦微露，光影交错间，生活的诗意悄然绽放。那些平凡的瞬间，都成为了时光里最温柔的注脚...
              </p>
            )}
            {selectedStyle === "简洁" && (
              <p className="text-sm leading-relaxed text-[#424242]">
                周末野餐。天气晴朗，心情愉快。家人欢聚，享受自然。简单而美好。
              </p>
            )}
            {selectedStyle === "怀旧" && (
              <p className="text-sm leading-relaxed text-[#424242]">
                依稀记得，那个午后的阳光，穿过梧桐树的枝叶，洒在泛黄的相册上。时光荏苒，温情依旧...
              </p>
            )}
            {selectedStyle === "活力" && (
              <p className="text-sm leading-relaxed text-[#424242]">
                今天太棒了！阳光灿烂，活力满满！和家人一起享受户外时光，每一刻都充满欢笑和能量！
              </p>
            )}
            {selectedStyle === "宁静" && (
              <p className="text-sm leading-relaxed text-[#424242]">
                静坐草地，感受微风轻拂。内心平和，思绪如流水般缓缓流淌。这一刻，时间仿佛静止...
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
