import { ArrowLeft } from "lucide-react";
import { Button } from "./ui/button";
import { UploadZone } from "./UploadZone";

interface UploadPageProps {
  onNavigate: (page: string) => void;
  onFileSelect: (file: File) => void;
}

export function UploadPage({ onNavigate, onFileSelect }: UploadPageProps) {
  return (
    <div className="min-h-screen bg-[#F1F5F9] flex flex-col">
      {/* 顶部导航 */}
      <header className="bg-white border-b border-[#F1F5F9] h-16 flex items-center px-8">
        <Button
          variant="ghost"
          onClick={() => onNavigate("dashboard")}
          className="mr-4"
        >
          <ArrowLeft className="w-5 h-5 mr-2" />
          返回
        </Button>
        <h2>上传素材</h2>
      </header>

      {/* 上传区域 */}
      <main className="flex-1 p-8">
        <UploadZone onFileSelect={onFileSelect} />
      </main>
    </div>
  );
}
