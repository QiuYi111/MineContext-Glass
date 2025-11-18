import { Button } from "./ui/button";
import { Shield, Image, Camera, FolderOpen } from "lucide-react";

interface PermissionsScreenProps {
  onGrant: () => void;
  onSkip: () => void;
}

export function PermissionsScreen({ onGrant, onSkip }: PermissionsScreenProps) {
  const permissions = [
    {
      icon: Image,
      name: "相册访问权限",
      description: "读取你的照片和视频来生成日记",
    },
    {
      icon: Camera,
      name: "相机权限",
      description: "拍摄新的照片和视频",
    },
    {
      icon: FolderOpen,
      name: "存储权限",
      description: "保存生成的日记到本地",
    },
  ];

  return (
    <div className="min-h-screen bg-[#FAF3E0] flex flex-col items-center justify-center p-8">
      <div className="max-w-md w-full">
        {/* Icon */}
        <div className="flex justify-center mb-6">
          <div className="w-16 h-16 rounded-full bg-[#FFA726]/20 flex items-center justify-center">
            <Shield className="w-8 h-8 text-[#FFA726]" />
          </div>
        </div>

        {/* Title */}
        <h2 className="text-[24px] font-bold text-center mb-3" style={{ fontFamily: 'var(--font-heading)' }}>
          开启美好体验
        </h2>

        {/* Subtitle */}
        <p className="text-[16px] text-[#757575] text-center mb-8 leading-relaxed">
          为了让「心镜」更好地为你服务<br />我们需要以下权限
        </p>

        {/* Permissions List */}
        <div className="space-y-5 mb-10">
          {permissions.map((permission, index) => {
            const Icon = permission.icon;
            return (
              <div key={index} className="flex gap-4">
                <div className="w-12 h-12 rounded-full bg-white flex items-center justify-center flex-shrink-0">
                  <Icon className="w-6 h-6 text-[#FFA726]" />
                </div>
                <div className="flex-1">
                  <h4 className="text-[16px] font-semibold mb-1">
                    {permission.name}
                  </h4>
                  <p className="text-caption text-[#757575]">
                    {permission.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Primary Button */}
        <Button
          onClick={onGrant}
          className="w-full h-12 bg-[#FFA726] hover:bg-[#FF9800] text-white rounded-xl mb-4"
        >
          授予权限
        </Button>

        {/* Secondary Action */}
        <Button
          variant="ghost"
          onClick={onSkip}
          className="w-full text-[#9E9E9E] text-sm"
        >
          稍后设置
        </Button>
      </div>
    </div>
  );
}
