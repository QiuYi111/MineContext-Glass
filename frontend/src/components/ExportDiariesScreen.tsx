import { useState } from "react";
import { ArrowLeft, Download, FileText, Image, Calendar } from "lucide-react";
import { Button } from "./ui/button";
import { Checkbox } from "./ui/checkbox";
import { toast } from "sonner@2.0.3";

interface ExportDiariesScreenProps {
  onBack: () => void;
}

export function ExportDiariesScreen({ onBack }: ExportDiariesScreenProps) {
  const [selectedFormat, setSelectedFormat] = useState("pdf");
  const [includeImages, setIncludeImages] = useState(true);
  const [includeEmotions, setIncludeEmotions] = useState(true);
  const [dateRange, setDateRange] = useState("all");

  const formats = [
    {
      id: "pdf",
      name: "PDF 文档",
      icon: "📄",
      description: "适合打印和分享",
      size: "约 2-5 MB",
    },
    {
      id: "txt",
      name: "纯文本",
      icon: "📝",
      description: "轻量级，易于编辑",
      size: "约 100-500 KB",
    },
    {
      id: "html",
      name: "HTML 网页",
      icon: "🌐",
      description: "保留格式，浏览器可查看",
      size: "约 500 KB - 2 MB",
    },
    {
      id: "json",
      name: "JSON 数据",
      icon: "💾",
      description: "包含完整数据结构",
      size: "约 200 KB - 1 MB",
    },
  ];

  const dateRanges = [
    { id: "all", name: "全部日记", count: 45 },
    { id: "this-year", name: "今年", count: 32 },
    { id: "this-month", name: "本月", count: 8 },
    { id: "custom", name: "自定义范围", count: 0 },
  ];

  const handleExport = () => {
    const formatName = formats.find((f) => f.id === selectedFormat)?.name;
    toast.success(`正在导出为 ${formatName}，请稍候...`);
    
    // 模拟导出过程
    setTimeout(() => {
      toast.success("导出成功！文件已保存到下载文件夹");
      setTimeout(() => {
        onBack();
      }, 1000);
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-[#FAF3E0]">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-white border-b border-[#E0E0E0]">
        <div className="flex items-center justify-between p-4">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ArrowLeft className="w-6 h-6" />
          </Button>
          <h2 className="text-[18px] font-semibold">导出日记</h2>
          <div className="w-10" />
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
        {/* Export Format */}
        <div>
          <h3 className="text-sm font-bold text-[#9E9E9E] mb-3 px-2">
            导出格式
          </h3>
          <div className="space-y-3">
            {formats.map((format) => (
              <button
                key={format.id}
                onClick={() => setSelectedFormat(format.id)}
                className={`w-full bg-white rounded-2xl p-4 text-left transition-all ${
                  selectedFormat === format.id
                    ? "ring-2 ring-[#FFA726] shadow-md"
                    : "shadow-sm hover:shadow-md"
                }`}
              >
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#FFA726] to-[#FFB74D] flex items-center justify-center text-2xl flex-shrink-0">
                    {format.icon}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-semibold">{format.name}</h4>
                      <span className="text-xs text-[#9E9E9E] bg-[#F5F5F5] px-2 py-0.5 rounded">
                        {format.size}
                      </span>
                    </div>
                    <p className="text-sm text-[#9E9E9E]">
                      {format.description}
                    </p>
                  </div>
                  {selectedFormat === format.id && (
                    <div className="w-6 h-6 rounded-full bg-[#FFA726] flex items-center justify-center">
                      <div className="w-2 h-2 rounded-full bg-white"></div>
                    </div>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Date Range */}
        <div>
          <h3 className="text-sm font-bold text-[#9E9E9E] mb-3 px-2">
            时间范围
          </h3>
          <div className="bg-white rounded-2xl overflow-hidden shadow-sm">
            {dateRanges.map((range, index) => (
              <div key={range.id}>
                <button
                  onClick={() => setDateRange(range.id)}
                  className="w-full flex items-center justify-between p-4 hover:bg-[#FAF3E0] transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <Calendar className="w-5 h-5 text-[#757575]" />
                    <span className="font-medium">{range.name}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    {range.count > 0 && (
                      <span className="text-sm text-[#9E9E9E]">
                        {range.count} 篇
                      </span>
                    )}
                    <div
                      className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                        dateRange === range.id
                          ? "border-[#FFA726] bg-[#FFA726]"
                          : "border-[#E0E0E0]"
                      }`}
                    >
                      {dateRange === range.id && (
                        <div className="w-2 h-2 rounded-full bg-white"></div>
                      )}
                    </div>
                  </div>
                </button>
                {index < dateRanges.length - 1 && (
                  <div className="h-px bg-[#E0E0E0] mx-4" />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Export Options */}
        <div>
          <h3 className="text-sm font-bold text-[#9E9E9E] mb-3 px-2">
            导出选项
          </h3>
          <div className="bg-white rounded-2xl overflow-hidden shadow-sm">
            <label className="flex items-center justify-between p-4 cursor-pointer hover:bg-[#FAF3E0] transition-colors">
              <div className="flex items-center gap-3">
                <Image className="w-5 h-5 text-[#757575]" />
                <span className="font-medium">包含图片</span>
              </div>
              <Checkbox
                checked={includeImages}
                onCheckedChange={(checked) =>
                  setIncludeImages(checked as boolean)
                }
              />
            </label>
            <div className="h-px bg-[#E0E0E0] mx-4" />
            <label className="flex items-center justify-between p-4 cursor-pointer hover:bg-[#FAF3E0] transition-colors">
              <div className="flex items-center gap-3">
                <span className="text-xl">😊</span>
                <span className="font-medium">包含情绪标签</span>
              </div>
              <Checkbox
                checked={includeEmotions}
                onCheckedChange={(checked) =>
                  setIncludeEmotions(checked as boolean)
                }
              />
            </label>
          </div>
        </div>

        {/* Summary */}
        <div className="bg-gradient-to-br from-[#FFA726] to-[#FFB74D] rounded-2xl p-5 text-white">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <FileText className="w-5 h-5" />
            导出摘要
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-white/80">格式：</span>
              <span className="font-semibold">
                {formats.find((f) => f.id === selectedFormat)?.name}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/80">范围：</span>
              <span className="font-semibold">
                {dateRanges.find((r) => r.id === dateRange)?.name}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-white/80">日记数量：</span>
              <span className="font-semibold">
                {dateRanges.find((r) => r.id === dateRange)?.count || 0} 篇
              </span>
            </div>
          </div>
        </div>

        {/* Export Button */}
        <Button
          onClick={handleExport}
          className="w-full h-12 bg-[#FFA726] hover:bg-[#FF9800] text-white text-base font-semibold"
        >
          <Download className="w-5 h-5 mr-2" />
          开始导出
        </Button>

        {/* Tips */}
        <div className="bg-[#FFF8E1] rounded-xl p-4">
          <p className="text-sm font-semibold mb-2">💡 导出提示</p>
          <ul className="text-xs text-[#757575] space-y-1">
            <li>• PDF 格式最适合打印和存档</li>
            <li>• 纯文本格式文件最小，便于传输</li>
            <li>• JSON 格式可用于数据备份和迁移</li>
            <li>• 包含图片会显著增加文件大小</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
