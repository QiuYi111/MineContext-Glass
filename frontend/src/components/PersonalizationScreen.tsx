import { useState } from "react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Switch } from "./ui/switch";
import { Sun, BookOpen, Minimize2, Sparkles } from "lucide-react";

interface PersonalizationScreenProps {
  onComplete: () => void;
}

export function PersonalizationScreen({ onComplete }: PersonalizationScreenProps) {
  const [selectedStyle, setSelectedStyle] = useState("warm");
  const [nickname, setNickname] = useState("");
  const [notificationEnabled, setNotificationEnabled] = useState(true);

  const styles = [
    { id: "warm", label: "温馨", icon: Sun },
    { id: "literary", label: "文艺", icon: BookOpen },
    { id: "minimal", label: "简约", icon: Minimize2 },
    { id: "lively", label: "活泼", icon: Sparkles },
  ];

  return (
    <div className="min-h-screen bg-[#FAF3E0] flex flex-col">
      {/* Header */}
      <div className="p-6 text-center border-b border-[#E0E0E0]">
        <h2 className="text-[20px] font-bold" style={{ fontFamily: 'var(--font-heading)' }}>
          个性化设置
        </h2>
      </div>

      {/* Content */}
      <div className="flex-1 p-6 space-y-8 overflow-auto">
        {/* Diary Style */}
        <div>
          <Label className="text-[16px] font-semibold mb-4 block">
            选择你喜欢的日记风格
          </Label>
          <div className="grid grid-cols-2 gap-4">
            {styles.map((style) => {
              const Icon = style.icon;
              return (
                <button
                  key={style.id}
                  onClick={() => setSelectedStyle(style.id)}
                  className={`h-[100px] rounded-xl flex flex-col items-center justify-center gap-2 transition-all ${
                    selectedStyle === style.id
                      ? "bg-[#FFA726]/10 border-2 border-[#FFA726]"
                      : "bg-white border border-[#E0E0E0]"
                  }`}
                >
                  <Icon
                    className="w-8 h-8"
                    style={{
                      color: selectedStyle === style.id ? "#FFA726" : "#757575",
                    }}
                  />
                  <span
                    className="text-sm font-medium"
                    style={{
                      color: selectedStyle === style.id ? "#FFA726" : "#424242",
                    }}
                  >
                    {style.label}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Nickname Input */}
        <div>
          <Label className="text-[16px] font-semibold mb-4 block">
            我们该如何称呼你？
          </Label>
          <Input
            placeholder="输入你的昵称"
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            className="h-12 rounded-lg border-[#E0E0E0] bg-white"
          />
        </div>

        {/* Notification Toggle */}
        <div className="bg-white rounded-xl p-4 border border-[#E0E0E0]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-[#FFA726]/10 flex items-center justify-center">
                <span className="text-xl">🔔</span>
              </div>
              <Label className="text-[14px]">每日提醒我记录生活</Label>
            </div>
            <Switch
              checked={notificationEnabled}
              onCheckedChange={setNotificationEnabled}
            />
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-6 border-t border-[#E0E0E0]">
        <Button
          onClick={onComplete}
          className="w-full h-12 bg-[#FFA726] hover:bg-[#FF9800] text-white rounded-xl"
        >
          完成设置，开始使用
        </Button>
      </div>
    </div>
  );
}
