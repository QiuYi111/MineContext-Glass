import { useState } from "react";
import { X, Globe, Users, Lock, Check } from "lucide-react";
import { Button } from "./ui/button";
import { motion } from "motion/react";

interface PublishSettingsModalProps {
  onClose: () => void;
  onPublish: (visibility: string) => void;
  diaryTitle: string;
}

export function PublishSettingsModal({
  onClose,
  onPublish,
  diaryTitle,
}: PublishSettingsModalProps) {
  const [selectedVisibility, setSelectedVisibility] = useState("public");

  const visibilityOptions = [
    {
      id: "public",
      icon: Globe,
      label: "公开",
      description: "所有人都可以看到这篇日记",
      color: "#64B5F6",
    },
    {
      id: "friends",
      icon: Users,
      label: "好友可见",
      description: "只有你的好友可以看到",
      color: "#81C784",
    },
    {
      id: "private",
      icon: Lock,
      label: "私密",
      description: "只有你自己可以看到",
      color: "#9E9E9E",
    },
  ];

  const handlePublish = () => {
    onPublish(selectedVisibility);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/50">
      <motion.div
        initial={{ y: "100%" }}
        animate={{ y: 0 }}
        exit={{ y: "100%" }}
        transition={{ type: "spring", damping: 25, stiffness: 300 }}
        className="w-full max-w-md bg-white rounded-t-3xl shadow-xl"
      >
        {/* Handle */}
        <div className="flex justify-center pt-3 pb-2">
          <div className="w-10 h-1 bg-[#E0E0E0] rounded-full" />
        </div>

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#E0E0E0]">
          <h2 className="text-[18px] font-semibold">发布设置</h2>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="w-6 h-6" />
          </Button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Diary Preview */}
          <div className="bg-[#FAF3E0] rounded-xl p-4 mb-6">
            <p className="text-sm text-[#9E9E9E] mb-1">将要发布</p>
            <h3
              className="text-[16px] font-semibold"
              style={{ fontFamily: "var(--font-heading)" }}
            >
              {diaryTitle}
            </h3>
          </div>

          {/* Visibility Options */}
          <div className="space-y-3 mb-6">
            <label className="text-sm font-semibold text-[#757575]">
              选择可见范围
            </label>
            {visibilityOptions.map((option) => {
              const Icon = option.icon;
              const isSelected = selectedVisibility === option.id;
              return (
                <button
                  key={option.id}
                  onClick={() => setSelectedVisibility(option.id)}
                  className={`w-full flex items-start gap-4 p-4 rounded-xl border-2 transition-all ${
                    isSelected
                      ? "border-[#FFA726] bg-[#FFA726]/5"
                      : "border-[#E0E0E0] bg-white"
                  }`}
                >
                  <div
                    className="w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0"
                    style={{
                      backgroundColor: isSelected
                        ? `${option.color}20`
                        : "#F5F5DC",
                    }}
                  >
                    <Icon
                      className="w-6 h-6"
                      style={{
                        color: isSelected ? option.color : "#9E9E9E",
                      }}
                    />
                  </div>
                  <div className="flex-1 text-left">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold">{option.label}</span>
                      {isSelected && (
                        <Check className="w-4 h-4 text-[#FFA726]" />
                      )}
                    </div>
                    <p className="text-sm text-[#757575]">
                      {option.description}
                    </p>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Additional Options */}
          <div className="bg-[#F5F5DC] rounded-xl p-4 mb-6">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-sm">💡</span>
              <p className="text-sm text-[#757575]">
                发布后，你可以随时修改可见范围
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={onClose}
              className="flex-1 h-12 border-[#E0E0E0]"
            >
              取消
            </Button>
            <Button
              onClick={handlePublish}
              className="flex-1 h-12 bg-[#FFA726] hover:bg-[#FF9800] text-white"
            >
              发布日记
            </Button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
