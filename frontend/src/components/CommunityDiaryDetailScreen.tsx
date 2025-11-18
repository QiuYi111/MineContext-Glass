import { useState } from "react";
import { ArrowLeft, Heart, MessageCircle, Share2, Send } from "lucide-react";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Input } from "./ui/input";
import { ScrollArea } from "./ui/scroll-area";

interface CommunityDiaryDetailScreenProps {
  onBack: () => void;
  onNavigate: (page: string, data?: any) => void;
}

export function CommunityDiaryDetailScreen({
  onBack,
  onNavigate,
}: CommunityDiaryDetailScreenProps) {
  const [isLiked, setIsLiked] = useState(false);
  const [likes, setLikes] = useState(128);
  const [commentText, setCommentText] = useState("");
  const [comments, setComments] = useState([
    {
      id: 1,
      user: {
        name: "王小明",
        avatar: "https://i.pravatar.cc/150?img=12",
      },
      content: "太美了！这个地方我也想去看看",
      likes: 12,
      timeAgo: "1小时前",
      isLiked: false,
    },
    {
      id: 2,
      user: {
        name: "李梦琪",
        avatar: "https://i.pravatar.cc/150?img=23",
      },
      content: "文字写得好棒，很有画面感~",
      likes: 8,
      timeAgo: "2小时前",
      isLiked: true,
    },
    {
      id: 3,
      user: {
        name: "陈浩然",
        avatar: "https://i.pravatar.cc/150?img=33",
      },
      content: "看到你的日记，也想起了我的海边之旅",
      likes: 5,
      timeAgo: "3小时前",
      isLiked: false,
    },
  ]);

  const handleLike = () => {
    setIsLiked(!isLiked);
    setLikes(isLiked ? likes - 1 : likes + 1);
  };

  const handleCommentLike = (commentId: number) => {
    setComments(
      comments.map((comment) =>
        comment.id === commentId
          ? {
              ...comment,
              isLiked: !comment.isLiked,
              likes: comment.isLiked ? comment.likes - 1 : comment.likes + 1,
            }
          : comment
      )
    );
  };

  const handleSendComment = () => {
    if (commentText.trim()) {
      const newComment = {
        id: comments.length + 1,
        user: {
          name: "小明",
          avatar: "https://i.pravatar.cc/150?img=50",
        },
        content: commentText,
        likes: 0,
        timeAgo: "刚刚",
        isLiked: false,
      };
      setComments([newComment, ...comments]);
      setCommentText("");
    }
  };

  return (
    <div className="min-h-screen bg-[#FAF3E0] flex flex-col">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-white border-b border-[#E0E0E0]">
        <div className="flex items-center justify-between p-4">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ArrowLeft className="w-6 h-6" />
          </Button>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={handleLike}
              className={isLiked ? "text-[#FFA726]" : ""}
            >
              <Heart
                className={`w-6 h-6 ${isLiked ? "fill-[#FFA726]" : ""}`}
              />
            </Button>
            <Button variant="ghost" size="icon">
              <Share2 className="w-6 h-6" />
            </Button>
          </div>
        </div>
      </div>

      {/* Content */}
      <ScrollArea className="flex-1">
        <div className="pb-24">
          {/* User Info */}
          <div className="bg-white p-4 border-b border-[#E0E0E0]">
            <button
              onClick={() => onNavigate("user-profile", { userId: 1 })}
              className="flex items-center gap-3"
            >
              <div className="w-12 h-12 rounded-full overflow-hidden bg-gradient-to-br from-[#FFA726] to-[#FFB74D]">
                <img
                  src="https://i.pravatar.cc/150?img=1"
                  alt="林小雨"
                  className="w-full h-full object-cover"
                />
              </div>
              <div className="text-left">
                <p className="font-semibold text-[16px]">林小雨</p>
                <p className="text-xs text-[#9E9E9E]">2小时前</p>
              </div>
            </button>
          </div>

          {/* Diary Image */}
          <div className="w-full aspect-[4/3] bg-white">
            <img
              src="https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800"
              alt="Diary"
              className="w-full h-full object-cover"
            />
          </div>

          {/* Stats Bar */}
          <div className="bg-white px-4 py-3 border-b border-[#E0E0E0] flex items-center gap-4 text-sm">
            <span className="text-[#757575]">
              <span className="font-semibold text-[#424242]">{likes}</span> 人喜欢
            </span>
            <span className="text-[#757575]">
              <span className="font-semibold text-[#424242]">
                {comments.length}
              </span>{" "}
              条评论
            </span>
          </div>

          {/* Diary Content */}
          <div className="bg-white p-6">
            <div className="flex gap-2 mb-4">
              <Badge className="bg-[#FFA726]/20 text-[#FFA726] hover:bg-[#FFA726]/30">
                平静
              </Badge>
              <Badge className="bg-[#64B5F6]/20 text-[#64B5F6] hover:bg-[#64B5F6]/30">
                治愈
              </Badge>
            </div>

            <h1
              className="text-[24px] font-bold mb-4"
              style={{ fontFamily: "var(--font-heading)" }}
            >
              海边的日落，心中的宁静
            </h1>

            <div className="space-y-4 text-[17px] leading-[1.8] text-[#424242]">
              <p>
                今天来到海边，看着夕阳慢慢落下，海浪轻轻拍打着沙滩。这一刻，所有的烦恼都随风而去，心中只剩下宁静和感恩。
              </p>
              <p>
                橙红色的晚霞映照在海面上，波光粼粼，美得让人屏息。我坐在沙滩上，感受着海风的温柔，倾听着海浪的低语。
              </p>
              <p>
                生活总是匆匆忙忙，能有这样的时刻停下来，感受大自然的美好，真的很珍贵。希望以后还能有更多这样的时光。
              </p>
            </div>
          </div>

          {/* Comments Section */}
          <div className="bg-white mt-2 p-4">
            <h3 className="font-semibold mb-4">评论 ({comments.length})</h3>
            <div className="space-y-4">
              {comments.map((comment) => (
                <div key={comment.id} className="flex gap-3">
                  <div className="w-9 h-9 rounded-full overflow-hidden bg-gradient-to-br from-[#FFA726] to-[#FFB74D] flex-shrink-0">
                    <img
                      src={comment.user.avatar}
                      alt={comment.user.name}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="flex-1">
                    <div className="bg-[#F5F5DC] rounded-2xl rounded-tl-none px-4 py-3">
                      <p className="font-semibold text-sm mb-1">
                        {comment.user.name}
                      </p>
                      <p className="text-sm text-[#424242]">{comment.content}</p>
                    </div>
                    <div className="flex items-center gap-4 mt-2 text-xs text-[#9E9E9E]">
                      <span>{comment.timeAgo}</span>
                      <button
                        onClick={() => handleCommentLike(comment.id)}
                        className={`flex items-center gap-1 ${
                          comment.isLiked ? "text-[#FFA726]" : ""
                        }`}
                      >
                        <Heart
                          className={`w-3 h-3 ${
                            comment.isLiked ? "fill-[#FFA726]" : ""
                          }`}
                        />
                        {comment.likes > 0 && comment.likes}
                      </button>
                      <button>回复</button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </ScrollArea>

      {/* Comment Input */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-[#E0E0E0] p-4">
        <div className="max-w-md mx-auto flex gap-3">
          <Input
            placeholder="写下你的想法..."
            value={commentText}
            onChange={(e) => setCommentText(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && handleSendComment()}
            className="flex-1 h-10 rounded-full border-[#E0E0E0] bg-[#F5F5DC]"
          />
          <Button
            onClick={handleSendComment}
            disabled={!commentText.trim()}
            className="w-10 h-10 rounded-full bg-[#FFA726] hover:bg-[#FF9800] p-0"
          >
            <Send className="w-5 h-5" />
          </Button>
        </div>
      </div>
    </div>
  );
}
