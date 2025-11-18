import { Calendar, Heart } from "lucide-react";
import { Card } from "./ui/card";
import { Badge } from "./ui/badge";

interface DiaryCardProps {
  title: string;
  preview: string;
  date: string;
  thumbnail?: string;
  emotions: { label: string; color: string }[];
  isFavorite?: boolean;
  onClick?: () => void;
}

export function DiaryCard({
  title,
  preview,
  date,
  thumbnail,
  emotions,
  isFavorite,
  onClick,
}: DiaryCardProps) {
  return (
    <Card
      className="overflow-hidden cursor-pointer transition-all duration-300 hover:shadow-lg hover:-translate-y-1 bg-white border-[#F1F5F9]"
      onClick={onClick}
    >
      <div className="flex gap-4 p-4">
        {thumbnail && (
          <div className="flex-shrink-0">
            <div
              className="w-[120px] h-[120px] rounded-lg bg-cover bg-center"
              style={{ backgroundImage: `url(${thumbnail})` }}
            />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-2">
            <h3 className="truncate">{title}</h3>
            {isFavorite && <Heart className="w-5 h-5 fill-[#E94E77] text-[#E94E77] flex-shrink-0" />}
          </div>
          <p className="text-[#64748B] line-clamp-3 mb-3">{preview}</p>
          <div className="flex items-center gap-2 flex-wrap">
            <div className="flex items-center gap-1 caption">
              <Calendar className="w-4 h-4" />
              <span>{date}</span>
            </div>
            {emotions.map((emotion, index) => (
              <Badge
                key={index}
                className="rounded-full"
                style={{ backgroundColor: emotion.color, color: "#fff" }}
              >
                {emotion.label}
              </Badge>
            ))}
          </div>
        </div>
      </div>
    </Card>
  );
}
