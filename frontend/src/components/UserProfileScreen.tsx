import { useState } from "react";
import { ArrowLeft, MoreVertical, Calendar, BookOpen, Heart } from "lucide-react";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";

interface UserProfileScreenProps {
  onBack: () => void;
  onNavigate: (page: string, data?: any) => void;
}

export function UserProfileScreen({ onBack, onNavigate }: UserProfileScreenProps) {
  const [isFollowing, setIsFollowing] = useState(false);

  const userData = {
    name: "林小雨",
    avatar: "https://i.pravatar.cc/150?img=1",
    bio: "记录生活的美好瞬间 | 热爱旅行与摄影 📸",
    stats: {
      diaries: 89,
      followers: 1234,
      following: 567,
    },
  };

  const userDiaries = [
    {
      id: 1,
      title: "海边的日落，心中的宁静",
      image: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=400",
      likes: 128,
      comments: 23,
      date: "11月17日",
    },
    {
      id: 2,
      title: "山间徒步的冒险之旅",
      image: "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=400",
      likes: 95,
      comments: 18,
      date: "11月15日",
    },
    {
      id: 3,
      title: "城市夜景的霓虹之美",
      image: "https://images.unsplash.com/photo-1514565131-fce0801e5785?w=400",
      likes: 156,
      comments: 31,
      date: "11月12日",
    },
    {
      id: 4,
      title: "清晨的第一缕阳光",
      image: "https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?w=400",
      likes: 203,
      comments: 42,
      date: "11月10日",
    },
  ];

  return (
    <div className="min-h-screen bg-[#FAF3E0]">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-white border-b border-[#E0E0E0]">
        <div className="flex items-center justify-between p-4">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ArrowLeft className="w-6 h-6" />
          </Button>
          <h2 className="text-[18px] font-semibold">{userData.name}</h2>
          <Button variant="ghost" size="icon">
            <MoreVertical className="w-6 h-6" />
          </Button>
        </div>
      </div>

      {/* Profile Header */}
      <div className="bg-white p-6 border-b border-[#E0E0E0]">
        <div className="flex items-start gap-4 mb-4">
          {/* Avatar */}
          <div className="w-20 h-20 rounded-full overflow-hidden bg-gradient-to-br from-[#FFA726] to-[#FFB74D] flex-shrink-0">
            <img
              src={userData.avatar}
              alt={userData.name}
              className="w-full h-full object-cover"
            />
          </div>

          {/* Stats */}
          <div className="flex-1 grid grid-cols-3 gap-4 pt-2">
            <div className="text-center">
              <div className="text-[20px] font-bold text-[#424242]">
                {userData.stats.diaries}
              </div>
              <div className="text-xs text-[#9E9E9E]">日记</div>
            </div>
            <div className="text-center">
              <div className="text-[20px] font-bold text-[#424242]">
                {userData.stats.followers}
              </div>
              <div className="text-xs text-[#9E9E9E]">粉丝</div>
            </div>
            <div className="text-center">
              <div className="text-[20px] font-bold text-[#424242]">
                {userData.stats.following}
              </div>
              <div className="text-xs text-[#9E9E9E]">关注</div>
            </div>
          </div>
        </div>

        {/* Bio */}
        <p className="text-sm text-[#757575] mb-4 leading-relaxed">
          {userData.bio}
        </p>

        {/* Action Buttons */}
        <div className="flex gap-3">
          <Button
            onClick={() => setIsFollowing(!isFollowing)}
            className={`flex-1 h-10 ${
              isFollowing
                ? "bg-[#F5F5DC] text-[#424242] hover:bg-[#E0E0E0]"
                : "bg-[#FFA726] text-white hover:bg-[#FF9800]"
            }`}
          >
            {isFollowing ? "已关注" : "关注"}
          </Button>
          <Button
            variant="outline"
            className="flex-1 h-10 border-[#E0E0E0]"
          >
            发消息
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="diaries" className="w-full">
        <TabsList className="w-full bg-white border-b border-[#E0E0E0] rounded-none h-12">
          <TabsTrigger
            value="diaries"
            className="flex-1 data-[state=active]:text-[#FFA726] data-[state=active]:border-b-2 data-[state=active]:border-[#FFA726]"
          >
            <BookOpen className="w-4 h-4 mr-2" />
            日记
          </TabsTrigger>
          <TabsTrigger
            value="liked"
            className="flex-1 data-[state=active]:text-[#FFA726] data-[state=active]:border-b-2 data-[state=active]:border-[#FFA726]"
          >
            <Heart className="w-4 h-4 mr-2" />
            喜欢
          </TabsTrigger>
        </TabsList>

        {/* Diaries Grid */}
        <TabsContent value="diaries" className="mt-0">
          <div className="grid grid-cols-2 gap-2 p-4">
            {userDiaries.map((diary) => (
              <button
                key={diary.id}
                onClick={() =>
                  onNavigate("community-diary-detail", { postId: diary.id })
                }
                className="relative aspect-square rounded-xl overflow-hidden group"
              >
                <img
                  src={diary.image}
                  alt={diary.title}
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                  <div className="absolute bottom-0 left-0 right-0 p-3 text-white">
                    <p className="text-xs font-semibold line-clamp-2 mb-1">
                      {diary.title}
                    </p>
                    <div className="flex items-center gap-3 text-xs">
                      <span className="flex items-center gap-1">
                        <Heart className="w-3 h-3" />
                        {diary.likes}
                      </span>
                      <span>{diary.date}</span>
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="liked" className="mt-0">
          <div className="p-8 text-center">
            <div className="w-20 h-20 rounded-full bg-[#E0E0E0]/30 flex items-center justify-center mx-auto mb-4">
              <Heart className="w-10 h-10 text-[#9E9E9E]" />
            </div>
            <p className="text-sm text-[#9E9E9E]">暂无喜欢的内容</p>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
