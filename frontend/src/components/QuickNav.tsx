import { Button } from "./ui/button";

interface QuickNavProps {
  onNavigate: (page: string) => void;
}

export function QuickNav({ onNavigate }: QuickNavProps) {
  const pages = [
    { id: "welcome", label: "欢迎页" },
    { id: "onboarding", label: "引导轮播" },
    { id: "home", label: "首页" },
    { id: "file-upload-photo", label: "📸 上传照片" },
    { id: "file-upload-video", label: "🎬 上传视频" },
    { id: "camera", label: "📷 拍摄" },
    { id: "processing", label: "⏳ AI处理中" },
    { id: "diary-detail", label: "日记详情" },
    { id: "diary-edit", label: "✏️ 编辑日记" },
    { id: "diary-list", label: "日记列表" },
    { id: "community", label: "🔥 社区发现" },
    { id: "user-profile", label: "👤 用户主页" },
    { id: "community-diary-detail", label: "💬 社区日记" },
    { id: "profile", label: "我的" },
    { id: "diary-style-setting", label: "⚙️ 日记风格" },
    { id: "diary-length-setting", label: "⚙️ 生成长度" },
    { id: "notification-setting", label: "⚙️ 通知设置" },
    { id: "privacy-setting", label: "⚙️ 隐私设置" },
    { id: "export-diaries", label: "💾 导出日记" },
  ];

  return (
    <div className="fixed top-4 right-4 z-50">
      <details className="bg-white rounded-xl shadow-lg border border-[#E0E0E0]">
        <summary className="px-4 py-2 cursor-pointer text-sm font-semibold text-[#FFA726] hover:bg-[#FAF3E0] rounded-t-xl">
          快捷导航 ⚡
        </summary>
        <div className="p-2 border-t border-[#E0E0E0] max-h-[70vh] overflow-y-auto">
          <div className="space-y-1">
            {pages.map((page) => (
              <Button
                key={page.id}
                onClick={() => onNavigate(page.id)}
                variant="ghost"
                className="w-full justify-start text-sm h-8 hover:bg-[#FFA726]/10 hover:text-[#FFA726]"
              >
                {page.label}
              </Button>
            ))}
          </div>
        </div>
      </details>
    </div>
  );
}
