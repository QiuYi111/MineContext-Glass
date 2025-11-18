import { ArrowLeft, User, Bell, Palette, Shield, HelpCircle, LogOut } from "lucide-react";
import { Button } from "./ui/button";
import { Switch } from "./ui/switch";
import { Label } from "./ui/label";
import { Avatar } from "./ui/avatar";
import { Separator } from "./ui/separator";

interface SettingsPageProps {
  onNavigate: (page: string) => void;
}

export function SettingsPage({ onNavigate }: SettingsPageProps) {
  return (
    <div className="min-h-screen bg-[#F1F5F9]">
      {/* 顶部导航 */}
      <header className="bg-white border-b border-[#F1F5F9] h-16 flex items-center px-8 sticky top-0 z-10">
        <Button
          variant="ghost"
          onClick={() => onNavigate("dashboard")}
          className="mr-4"
        >
          <ArrowLeft className="w-5 h-5 mr-2" />
          返回
        </Button>
        <h2>设置</h2>
      </header>

      {/* 主内容区 */}
      <main className="max-w-4xl mx-auto p-8">
        {/* 个人信息 */}
        <div className="bg-white rounded-2xl p-6 mb-6 shadow-sm">
          <div className="flex items-center gap-4 mb-6">
            <User className="w-5 h-5 text-[#E94E77]" />
            <h3>个人信息</h3>
          </div>
          
          <div className="flex items-center gap-6">
            <Avatar className="w-20 h-20">
              <div className="w-full h-full gradient-primary flex items-center justify-center text-white text-2xl">
                用
              </div>
            </Avatar>
            <div className="flex-1">
              <p style={{ fontSize: '18px', fontWeight: 500 }}>用户昵称</p>
              <p className="caption">user@example.com</p>
            </div>
            <Button variant="outline" className="border-[#94A3B8]">
              编辑资料
            </Button>
          </div>
        </div>

        {/* 通知设置 */}
        <div className="bg-white rounded-2xl p-6 mb-6 shadow-sm">
          <div className="flex items-center gap-4 mb-6">
            <Bell className="w-5 h-5 text-[#E94E77]" />
            <h3>通知设置</h3>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>日记生成完成通知</Label>
                <p className="caption">AI完成日记生成时接收通知</p>
              </div>
              <Switch defaultChecked />
            </div>
            
            <Separator className="bg-[#F1F5F9]" />
            
            <div className="flex items-center justify-between">
              <div>
                <Label>每日回顾提醒</Label>
                <p className="caption">每天固定时间收到回顾提醒</p>
              </div>
              <Switch />
            </div>
            
            <Separator className="bg-[#F1F5F9]" />
            
            <div className="flex items-center justify-between">
              <div>
                <Label>邮件通知</Label>
                <p className="caption">通过邮件接收重要更新</p>
              </div>
              <Switch defaultChecked />
            </div>
          </div>
        </div>

        {/* 外观设置 */}
        <div className="bg-white rounded-2xl p-6 mb-6 shadow-sm">
          <div className="flex items-center gap-4 mb-6">
            <Palette className="w-5 h-5 text-[#E94E77]" />
            <h3>外观设置</h3>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>深色模式</Label>
                <p className="caption">切换到深色主题</p>
              </div>
              <Switch />
            </div>
            
            <Separator className="bg-[#F1F5F9]" />
            
            <div>
              <Label className="mb-3 block">日记字体风格</Label>
              <div className="flex gap-3">
                <button className="px-4 py-2 rounded-lg bg-[#F1F5F9] border-2 border-[#E94E77] text-[#E94E77]">
                  手写体
                </button>
                <button className="px-4 py-2 rounded-lg bg-[#F1F5F9] border-2 border-transparent text-[#64748B] hover:border-[#94A3B8]">
                  宋体
                </button>
                <button className="px-4 py-2 rounded-lg bg-[#F1F5F9] border-2 border-transparent text-[#64748B] hover:border-[#94A3B8]">
                  黑体
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* 隐私与安全 */}
        <div className="bg-white rounded-2xl p-6 mb-6 shadow-sm">
          <div className="flex items-center gap-4 mb-6">
            <Shield className="w-5 h-5 text-[#E94E77]" />
            <h3>隐私与安全</h3>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>本地数据加密</Label>
                <p className="caption">使用加密保护本地日记数据</p>
              </div>
              <Switch defaultChecked />
            </div>
            
            <Separator className="bg-[#F1F5F9]" />
            
            <div className="flex items-center justify-between">
              <div>
                <Label>自动备份</Label>
                <p className="caption">定期备份日记到云端</p>
              </div>
              <Switch defaultChecked />
            </div>
            
            <Separator className="bg-[#F1F5F9]" />
            
            <Button variant="outline" className="w-full border-[#94A3B8]">
              导出所有数据
            </Button>
          </div>
        </div>

        {/* 帮助与支持 */}
        <div className="bg-white rounded-2xl p-6 mb-6 shadow-sm">
          <div className="flex items-center gap-4 mb-6">
            <HelpCircle className="w-5 h-5 text-[#E94E77]" />
            <h3>帮助与支持</h3>
          </div>
          
          <div className="space-y-3">
            <Button variant="ghost" className="w-full justify-start text-[#64748B]">
              使用指南
            </Button>
            <Button variant="ghost" className="w-full justify-start text-[#64748B]">
              常见问题
            </Button>
            <Button variant="ghost" className="w-full justify-start text-[#64748B]">
              反馈建议
            </Button>
            <Button variant="ghost" className="w-full justify-start text-[#64748B]">
              关于我们
            </Button>
          </div>
        </div>

        {/* 退出登录 */}
        <div className="bg-white rounded-2xl p-6 shadow-sm">
          <Button variant="outline" className="w-full border-destructive text-destructive hover:bg-destructive hover:text-white">
            <LogOut className="w-5 h-5 mr-2" />
            退出登录
          </Button>
        </div>

        {/* 版本信息 */}
        <div className="text-center mt-8">
          <p className="caption">AI日记本 v1.0.0</p>
        </div>
      </main>
    </div>
  );
}
