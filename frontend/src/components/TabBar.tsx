import { Home, BookOpen, Compass, User } from "lucide-react";

interface TabBarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export function TabBar({ activeTab, onTabChange }: TabBarProps) {
  const tabs = [
    { id: "home", label: "首页", icon: Home },
    { id: "community", label: "发现", icon: Compass },
    { id: "diary", label: "日记", icon: BookOpen },
    { id: "profile", label: "我的", icon: User },
  ];

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-[#E0E0E0] shadow-lg z-50">
      <div className="flex items-center justify-around h-20 max-w-md mx-auto px-4">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className="flex flex-col items-center justify-center gap-1 min-w-[60px]"
            >
              <Icon
                className="w-6 h-6"
                style={{
                  color: isActive ? "#FFA726" : "#9E9E9E",
                  strokeWidth: isActive ? 2 : 1.5,
                }}
              />
              <span
                className="text-xs font-medium"
                style={{
                  color: isActive ? "#FFA726" : "#9E9E9E",
                }}
              >
                {tab.label}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
