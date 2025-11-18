import { useState, useRef, useEffect } from "react";
import { ArrowLeft, Camera, RotateCw, Check, X } from "lucide-react";
import { Button } from "./ui/button";
import { toast } from "sonner@2.0.3";

interface CameraScreenProps {
  onBack: () => void;
  onCapture: (file: File) => void;
}

export function CameraScreen({ onBack, onCapture }: CameraScreenProps) {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [facingMode, setFacingMode] = useState<"user" | "environment">("environment");
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    startCamera();
    return () => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [facingMode]);

  const startCamera = async () => {
    try {
      // 检查是否支持相机
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        toast.error("您的浏览器不支持相机功能");
        return;
      }

      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: facingMode },
        audio: false,
      });
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (error) {
      console.error("Error accessing camera:", error);
      toast.error("无法访问相机，请检查权限设置或使用文件上传功能");
      // 3秒后自动返回
      setTimeout(() => {
        onBack();
      }, 3000);
    }
  };

  const handleCapture = () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext("2d");

    if (!context) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    const imageDataUrl = canvas.toDataURL("image/jpeg", 0.9);
    setCapturedImage(imageDataUrl);

    // 停止摄像头
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
    }
  };

  const handleRetake = () => {
    setCapturedImage(null);
    startCamera();
  };

  const handleConfirm = () => {
    if (!capturedImage) return;

    // 将 data URL 转换为 File 对象
    fetch(capturedImage)
      .then((res) => res.blob())
      .then((blob) => {
        const file = new File([blob], `photo_${Date.now()}.jpg`, {
          type: "image/jpeg",
        });
        onCapture(file);
      });
  };

  const handleFlipCamera = () => {
    setFacingMode((prev) => (prev === "user" ? "environment" : "user"));
  };

  return (
    <div className="min-h-screen bg-black flex flex-col">
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 z-10 bg-gradient-to-b from-black/50 to-transparent">
        <div className="flex items-center justify-between p-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={onBack}
            className="text-white hover:bg-white/20"
          >
            <ArrowLeft className="w-6 h-6" />
          </Button>
          {!capturedImage && (
            <Button
              variant="ghost"
              size="icon"
              onClick={handleFlipCamera}
              className="text-white hover:bg-white/20"
            >
              <RotateCw className="w-6 h-6" />
            </Button>
          )}
        </div>
      </div>

      {/* Camera View / Preview */}
      <div className="flex-1 flex items-center justify-center relative">
        {capturedImage ? (
          <img
            src={capturedImage}
            alt="Captured"
            className="max-w-full max-h-full object-contain"
          />
        ) : (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            className="max-w-full max-h-full object-contain"
          />
        )}
        <canvas ref={canvasRef} className="hidden" />
      </div>

      {/* Bottom Controls */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/50 to-transparent pb-8 pt-12">
        <div className="flex items-center justify-center gap-12">
          {capturedImage ? (
            <>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleRetake}
                className="w-16 h-16 rounded-full bg-white/20 hover:bg-white/30 text-white"
              >
                <X className="w-8 h-8" />
              </Button>
              <Button
                size="icon"
                onClick={handleConfirm}
                className="w-20 h-20 rounded-full bg-[#FFA726] hover:bg-[#FF9800] text-white"
              >
                <Check className="w-10 h-10" />
              </Button>
            </>
          ) : (
            <Button
              size="icon"
              onClick={handleCapture}
              className="w-20 h-20 rounded-full bg-white hover:bg-white/90 border-4 border-[#FFA726]"
            >
              <Camera className="w-10 h-10 text-[#FFA726]" />
            </Button>
          )}
        </div>

        {!capturedImage && (
          <p className="text-center text-white text-sm mt-6">
            点击按钮拍摄照片
          </p>
        )}
      </div>
    </div>
  );
}
