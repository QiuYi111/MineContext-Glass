import { Button } from "./ui/button";
import { BookOpen, Search, WifiOff } from "lucide-react";

interface EmptyStateProps {
  type: "no-diaries" | "no-results" | "network-error";
  onAction?: () => void;
}

export function EmptyState({ type, onAction }: EmptyStateProps) {
  const configs = {
    "no-diaries": {
      icon: BookOpen,
      title: "还没有日记哦",
      subtitle: "去首页上传素材，生成你的第一篇日记吧",
      buttonText: "去上传",
      buttonVariant: "default" as const,
    },
    "no-results": {
      icon: Search,
      title: "没有找到相关日记",
      subtitle: "试试其他关键词或筛选条件",
      buttonText: "清除筛选",
      buttonVariant: "outline" as const,
    },
    "network-error": {
      icon: WifiOff,
      title: "网络连接失败",
      subtitle: "请检查网络设置后重试",
      buttonText: "重试",
      buttonVariant: "default" as const,
    },
  };

  const config = configs[type];
  const Icon = config.icon;

  return (
    <div className="flex flex-col items-center justify-center py-20 px-8">
      <div className="w-[120px] h-[120px] rounded-full bg-[#E0E0E0]/30 flex items-center justify-center mb-6">
        <Icon className="w-16 h-16 text-[#9E9E9E]" strokeWidth={1.5} />
      </div>
      <h3 className="text-[20px] font-semibold mb-2 text-center">
        {config.title}
      </h3>
      <p className="text-caption text-[#757575] text-center mb-6 max-w-[280px]">
        {config.subtitle}
      </p>
      {onAction && (
        <Button
          onClick={onAction}
          variant={config.buttonVariant}
          className={`w-[200px] h-12 rounded-xl ${
            config.buttonVariant === "default"
              ? "bg-[#FFA726] hover:bg-[#FF9800] text-white"
              : "border-[#E0E0E0]"
          }`}
        >
          {config.buttonText}
        </Button>
      )}
    </div>
  );
}
