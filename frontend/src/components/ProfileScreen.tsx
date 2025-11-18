import { ChevronRight, Edit } from "lucide-react";
import { Button } from "./ui/button";
import { Switch } from "./ui/switch";
import { TabBar } from "./TabBar";

interface ProfileScreenProps {
  onTabChange: (tab: string) => void;
  onNavigate?: (page: string) => void;
}

export function ProfileScreen({ onTabChange, onNavigate }: ProfileScreenProps) {
  const handleSettingClick = (label: string) => {
    const navigationMap: Record<string, string> = {
      "日记风格": "diary-style-setting",
      "AI生成长度": "diary-length-setting",
      "通知设置": "notification-setting",
      "隐私设置": "privacy-setting",
      "导出所有日记": "export-diaries",
      "备份与恢复": "backup-restore",
      "清除缓存": "clear-cache",
      "主题模式": "theme-setting",
      "使用教程": "tutorial",
      "常见问题": "faq",
      "关于心镜": "about",
    };

    const targetPage = navigationMap[label];
    if (targetPage && onNavigate) {
      onNavigate(targetPage);
    }
  };
  const settingsSections = [
    {
      title: "偏好设置",
      items: [
        { label: "日记风格", value: "温馨", hasArrow: true },
        { label: "AI生成长度", value: "中篇", hasArrow: true },
        { label: "自动保存", hasSwitch: true, checked: true },
        { label: "每日提醒", hasSwitch: true, checked: true, extraValue: "09:00" },
      ],
    },
    {
      title: "数据管理",
      items: [
        { label: "导出所有日记", hasArrow: true },
        { label: "备份与恢复", hasArrow: true },
        { label: "清除缓存", value: "128 MB", hasArrow: true },
      ],
    },
    {
      title: "通用",
      items: [
        { label: "通知设置", hasArrow: true },
        { label: "隐私设置", hasArrow: true },
        { label: "主题模式", value: "浅色", hasArrow: true },
        { label: "语言", value: "简体中文", hasArrow: true },
      ],
    },
    {
      title: "关于与帮助",
      items: [
        { label: "使用教程", hasArrow: true },
        { label: "常见问题", hasArrow: true },
        { label: "联系我们", hasArrow: true },
        { label: "关于心镜", hasArrow: true },
        { label: "版本号", value: "v1.0.0", hasArrow: false },
      ],
    },
  ];

  return (
    <div className="min-h-screen bg-[#FAF3E0] pb-24">
      {/* Header */}
      <div className="text-center p-6 border-b border-[#E0E0E0] bg-white">
        <h1 className="text-[20px] font-bold" style={{ fontFamily: 'var(--font-heading)' }}>
          我的
        </h1>
      </div>

      {/* Profile Section */}
      <div className="p-6">
        <div className="bg-white rounded-2xl p-6 shadow-sm mb-6">
          <div className="flex flex-col items-center mb-6">
            {/* Avatar */}
            <div className="relative mb-3">
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-[#FFA726] to-[#FFB74D] flex items-center justify-center text-white text-2xl font-bold">
                小明
              </div>
              <button className="absolute bottom-0 right-0 w-7 h-7 rounded-full bg-white border-2 border-white shadow-lg flex items-center justify-center">
                <Edit className="w-4 h-4 text-[#FFA726]" />
              </button>
            </div>

            {/* Name */}
            <h2 className="text-[20px] font-semibold mb-1">小明</h2>
            <p className="text-sm text-[#757575]">记录生活，感受美好</p>
          </div>

          {/* Stats */}
          <div className="flex justify-center gap-8 pt-4 border-t border-[#E0E0E0]">
            <div className="text-center">
              <div className="flex items-center justify-center gap-2 mb-1">
                <span className="text-xl">📅</span>
                <span className="text-[20px] font-bold text-[#FFA726]">45</span>
              </div>
              <p className="text-xs text-[#9E9E9E]">已记录天数</p>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center gap-2 mb-1">
                <span className="text-xl">📖</span>
                <span className="text-[20px] font-bold text-[#FFA726]">45</span>
              </div>
              <p className="text-xs text-[#9E9E9E]">生成日记</p>
            </div>
          </div>
        </div>

        {/* Settings Sections */}
        {settingsSections.map((section, sectionIndex) => (
          <div key={sectionIndex} className="mb-6">
            <h3 className="text-sm font-bold text-[#9E9E9E] mb-3 px-2">
              {section.title}
            </h3>
            <div className="bg-white rounded-2xl overflow-hidden shadow-sm">
              {section.items.map((item, itemIndex) => (
                <div key={itemIndex}>
                  <button
                    className="w-full flex items-center gap-4 p-4 hover:bg-[#FAF3E0] transition-colors"
                    onClick={() => !item.hasSwitch && handleSettingClick(item.label)}
                  >
                    <span className="flex-1 text-left text-[16px] font-medium">
                      {item.label}
                    </span>
                    {item.hasSwitch ? (
                      <div className="flex items-center gap-2">
                        {item.extraValue && (
                          <span className="text-sm text-[#757575]">
                            {item.extraValue}
                          </span>
                        )}
                        <Switch defaultChecked={item.checked} />
                      </div>
                    ) : (
                      <>
                        {item.value && (
                          <span className="text-sm text-[#9E9E9E]">
                            {item.value}
                          </span>
                        )}
                        {item.hasArrow && (
                          <ChevronRight className="w-5 h-5 text-[#9E9E9E]" />
                        )}
                      </>
                    )}
                  </button>
                  {itemIndex < section.items.length - 1 && (
                    <div className="h-px bg-[#E0E0E0] ml-4" />
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Tab Bar */}
      <TabBar activeTab="profile" onTabChange={onTabChange} />
    </div>
  );
}
