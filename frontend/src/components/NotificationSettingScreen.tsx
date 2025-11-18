import { useState } from "react";
import { ArrowLeft, Bell, Clock } from "lucide-react";
import { Button } from "./ui/button";
import { Switch } from "./ui/switch";
import { toast } from "sonner@2.0.3";

interface NotificationSettingScreenProps {
  onBack: () => void;
}

export function NotificationSettingScreen({ onBack }: NotificationSettingScreenProps) {
  const [dailyReminder, setDailyReminder] = useState(true);
  const [reminderTime, setReminderTime] = useState("09:00");
  const [weekendReminder, setWeekendReminder] = useState(true);
  const [communityNotify, setCommunityNotify] = useState(true);
  const [likeNotify, setLikeNotify] = useState(true);
  const [commentNotify, setCommentNotify] = useState(true);
  const [followNotify, setFollowNotify] = useState(true);

  const timeOptions = [
    "07:00", "08:00", "09:00", "10:00", "11:00",
    "12:00", "14:00", "16:00", "18:00", "20:00", "21:00"
  ];

  const handleSave = () => {
    toast.success("通知设置已保存");
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
          <h2 className="text-[18px] font-semibold">通知设置</h2>
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
        {/* Daily Reminder Section */}
        <div className="bg-white rounded-2xl p-5 shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#FFA726] to-[#FFB74D] flex items-center justify-center">
              <Bell className="w-5 h-5 text-white" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold">每日提醒</h3>
              <p className="text-xs text-[#9E9E9E]">提醒你记录每天的生活</p>
            </div>
            <Switch
              checked={dailyReminder}
              onCheckedChange={setDailyReminder}
            />
          </div>

          {dailyReminder && (
            <div className="pl-[52px]">
              <label className="text-sm text-[#757575] mb-2 block flex items-center gap-2">
                <Clock className="w-4 h-4" />
                提醒时间
              </label>
              <div className="grid grid-cols-4 gap-2">
                {timeOptions.map((time) => (
                  <button
                    key={time}
                    onClick={() => setReminderTime(time)}
                    className={`py-2 px-3 rounded-lg text-sm transition-all ${
                      reminderTime === time
                        ? "bg-[#FFA726] text-white"
                        : "bg-[#F5F5F5] text-[#424242] hover:bg-[#E0E0E0]"
                    }`}
                  >
                    {time}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Weekend Reminder */}
        <div className="bg-white rounded-2xl overflow-hidden shadow-sm">
          <div className="flex items-center justify-between p-5">
            <div>
              <h3 className="font-semibold mb-1">周末提醒</h3>
              <p className="text-sm text-[#9E9E9E]">周末也接收记录提醒</p>
            </div>
            <Switch
              checked={weekendReminder}
              onCheckedChange={setWeekendReminder}
            />
          </div>
        </div>

        {/* Community Notifications */}
        <div>
          <h3 className="text-sm font-bold text-[#9E9E9E] mb-3 px-2">
            社区互动通知
          </h3>
          <div className="bg-white rounded-2xl overflow-hidden shadow-sm">
            <div className="flex items-center justify-between p-5">
              <div>
                <h3 className="font-semibold mb-1">评论通知</h3>
                <p className="text-sm text-[#9E9E9E]">有人评论你的日记</p>
              </div>
              <Switch
                checked={commentNotify}
                onCheckedChange={setCommentNotify}
              />
            </div>
            <div className="h-px bg-[#E0E0E0] mx-5" />
            <div className="flex items-center justify-between p-5">
              <div>
                <h3 className="font-semibold mb-1">点赞通知</h3>
                <p className="text-sm text-[#9E9E9E]">有人喜欢你的日记</p>
              </div>
              <Switch
                checked={likeNotify}
                onCheckedChange={setLikeNotify}
              />
            </div>
            <div className="h-px bg-[#E0E0E0] mx-5" />
            <div className="flex items-center justify-between p-5">
              <div>
                <h3 className="font-semibold mb-1">关注通知</h3>
                <p className="text-sm text-[#9E9E9E]">有新用户关注你</p>
              </div>
              <Switch
                checked={followNotify}
                onCheckedChange={setFollowNotify}
              />
            </div>
            <div className="h-px bg-[#E0E0E0] mx-5" />
            <div className="flex items-center justify-between p-5">
              <div>
                <h3 className="font-semibold mb-1">社区动态</h3>
                <p className="text-sm text-[#9E9E9E]">关注的人发布新日记</p>
              </div>
              <Switch
                checked={communityNotify}
                onCheckedChange={setCommunityNotify}
              />
            </div>
          </div>
        </div>

        {/* Tips */}
        <div className="bg-[#FFF8E1] rounded-xl p-4">
          <p className="text-sm font-semibold mb-2">💡 温馨提示</p>
          <ul className="text-xs text-[#757575] space-y-1">
            <li>• 适度的提醒可以帮助养成记录习惯</li>
            <li>• 可以根据个人作息调整提醒时间</li>
            <li>• 关闭不需要的通知保持专注</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
