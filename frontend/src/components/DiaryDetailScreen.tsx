import { useState, useEffect } from "react";
import { ArrowLeft, MoreVertical, Edit, Share2, Heart, Bookmark, Upload } from "lucide-react";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { PublishSettingsModal } from "./PublishSettingsModal";
import { toast } from "sonner";
import { glassApi, DiaryReport } from "../services/glassApi";

interface DiaryDetailScreenProps {
  onBack: () => void;
  onEdit?: () => void;
  timelineId?: string | null;
  reportId?: string | null;
}

export function DiaryDetailScreen({ onBack, onEdit, timelineId, reportId }: DiaryDetailScreenProps) {
  const [isLiked, setIsLiked] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [showPublishModal, setShowPublishModal] = useState(false);
  const [showMoreMenu, setShowMoreMenu] = useState(false);
  const [diaryReport, setDiaryReport] = useState<DiaryReport | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load diary report data
  useEffect(() => {
    const loadDiaryReport = async () => {
      if (!timelineId) {
        // Use mock data if no timelineId provided
        setDiaryReport({
          id: reportId || 'demo-report',
          timeline_id: timelineId || 'demo-timeline',
          title: "阳光下的周末野餐时光",
          content: `今天是一个完美的周末，阳光明媚，微风和煦。我和朋友们一起去了城市公园，享受了一场惬意的野餐。

我们带上了精心准备的食物：三明治、水果沙拉、还有我烘焙的巧克力曲奇。找了一块绿树成荫的草地，铺上格子野餐垫，就这样度过了一个悠闲的下午。

阳光透过树叶洒在草地上，形成斑驳的光影。远处传来孩子们的笑声，还有偶尔飘过的花香。这样的时刻让人感到无比的宁静和幸福。

我们聊了很多话题，从工作到生活，从梦想到现实。在这样美好的氛围中，所有的烦恼似乎都烟消云散了。这大概就是生活最美好的样子吧。`,
          style: 'casual',
          length: 'detailed',
          created_at: new Date().toISOString(),
          summary: "与朋友的美好周末野餐，享受阳光、美食和温馨的交谈时光。",
          insights: [
            "户外活动对心理健康的重要性",
            "友谊是生活中最珍贵的财富",
            "简单的时刻往往最值得珍惜"
          ],
          images: [
            "https://via.placeholder.com/400x300/FFE4B5/000000?text=🧺+阳光野餐",
            "https://via.placeholder.com/400x300/E8F5E8/000000?text=🌳+公园风景"
          ]
        });
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);

        if (reportId) {
          // Load specific report
          const reports = await glassApi.getDiaryReports(timelineId);
          const report = reports.find(r => r.id === reportId);
          if (report) {
            setDiaryReport(report);
          } else {
            // Generate new report if not found
            const newReport = await glassApi.generateReport({
              timeline_id: timelineId,
              style: 'casual',
              length: 'detailed'
            });
            setDiaryReport(newReport);
          }
        } else {
          // Generate new report
          const newReport = await glassApi.generateReport({
            timeline_id: timelineId,
            style: 'casual',
            length: 'detailed'
          });
          setDiaryReport(newReport);
        }
      } catch (error) {
        console.error('Failed to load diary report:', error);
        toast.error("Failed to load diary report");

        // Fallback to mock data
        setDiaryReport({
          id: 'fallback-report',
          timeline_id: timelineId || 'fallback-timeline',
          title: "美好的一天",
          content: "今天是美好的一天，虽然遇到了一些技术问题，但生活依然充满希望。",
          style: 'casual',
          length: 'brief',
          created_at: new Date().toISOString(),
          summary: "日常生活中的一天",
          insights: ["生活总是在继续"]
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadDiaryReport();
  }, [timelineId, reportId]);

  const handlePublish = (visibility: string) => {
    setShowPublishModal(false);
    const visibilityLabels: Record<string, string> = {
      public: "公开",
      friends: "好友可见",
      private: "私密",
    };
    toast.success(`日记已${visibilityLabels[visibility]}发布到社区`);
  };

  const handleSave = () => {
    setIsSaved(!isSaved);
    toast.success(isSaved ? "已取消保存" : "已保存到收藏");
  };

  const handleShare = () => {
    // 使用 Web Share API 或复制链接
    if (navigator.share) {
      navigator
        .share({
          title: "阳光下的周末野餐时光",
          text: "来看看我的日记",
          url: window.location.href,
        })
        .catch(() => {
          // 用户取消分享
        });
    } else {
      // 复制链接
      navigator.clipboard.writeText(window.location.href);
      toast.success("链接已复制到剪贴板");
    }
    setShowMoreMenu(false);
  };

  const handleExport = () => {
    toast.success("日记导出功能开发中");
    setShowMoreMenu(false);
  };

  const handleDelete = () => {
    if (confirm("确定要删除这篇日记吗？此操作无法撤销。")) {
      toast.success("日记已删除");
      setTimeout(() => {
        onBack();
      }, 1000);
    }
    setShowMoreMenu(false);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#FAF3E0] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-[#FFA726] border-t-transparent mx-auto mb-4"></div>
          <p className="text-[#757575]">正在加载日记...</p>
        </div>
      </div>
    );
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const options: Intl.DateTimeFormatOptions = {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      weekday: 'long'
    };
    return date.toLocaleDateString('zh-CN', options);
  };

  const getStyleLabel = (style: string) => {
    const labels: Record<string, string> = {
      professional: '专业',
      casual: '休闲',
      poetic: '诗意',
      humorous: '幽默'
    };
    return labels[style] || '休闲';
  };

  const getLengthLabel = (length: string) => {
    const labels: Record<string, string> = {
      brief: '简短',
      detailed: '详细',
      comprehensive: '全面'
    };
    return labels[length] || '详细';
  };

  return (
    <div className="min-h-screen bg-[#FAF3E0]">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-[#FAF3E0]/80 backdrop-blur-md border-b border-[#E0E0E0]">
        <div className="flex items-center justify-between p-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={onBack}
            className="text-[#424242]"
          >
            <ArrowLeft className="w-6 h-6" />
          </Button>
          <div className="relative">
            <Button
              variant="ghost"
              size="icon"
              className="text-[#424242]"
              onClick={() => setShowMoreMenu(!showMoreMenu)}
            >
              <MoreVertical className="w-6 h-6" />
            </Button>
            {showMoreMenu && (
              <>
                <div
                  className="fixed inset-0 z-20"
                  onClick={() => setShowMoreMenu(false)}
                />
                <div className="absolute right-0 top-12 z-30 bg-white rounded-xl shadow-lg border border-[#E0E0E0] overflow-hidden min-w-[160px]">
                  <button
                    onClick={handleShare}
                    className="w-full flex items-center gap-3 px-4 py-3 hover:bg-[#FAF3E0] transition-colors text-left"
                  >
                    <Share2 className="w-4 h-4" />
                    <span className="text-sm">分享</span>
                  </button>
                  <div className="h-px bg-[#E0E0E0]" />
                  <button
                    onClick={handleExport}
                    className="w-full flex items-center gap-3 px-4 py-3 hover:bg-[#FAF3E0] transition-colors text-left"
                  >
                    <span className="text-sm">📥</span>
                    <span className="text-sm">导出</span>
                  </button>
                  <div className="h-px bg-[#E0E0E0]" />
                  <button
                    onClick={handleDelete}
                    className="w-full flex items-center gap-3 px-4 py-3 hover:bg-red-50 transition-colors text-left text-red-500"
                  >
                    <span className="text-sm">🗑️</span>
                    <span className="text-sm">删除</span>
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="px-6 pb-24">
        {/* Diary Header */}
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm text-[#757575]">📅</span>
            <span className="text-sm text-[#757575]">
              {diaryReport?.created_at ? formatDate(diaryReport.created_at) : '今天'}
            </span>
            <span className="text-sm">☀️</span>
          </div>
          <div className="flex gap-2 mb-4">
            <Badge className="bg-[#FFA726]/20 text-[#FFA726] hover:bg-[#FFA726]/30">
              {diaryReport ? getStyleLabel(diaryReport.style) : '休闲'}
            </Badge>
            <Badge className="bg-[#64B5F6]/20 text-[#64B5F6] hover:bg-[#64B5F6]/30">
              {diaryReport ? getLengthLabel(diaryReport.length) : '详细'}
            </Badge>
            <Badge className="bg-[#81C784]/20 text-[#81C784] hover:bg-[#81C784]/30">
              AI生成
            </Badge>
          </div>
        </div>

        {/* Diary Title */}
        <h1
          className="text-[28px] font-bold mb-4 leading-tight"
          style={{ fontFamily: 'var(--font-heading)' }}
        >
          {diaryReport?.title || '美好的一天'}
        </h1>

        {/* Diary Body */}
        <div className="space-y-4 mb-8">
          {diaryReport?.content.split('\n\n').map((paragraph, index) => (
            <p key={index} className="text-[17px] leading-[1.8] text-[#424242]">
              {paragraph}
            </p>
          ))}

          {/* Images */}
          {diaryReport?.images && diaryReport.images.length > 0 && (
            <div className="my-6 space-y-4">
              {diaryReport.images.map((image, index) => (
                <div key={index} className="rounded-xl overflow-hidden">
                  <img
                    src={image}
                    alt={`日记图片 ${index + 1}`}
                    className="w-full h-auto"
                  />
                  <p className="text-xs italic text-[#9E9E9E] mt-2 text-center">
                    照片 {index + 1}
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* Summary */}
          {diaryReport?.summary && (
            <div className="bg-white rounded-xl p-4 mt-6">
              <h3 className="font-semibold mb-2 text-[#424242]">📝 摘要</h3>
              <p className="text-sm text-[#757575] leading-relaxed">
                {diaryReport.summary}
              </p>
            </div>
          )}

          {/* Insights */}
          {diaryReport?.insights && diaryReport.insights.length > 0 && (
            <div className="bg-white rounded-xl p-4 mt-4">
              <h3 className="font-semibold mb-2 text-[#424242]">💡 洞察</h3>
              <ul className="space-y-2">
                {diaryReport.insights.map((insight, index) => (
                  <li key={index} className="text-sm text-[#757575] flex items-start gap-2">
                    <span className="text-[#FFA726]">•</span>
                    {insight}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Metadata Footer */}
        <div className="border-t border-[#E0E0E0] pt-4">
          <p className="text-xs text-[#9E9E9E]">
            生成于 {diaryReport?.created_at ?
              new Date(diaryReport.created_at).toLocaleString('zh-CN') :
              new Date().toLocaleString('zh-CN')
            }
          </p>
          <p className="text-xs text-[#9E9E9E]">
            共 {diaryReport?.content.length || 0} 字
          </p>
        </div>
      </div>

      {/* Bottom Action Bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-[#E0E0E0] shadow-lg">
        <div className="flex items-center justify-around h-16 max-w-md mx-auto px-6">
          <button
            className="flex flex-col items-center gap-1"
            onClick={onEdit}
          >
            <Edit className="w-6 h-6 text-[#757575]" />
            <span className="text-xs text-[#757575]">编辑</span>
          </button>
          <button 
            className="flex flex-col items-center gap-1"
            onClick={() => setShowPublishModal(true)}
          >
            <Upload className="w-6 h-6 text-[#757575]" />
            <span className="text-xs text-[#757575]">发布</span>
          </button>
          <button
            className="flex flex-col items-center gap-1"
            onClick={handleSave}
          >
            <Bookmark
              className={`w-6 h-6 ${isSaved ? "fill-[#FFA726] text-[#FFA726]" : "text-[#757575]"}`}
            />
            <span className={`text-xs ${isSaved ? "text-[#FFA726]" : "text-[#757575]"}`}>
              {isSaved ? "已保存" : "保存"}
            </span>
          </button>
          <button
            className="flex flex-col items-center gap-1"
            onClick={() => setIsLiked(!isLiked)}
          >
            <Heart
              className={`w-6 h-6 ${isLiked ? "fill-[#FFA726] text-[#FFA726]" : "text-[#757575]"}`}
            />
            <span className={`text-xs ${isLiked ? "text-[#FFA726]" : "text-[#757575]"}`}>
              喜欢
            </span>
          </button>
        </div>
      </div>

      {/* Publish Settings Modal */}
      {showPublishModal && (
        <PublishSettingsModal
          diaryTitle="阳光下的周末野餐时光"
          onClose={() => setShowPublishModal(false)}
          onPublish={handlePublish}
        />
      )}
    </div>
  );
}
