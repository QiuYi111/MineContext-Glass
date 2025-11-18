import { useState, useRef } from "react";
import { ArrowLeft, Upload, Image, Video, X, Check, Loader2 } from "lucide-react";
import { Button } from "./ui/button";
import { toast } from "sonner";
import { glassApi } from "../services/glassApi";

interface FileUploadScreenProps {
  onBack: () => void;
  onUpload: (files: File[], taskId?: string) => void;
  mode: "photo" | "video";
}

export function FileUploadScreen({ onBack, onUpload, mode }: FileUploadScreenProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [previewUrls, setPreviewUrls] = useState<string[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    
    if (files.length === 0) return;

    // 验证文件类型
    const validFiles = files.filter((file) => {
      if (mode === "photo") {
        return file.type.startsWith("image/");
      } else {
        return file.type.startsWith("video/");
      }
    });

    if (validFiles.length !== files.length) {
      toast.error(`请选择${mode === "photo" ? "图片" : "视频"}文件`);
    }

    // 限制视频只能上传一个
    if (mode === "video" && validFiles.length > 1) {
      toast.error("只能上传一个视频文件");
      return;
    }

    // 限制照片最多9张
    if (mode === "photo" && selectedFiles.length + validFiles.length > 9) {
      toast.error("最多只能上传9张照片");
      return;
    }

    // 生成预览URL
    const newPreviewUrls = validFiles.map((file) => URL.createObjectURL(file));
    
    setSelectedFiles([...selectedFiles, ...validFiles]);
    setPreviewUrls([...previewUrls, ...newPreviewUrls]);
  };

  const handleRemoveFile = (index: number) => {
    const newFiles = selectedFiles.filter((_, i) => i !== index);
    const newUrls = previewUrls.filter((_, i) => i !== index);
    
    // 释放旧的URL
    URL.revokeObjectURL(previewUrls[index]);
    
    setSelectedFiles(newFiles);
    setPreviewUrls(newUrls);
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      toast.error("请先选择文件");
      return;
    }

    setIsUploading(true);

    try {
      // For video files, upload to backend first
      if (mode === "video") {
        const videoFile = selectedFiles[0];
        toast.info("开始上传视频文件...");

        const response = await glassApi.uploadVideo(videoFile);
        toast.success("视频上传成功，开始处理...");

        // Pass both files and task ID to parent
        onUpload(selectedFiles, response.task_id);
      } else {
        // For photos, we can upload them directly or start processing
        toast.info(`开始处理 ${selectedFiles.length} 张照片...`);

        // For now, we'll simulate processing for photos
        // In the future, we can implement batch photo upload
        onUpload(selectedFiles);
      }
    } catch (error) {
      console.error("Upload failed:", error);
      toast.error("上传失败，请重试");
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files);
    
    // 模拟文件输入事件
    const input = fileInputRef.current;
    if (input) {
      const dataTransfer = new DataTransfer();
      files.forEach((file) => dataTransfer.items.add(file));
      input.files = dataTransfer.files;
      input.dispatchEvent(new Event("change", { bubbles: true }));
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  return (
    <div className="min-h-screen bg-[#FAF3E0]">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-white border-b border-[#E0E0E0]">
        <div className="flex items-center justify-between p-4">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ArrowLeft className="w-6 h-6" />
          </Button>
          <h2 className="text-[18px] font-semibold">
            {mode === "photo" ? "选择照片" : "选择视频"}
          </h2>
          <div className="w-10" />
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {/* Upload Zone */}
        {selectedFiles.length === 0 ? (
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            className="border-2 border-dashed border-[#E0E0E0] rounded-2xl p-12 text-center bg-white"
          >
            <div className="w-24 h-24 rounded-full bg-gradient-to-br from-[#FFA726] to-[#FFB74D] flex items-center justify-center mx-auto mb-6">
              {mode === "photo" ? (
                <Image className="w-12 h-12 text-white" />
              ) : (
                <Video className="w-12 h-12 text-white" />
              )}
            </div>
            <h3 className="text-[18px] font-semibold mb-2">
              {mode === "photo" ? "选择照片" : "选择视频"}
            </h3>
            <p className="text-sm text-[#757575] mb-6">
              {mode === "photo"
                ? "支持 JPG、PNG 格式，最多9张"
                : "支持 MP4、MOV 格式，最大100MB"}
            </p>
            <Button
              onClick={() => fileInputRef.current?.click()}
              className="bg-[#FFA726] hover:bg-[#FF9800] text-white h-12 px-8"
            >
              <Upload className="w-5 h-5 mr-2" />
              {mode === "photo" ? "选择照片" : "选择视频"}
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              accept={mode === "photo" ? "image/*" : "video/*"}
              multiple={mode === "photo"}
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>
        ) : (
          <>
            {/* Preview Grid */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold">
                  已选择 {selectedFiles.length} 个文件
                </h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => fileInputRef.current?.click()}
                  className="text-[#FFA726]"
                >
                  + 添加更多
                </Button>
              </div>

              <div className="grid grid-cols-3 gap-3">
                {previewUrls.map((url, index) => (
                  <div
                    key={index}
                    className="relative aspect-square rounded-xl overflow-hidden bg-white border border-[#E0E0E0]"
                  >
                    {mode === "photo" ? (
                      <img
                        src={url}
                        alt={`Preview ${index + 1}`}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <video
                        src={url}
                        className="w-full h-full object-cover"
                      />
                    )}
                    <button
                      onClick={() => handleRemoveFile(index)}
                      className="absolute top-2 right-2 w-6 h-6 rounded-full bg-black/50 flex items-center justify-center hover:bg-black/70"
                    >
                      <X className="w-4 h-4 text-white" />
                    </button>
                    <div className="absolute bottom-2 left-2 px-2 py-1 bg-black/50 rounded text-xs text-white">
                      {index + 1}
                    </div>
                  </div>
                ))}
              </div>

              <input
                ref={fileInputRef}
                type="file"
                accept={mode === "photo" ? "image/*" : "video/*"}
                multiple={mode === "photo"}
                onChange={handleFileSelect}
                className="hidden"
              />
            </div>

            {/* File Info */}
            <div className="bg-[#E3F2FD] border border-[#64B5F6] rounded-xl p-4 mb-6">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-full bg-[#64B5F6] flex items-center justify-center flex-shrink-0">
                  <Check className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-sm mb-1">文件准备就绪</p>
                  <p className="text-xs text-[#757575]">
                    {mode === "photo"
                      ? `已选择 ${selectedFiles.length} 张照片，AI将分析并生成精彩的日记内容`
                      : `已选择 1 个视频文件，AI将提取关键画面并生成日记`}
                  </p>
                </div>
              </div>
            </div>

            {/* Tips */}
            <div className="bg-[#FFF8E1] rounded-xl p-4 mb-6">
              <p className="text-sm font-semibold mb-2">💡 小提示</p>
              <ul className="text-xs text-[#757575] space-y-1">
                {mode === "photo" ? (
                  <>
                    <li>• 多张照片可以生成更丰富的故事情节</li>
                    <li>• 建议上传同一主题的照片，效果更好</li>
                    <li>• 清晰的照片能让AI更好地理解场景</li>
                  </>
                ) : (
                  <>
                    <li>• AI会自动提取视频中的关键画面</li>
                    <li>• 建议视频长度在1-5分钟之间</li>
                    <li>• 视频越清晰，生成的日记越精彩</li>
                  </>
                )}
              </ul>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={onBack}
                disabled={isUploading}
                className="flex-1 h-12 border-[#E0E0E0]"
              >
                取消
              </Button>
              <Button
                onClick={handleUpload}
                disabled={isUploading}
                className="flex-1 h-12 bg-[#FFA726] hover:bg-[#FF9800] text-white disabled:opacity-50"
              >
                {isUploading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    {mode === "video" ? "上传中..." : "处理中..."}
                  </>
                ) : (
                  "开始生成"
                )}
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
