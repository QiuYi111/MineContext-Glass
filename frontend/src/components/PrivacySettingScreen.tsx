import { useState } from "react";
import { ArrowLeft, Shield, Eye, Lock } from "lucide-react";
import { Button } from "./ui/button";
import { Switch } from "./ui/switch";
import { toast } from "sonner@2.0.3";

interface PrivacySettingScreenProps {
  onBack: () => void;
}

export function PrivacySettingScreen({ onBack }: PrivacySettingScreenProps) {
  const [defaultVisibility, setDefaultVisibility] = useState("private");
  const [allowSearch, setAllowSearch] = useState(true);
  const [showStats, setShowStats] = useState(true);
  const [allowDownload, setAllowDownload] = useState(false);

  const visibilityOptions = [
    {
      id: "private",
      name: "私密",
      icon: <Lock className="w-5 h-5" />,
      description: "仅自己可见",
      color: "from-[#9E9E9E] to-[#757575]",
    },
    {
      id: "friends",
      name: "好友可见",
      icon: "👥",
      description: "只有关注的好友能看到",
      color: "from-[#64B5F6] to-[#42A5F5]",
    },
    {
      id: "public",
      name: "公开",
      icon: "🌍",
      description: "所有人都可以看到",
      color: "from-[#FFA726] to-[#FFB74D]",
    },
  ];

  const handleSave = () => {
    toast.success("隐私设置已保存");
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
          <h2 className="text-[18px] font-semibold">隐私设置</h2>
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
        {/* Security Notice */}
        <div className="bg-[#E3F2FD] rounded-xl p-4 flex gap-3">
          <Shield className="w-5 h-5 text-[#42A5F5] flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-[#424242] mb-1">
              你的隐私很重要
            </p>
            <p className="text-xs text-[#757575]">
              我们承诺保护你的个人信息安全，你可以随时调整隐私设置
            </p>
          </div>
        </div>

        {/* Default Visibility */}
        <div>
          <h3 className="text-sm font-bold text-[#9E9E9E] mb-3 px-2">
            默认可见范围
          </h3>
          <div className="space-y-3">
            {visibilityOptions.map((option) => (
              <button
                key={option.id}
                onClick={() => setDefaultVisibility(option.id)}
                className={`w-full bg-white rounded-2xl p-4 text-left transition-all ${
                  defaultVisibility === option.id
                    ? "ring-2 ring-[#FFA726] shadow-md"
                    : "shadow-sm hover:shadow-md"
                }`}
              >
                <div className="flex items-center gap-4">
                  <div
                    className={`w-12 h-12 rounded-xl bg-gradient-to-br ${option.color} flex items-center justify-center text-xl flex-shrink-0`}
                  >
                    {typeof option.icon === "string" ? (
                      option.icon
                    ) : (
                      <div className="text-white">{option.icon}</div>
                    )}
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold mb-1">{option.name}</h4>
                    <p className="text-sm text-[#9E9E9E]">
                      {option.description}
                    </p>
                  </div>
                  {defaultVisibility === option.id && (
                    <div className="w-6 h-6 rounded-full bg-[#FFA726] flex items-center justify-center">
                      <div className="w-2 h-2 rounded-full bg-white"></div>
                    </div>
                  )}
                </div>
              </button>
            ))}
          </div>
          <p className="text-xs text-[#9E9E9E] mt-3 px-2">
            💡 新创建的日记将默认使用此可见范围，你也可以在发布时单独调整
          </p>
        </div>

        {/* Privacy Options */}
        <div>
          <h3 className="text-sm font-bold text-[#9E9E9E] mb-3 px-2">
            隐私选项
          </h3>
          <div className="bg-white rounded-2xl overflow-hidden shadow-sm">
            <div className="flex items-center justify-between p-5">
              <div className="flex items-center gap-3">
                <Eye className="w-5 h-5 text-[#757575]" />
                <div>
                  <h3 className="font-semibold mb-1">允许搜索</h3>
                  <p className="text-sm text-[#9E9E9E]">
                    允许其他人搜索到我
                  </p>
                </div>
              </div>
              <Switch checked={allowSearch} onCheckedChange={setAllowSearch} />
            </div>
            <div className="h-px bg-[#E0E0E0] mx-5" />
            <div className="flex items-center justify-between p-5">
              <div className="flex items-center gap-3">
                <span className="text-xl">📊</span>
                <div>
                  <h3 className="font-semibold mb-1">显示统计数据</h3>
                  <p className="text-sm text-[#9E9E9E]">
                    在个人主页显示日记数量等统计
                  </p>
                </div>
              </div>
              <Switch checked={showStats} onCheckedChange={setShowStats} />
            </div>
            <div className="h-px bg-[#E0E0E0] mx-5" />
            <div className="flex items-center justify-between p-5">
              <div className="flex items-center gap-3">
                <span className="text-xl">⬇️</span>
                <div>
                  <h3 className="font-semibold mb-1">允许下载</h3>
                  <p className="text-sm text-[#9E9E9E]">
                    允许他人下载我的公开日记
                  </p>
                </div>
              </div>
              <Switch
                checked={allowDownload}
                onCheckedChange={setAllowDownload}
              />
            </div>
          </div>
        </div>

        {/* Data Protection */}
        <div className="bg-white rounded-2xl p-5 shadow-sm">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <Shield className="w-5 h-5 text-[#FFA726]" />
            数据保护
          </h3>
          <div className="space-y-3">
            <button className="w-full flex items-center justify-between py-3 px-4 bg-[#FAF3E0] rounded-xl hover:bg-[#F5EDD8] transition-colors">
              <span className="text-sm font-medium">管理已屏蔽用户</span>
              <span className="text-xs text-[#9E9E9E]">0 人</span>
            </button>
            <button className="w-full flex items-center justify-between py-3 px-4 bg-[#FAF3E0] rounded-xl hover:bg-[#F5EDD8] transition-colors">
              <span className="text-sm font-medium">删除我的账户</span>
              <span className="text-xs text-red-500">永久删除</span>
            </button>
          </div>
        </div>

        {/* Tips */}
        <div className="bg-[#FFF8E1] rounded-xl p-4">
          <p className="text-sm font-semibold mb-2">🔒 安全建议</p>
          <ul className="text-xs text-[#757575] space-y-1">
            <li>• 私密日记不会在社区中展示</li>
            <li>• 好友可见需要对方关注你</li>
            <li>• 公开日记可能被更多人看到和互动</li>
            <li>• 定期检查隐私设置确保符合你的需求</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
