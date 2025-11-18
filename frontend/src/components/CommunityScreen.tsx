import { useState, useMemo } from "react";
import { Heart, MessageCircle, Share2, MoreHorizontal, MapPin, TrendingUp, Users } from "lucide-react";
import { TabBar } from "./TabBar";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Avatar } from "./ui/avatar";
import { EmptyState } from "./EmptyState";

interface CommunityScreenProps {
  onNavigate: (page: string, data?: any) => void;
  onTabChange: (tab: string) => void;
}

export function CommunityScreen({ onNavigate, onTabChange }: CommunityScreenProps) {
  const [selectedFilter, setSelectedFilter] = useState("all");
  const [followingUsers] = useState([2, 5]); // IDs of users we follow

  const filters = [
    { id: "all", label: "全部" },
    { id: "following", label: "关注" },
    { id: "trending", label: "热门" },
    { id: "nearby", label: "附近" },
  ];

  const communityPosts = [
    {
      id: 1,
      userId: 1,
      user: {
        name: "林小雨",
        avatar: "https://i.pravatar.cc/150?img=1",
        location: "上海·浦东",
      },
      diary: {
        title: "海边的日落，心中的宁静",
        content: "今天来到海边，看着夕阳慢慢落下，海浪轻轻拍打着沙滩。这一刻，所有的烦恼都随风而去...",
        image: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800",
        emotions: ["平静", "治愈"],
        visibility: "公开",
      },
      stats: {
        likes: 128,
        comments: 23,
        shares: 5,
      },
      isLiked: false,
      timeAgo: "2小时前",
      distance: "1.2km",
      isTrending: false,
    },
    {
      id: 2,
      userId: 2,
      user: {
        name: "张晨曦",
        avatar: "https://i.pravatar.cc/150?img=5",
        location: "北京·朝阳",
      },
      diary: {
        title: "咖啡馆里的温暖午后",
        content: "找到了一家很有氛围的咖啡馆，阳光透过玻璃窗洒在桌上，手中的拿铁还冒着热气，翻开喜欢的书...",
        image: "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=800",
        emotions: ["惬意", "文艺"],
        visibility: "好友可见",
      },
      stats: {
        likes: 89,
        comments: 12,
        shares: 3,
      },
      isLiked: true,
      timeAgo: "5小时前",
      distance: "15.3km",
      isTrending: false,
    },
    {
      id: 3,
      userId: 3,
      user: {
        name: "王悦然",
        avatar: "https://i.pravatar.cc/150?img=9",
        location: "广州·天河",
      },
      diary: {
        title: "和朋友们的聚会时光",
        content: "好久不见的朋友们终于聚在一起，大家有说有笑，回忆起过去的点点滴滴，笑声充满了整个房间...",
        image: "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=800",
        emotions: ["快乐", "怀念"],
        visibility: "公开",
      },
      stats: {
        likes: 534,
        comments: 145,
        shares: 42,
      },
      isLiked: false,
      timeAgo: "1天前",
      distance: "852km",
      isTrending: true,
    },
    {
      id: 4,
      userId: 4,
      user: {
        name: "李思远",
        avatar: "https://i.pravatar.cc/150?img=12",
        location: "上海·静安",
      },
      diary: {
        title: "早晨的公园跑步",
        content: "清晨的空气格外清新，沿着公园的小路慢跑，看着晨练的人们，感受城市苏醒的美好...",
        image: "https://images.unsplash.com/photo-1476480862126-209bfaa8edc8?w=800",
        emotions: ["活力", "自由"],
        visibility: "公开",
      },
      stats: {
        likes: 45,
        comments: 8,
        shares: 2,
      },
      isLiked: false,
      timeAgo: "3小时前",
      distance: "0.8km",
      isTrending: false,
    },
    {
      id: 5,
      userId: 5,
      user: {
        name: "陈梦琪",
        avatar: "https://i.pravatar.cc/150?img=16",
        location: "深圳·南山",
      },
      diary: {
        title: "雨后的城市，格外清新",
        content: "刚下完雨，街道被洗得干干净净，空气中弥漫着泥土的芬芳。撑着伞漫步在街头，感受雨后的宁静...",
        image: "https://images.unsplash.com/photo-1428908728789-d2de25dbd4e2?w=800",
        emotions: ["宁静", "清新"],
        visibility: "公开",
      },
      stats: {
        likes: 678,
        comments: 89,
        shares: 23,
      },
      isLiked: false,
      timeAgo: "6小时前",
      distance: "1205km",
      isTrending: true,
    },
    {
      id: 6,
      userId: 2,
      user: {
        name: "张晨曦",
        avatar: "https://i.pravatar.cc/150?img=5",
        location: "北京·朝阳",
      },
      diary: {
        title: "周末的手工时光",
        content: "终于有时间做自己喜欢的事情了，今天做了一个陶艺作品，虽然还不够完美，但很享受这个过程...",
        image: "https://images.unsplash.com/photo-1513467535987-fd81bc7d62f8?w=800",
        emotions: ["专注", "满足"],
        visibility: "公开",
      },
      stats: {
        likes: 156,
        comments: 34,
        shares: 8,
      },
      isLiked: true,
      timeAgo: "1天前",
      distance: "15.3km",
      isTrending: false,
    },
    {
      id: 7,
      userId: 6,
      user: {
        name: "赵婉儿",
        avatar: "https://i.pravatar.cc/150?img=20",
        location: "上海·徐汇",
      },
      diary: {
        title: "美术馆的艺术之旅",
        content: "今天去了新开的美术馆，看到了很多震撼的艺术作品。艺术真的能触动人心，让人思考很多...",
        image: "https://images.unsplash.com/photo-1499781350541-7783f6c6a0c8?w=800",
        emotions: ["震撼", "思考"],
        visibility: "公开",
      },
      stats: {
        likes: 892,
        comments: 167,
        shares: 56,
      },
      isLiked: false,
      timeAgo: "12小时前",
      distance: "3.5km",
      isTrending: true,
    },
    {
      id: 8,
      userId: 5,
      user: {
        name: "陈梦琪",
        avatar: "https://i.pravatar.cc/150?img=16",
        location: "深圳·南山",
      },
      diary: {
        title: "深夜的读书时光",
        content: "夜深人静，泡一杯茶，翻开心爱的书。这样的时光总是让人感到特别充实和宁静...",
        image: "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=800",
        emotions: ["宁静", "充实"],
        visibility: "公开",
      },
      stats: {
        likes: 234,
        comments: 45,
        shares: 12,
      },
      isLiked: false,
      timeAgo: "2天前",
      distance: "1205km",
      isTrending: false,
    },
  ];

  const [posts, setPosts] = useState(communityPosts);

  // Filter posts based on selected filter
  const filteredPosts = useMemo(() => {
    switch (selectedFilter) {
      case "following":
        // Only show posts from users we follow
        return posts.filter((post) => followingUsers.includes(post.userId));
      case "trending":
        // Show trending posts (high engagement or marked as trending)
        return posts
          .filter((post) => post.isTrending || post.stats.likes > 200)
          .sort((a, b) => b.stats.likes - a.stats.likes);
      case "nearby":
        // Show nearby posts (sorted by distance)
        return posts
          .filter((post) => parseFloat(post.distance) < 100) // Within 100km
          .sort((a, b) => parseFloat(a.distance) - parseFloat(b.distance));
      case "all":
      default:
        // Show all posts, sorted by time (most recent first)
        return posts;
    }
  }, [selectedFilter, posts, followingUsers]);

  const handleLike = (postId: number) => {
    setPosts(
      posts.map((post) =>
        post.id === postId
          ? {
              ...post,
              isLiked: !post.isLiked,
              stats: {
                ...post.stats,
                likes: post.isLiked ? post.stats.likes - 1 : post.stats.likes + 1,
              },
            }
          : post
      )
    );
  };

  const getFilterIcon = (filterId: string) => {
    switch (filterId) {
      case "following":
        return <Users className="w-4 h-4 mr-1" />;
      case "trending":
        return <TrendingUp className="w-4 h-4 mr-1" />;
      case "nearby":
        return <MapPin className="w-4 h-4 mr-1" />;
      default:
        return null;
    }
  };

  const getEmptyStateConfig = () => {
    switch (selectedFilter) {
      case "following":
        return {
          icon: "👥",
          title: "还没有关注的人",
          description: "去发现页面关注一些有趣的用户吧",
        };
      case "trending":
        return {
          icon: "🔥",
          title: "暂无热门内容",
          description: "成为第一个创造热门内容的人",
        };
      case "nearby":
        return {
          icon: "📍",
          title: "附近暂无动态",
          description: "扩大搜索范围或稍后再试",
        };
      default:
        return {
          icon: "📝",
          title: "暂无内容",
          description: "开始记录你的生活故事吧",
        };
    }
  };

  return (
    <div className="min-h-screen bg-[#FAF3E0] pb-24">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-white border-b border-[#E0E0E0]">
        <div className="p-6">
          <h1
            className="text-[24px] font-bold mb-4"
            style={{ fontFamily: "var(--font-heading)" }}
          >
            发现
          </h1>

          {/* Filter Tabs */}
          <div className="flex gap-3 overflow-x-auto pb-1">
            {filters.map((filter) => (
              <button
                key={filter.id}
                onClick={() => setSelectedFilter(filter.id)}
                className={`px-4 py-2 rounded-full whitespace-nowrap transition-all flex items-center ${
                  selectedFilter === filter.id
                    ? "bg-[#FFA726] text-white shadow-md"
                    : "bg-[#F5F5DC] text-[#757575] hover:bg-[#E8DCC0]"
                }`}
              >
                {getFilterIcon(filter.id)}
                {filter.label}
                {filter.id === "following" && followingUsers.length > 0 && (
                  <span className="ml-2 px-1.5 py-0.5 bg-white/30 rounded-full text-xs">
                    {followingUsers.length}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Filter Info Banner */}
      {selectedFilter !== "all" && (
        <div className="px-6 pt-4">
          <div className="bg-white rounded-xl p-3 flex items-center gap-3 shadow-sm">
            {selectedFilter === "following" && (
              <>
                <Users className="w-5 h-5 text-[#FFA726]" />
                <div className="flex-1">
                  <p className="text-sm font-semibold">
                    关注的人 ({followingUsers.length})
                  </p>
                  <p className="text-xs text-[#9E9E9E]">
                    查看你关注的用户动态
                  </p>
                </div>
              </>
            )}
            {selectedFilter === "trending" && (
              <>
                <TrendingUp className="w-5 h-5 text-[#FFA726]" />
                <div className="flex-1">
                  <p className="text-sm font-semibold">热门内容</p>
                  <p className="text-xs text-[#9E9E9E]">
                    根据点赞和互动量排序
                  </p>
                </div>
              </>
            )}
            {selectedFilter === "nearby" && (
              <>
                <MapPin className="w-5 h-5 text-[#FFA726]" />
                <div className="flex-1">
                  <p className="text-sm font-semibold">附近的动态</p>
                  <p className="text-xs text-[#9E9E9E]">
                    距离你100km以内的内容
                  </p>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Community Feed */}
      <div className="space-y-4 p-6">
        {filteredPosts.length === 0 ? (
          <div className="mt-12">
            <EmptyState {...getEmptyStateConfig()} />
          </div>
        ) : (
          filteredPosts.map((post) => (
          <div key={post.id} className="bg-white rounded-2xl shadow-sm overflow-hidden">
            {/* Trending Badge */}
            {post.isTrending && selectedFilter !== "trending" && (
              <div className="bg-gradient-to-r from-[#FFA726] to-[#FFB74D] px-4 py-2">
                <div className="flex items-center gap-2 text-white text-sm font-semibold">
                  <TrendingUp className="w-4 h-4" />
                  <span>热门内容</span>
                </div>
              </div>
            )}

            {/* User Header */}
            <div className="flex items-center justify-between p-4">
              <button
                onClick={() => onNavigate("user-profile", { userId: post.id })}
                className="flex items-center gap-3 flex-1"
              >
                <div className="w-10 h-10 rounded-full overflow-hidden bg-gradient-to-br from-[#FFA726] to-[#FFB74D]">
                  <img
                    src={post.user.avatar}
                    alt={post.user.name}
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="text-left flex-1">
                  <div className="flex items-center gap-2">
                    <p className="font-semibold text-[14px]">{post.user.name}</p>
                    {followingUsers.includes(post.userId) && (
                      <Badge className="bg-[#FFA726]/20 text-[#FFA726] text-xs px-1.5 py-0">
                        已关注
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-[#9E9E9E]">
                    <span>{post.timeAgo}</span>
                    {selectedFilter === "nearby" && (
                      <>
                        <span>•</span>
                        <MapPin className="w-3 h-3 inline" />
                        <span>{post.distance}</span>
                      </>
                    )}
                  </div>
                </div>
              </button>
              <Button variant="ghost" size="icon">
                <MoreHorizontal className="w-5 h-5 text-[#757575]" />
              </Button>
            </div>

            {/* Diary Content */}
            <button
              onClick={() => onNavigate("community-diary-detail", { postId: post.id })}
              className="w-full text-left"
            >
              {/* Image */}
              {post.diary.image && (
                <div className="w-full aspect-[4/3] overflow-hidden">
                  <img
                    src={post.diary.image}
                    alt={post.diary.title}
                    className="w-full h-full object-cover"
                  />
                </div>
              )}

              {/* Text Content */}
              <div className="p-4">
                <h3
                  className="text-[18px] font-bold mb-2"
                  style={{ fontFamily: "var(--font-heading)" }}
                >
                  {post.diary.title}
                </h3>
                <p className="text-[15px] text-[#757575] line-clamp-3 mb-3 leading-relaxed">
                  {post.diary.content}
                </p>
                <div className="flex gap-2">
                  {post.diary.emotions.map((emotion, index) => (
                    <Badge
                      key={index}
                      className="bg-[#FFA726]/20 text-[#FFA726] hover:bg-[#FFA726]/30"
                    >
                      {emotion}
                    </Badge>
                  ))}
                </div>
              </div>
            </button>

            {/* Action Bar */}
            <div className="flex items-center justify-between px-4 pb-4 pt-2 border-t border-[#E0E0E0]">
              <button
                onClick={() => handleLike(post.id)}
                className="flex items-center gap-2 group"
              >
                <Heart
                  className={`w-6 h-6 transition-all ${
                    post.isLiked
                      ? "fill-[#FFA726] text-[#FFA726]"
                      : "text-[#757575] group-hover:text-[#FFA726]"
                  }`}
                />
                <span
                  className={`text-sm ${
                    post.isLiked ? "text-[#FFA726]" : "text-[#757575]"
                  }`}
                >
                  {post.stats.likes}
                </span>
              </button>

              <button
                onClick={() =>
                  onNavigate("community-diary-detail", { postId: post.id })
                }
                className="flex items-center gap-2 group"
              >
                <MessageCircle className="w-6 h-6 text-[#757575] group-hover:text-[#FFA726]" />
                <span className="text-sm text-[#757575]">
                  {post.stats.comments}
                </span>
              </button>

              <button className="flex items-center gap-2 group">
                <Share2 className="w-6 h-6 text-[#757575] group-hover:text-[#FFA726]" />
                <span className="text-sm text-[#757575]">{post.stats.shares}</span>
              </button>
            </div>
          </div>
          ))
        )}

        {/* Load More Button */}
        {filteredPosts.length > 0 && (
          <div className="pt-4">
            <Button
              variant="outline"
              className="w-full h-12 border-2 border-dashed border-[#E0E0E0] text-[#757575] hover:bg-[#FAF3E0] hover:border-[#FFA726] hover:text-[#FFA726]"
            >
              加载更多内容
            </Button>
          </div>
        )}
      </div>

      {/* Tab Bar */}
      <TabBar activeTab="community" onTabChange={onTabChange} />
    </div>
  );
}
