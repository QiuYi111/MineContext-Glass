import { Upload, Image, Video } from "lucide-react";
import { useState } from "react";
import { Button } from "./ui/button";

interface UploadZoneProps {
  onFileSelect: (file: File) => void;
}

export function UploadZone({ onFileSelect }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      onFileSelect(files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      onFileSelect(files[0]);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center h-full">
      <div
        className={`w-full max-w-2xl border-2 border-dashed rounded-2xl p-12 transition-all duration-300 ${
          isDragging
            ? "border-[#E94E77] bg-[#E94E77]/5 pulse-border"
            : "border-[#94A3B8] bg-white"
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="flex flex-col items-center text-center gap-6">
          <div className="w-20 h-20 rounded-full gradient-primary flex items-center justify-center">
            <Upload className="w-10 h-10 text-white" />
          </div>
          
          <div>
            <h3 className="mb-2">拖放视频或图片到此处，或点击选择文件</h3>
            <p className="caption flex items-center justify-center gap-2">
              <Video className="w-4 h-4" />
              <Image className="w-4 h-4" />
              支持MP4、JPG、PNG，单个文件最大200MB
            </p>
          </div>

          <div className="flex gap-4">
            <label>
              <input
                type="file"
                className="hidden"
                accept="video/mp4,image/jpeg,image/png"
                onChange={handleFileInput}
              />
              <Button
                type="button"
                variant="outline"
                className="cursor-pointer border-[#94A3B8]"
                onClick={() => document.querySelector<HTMLInputElement>('input[type="file"]')?.click()}
              >
                选择文件
              </Button>
            </label>
            <Button variant="ghost" className="text-[#64748B]">
              从相册导入
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
