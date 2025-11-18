import { useState, useEffect } from "react";
import { WelcomeScreen } from "./components/WelcomeScreen";
import { OnboardingCarousel } from "./components/OnboardingCarousel";
import { PermissionsScreen } from "./components/PermissionsScreen";
import { PersonalizationScreen } from "./components/PersonalizationScreen";
import { HomeScreen } from "./components/HomeScreen";
import { ProcessingScreen } from "./components/ProcessingScreen";
import { DiaryDetailScreen } from "./components/DiaryDetailScreen";
import { DiaryListScreen } from "./components/DiaryListScreen";
import { MemoriesScreen } from "./components/MemoriesScreen";
import { ProfileScreen } from "./components/ProfileScreen";
import { CommunityScreen } from "./components/CommunityScreen";
import { UserProfileScreen } from "./components/UserProfileScreen";
import { CommunityDiaryDetailScreen } from "./components/CommunityDiaryDetailScreen";
import { FileUploadScreen } from "./components/FileUploadScreen";
import { CameraScreen } from "./components/CameraScreen";
import { DiaryEditScreen } from "./components/DiaryEditScreen";
import { DiaryStyleSettingScreen } from "./components/DiaryStyleSettingScreen";
import { DiaryLengthSettingScreen } from "./components/DiaryLengthSettingScreen";
import { NotificationSettingScreen } from "./components/NotificationSettingScreen";
import { PrivacySettingScreen } from "./components/PrivacySettingScreen";
import { ExportDiariesScreen } from "./components/ExportDiariesScreen";
import { QuickNav } from "./components/QuickNav";
import { Toaster } from "./components/ui/sonner";
import { glassApi } from "./services/glassApi";
import { toast } from "sonner";

type Page =
  | "welcome"
  | "onboarding"
  | "permissions"
  | "personalization"
  | "home"
  | "upload"
  | "file-upload-photo"
  | "file-upload-video"
  | "camera"
  | "processing"
  | "diary-detail"
  | "diary-edit"
  | "diary-list"
  | "memories"
  | "profile"
  | "diary-style-setting"
  | "diary-length-setting"
  | "notification-setting"
  | "privacy-setting"
  | "export-diaries"
  | "community"
  | "user-profile"
  | "community-diary-detail";

// Application state for Glass backend integration
interface AppState {
  isBackendAvailable: boolean;
  currentTaskId: string | null;
  currentTimelineId: string | null;
  processingError: string | null;
  backgroundTasks: Array<{ id: string; fileName: string; startTime: Date }>;
}

export default function App() {
  const [currentPage, setCurrentPage] = useState<Page>("welcome");
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [appState, setAppState] = useState<AppState>(() => {
    // Load background tasks from localStorage if available
    const savedTasks = localStorage.getItem('backgroundTasks');
    try {
      const parsedTasks = savedTasks ? JSON.parse(savedTasks) : [];
      // Convert date strings back to Date objects
      const tasksWithDates = parsedTasks.map((task: any) => ({
        ...task,
        startTime: new Date(task.startTime)
      }));
      return {
        isBackendAvailable: false,
        currentTaskId: null,
        currentTimelineId: null,
        processingError: null,
        backgroundTasks: tasksWithDates,
      };
    } catch {
      return {
        isBackendAvailable: false,
        currentTaskId: null,
        currentTimelineId: null,
        processingError: null,
        backgroundTasks: [],
      };
    }
  });

  // Check backend availability on component mount with progressive checking
  useEffect(() => {
    const checkBackend = async () => {
      // Delay initial check to allow backend to start
      const checkWithDelay = async (delay = 2000, maxRetries = 3) => {
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
          await new Promise(resolve => setTimeout(resolve, delay));

          try {
            console.log(`Backend check attempt ${attempt}/${maxRetries}...`);
            const backendAvailable = await glassApi.isBackendAvailable();
            setAppState(prev => ({
              ...prev,
              isBackendAvailable: backendAvailable,
              processingError: backendAvailable ? null : "Glass backend service is not available"
            }));

            if (backendAvailable) {
              console.log("Backend is available!");
              return;
            }
          } catch (error) {
            console.log(`Backend check attempt ${attempt} failed:`, error);
          }
        }

        // If all retries failed, show warning but don't break the app
        console.warn("Backend not available after all retries, using demo mode");
        setAppState(prev => ({
          ...prev,
          isBackendAvailable: false,
          processingError: null // Don't show error on initial load
        }));
      };

      checkWithDelay();
    };

    checkBackend();

    // Request notification permission for background processing
    if ("Notification" in window && Notification.permission === "default") {
      Notification.requestPermission().then(permission => {
        if (permission === "granted") {
          console.log("System notification permission granted");
        }
      });
    }

    // Resume monitoring for existing background tasks
    if (appState.backgroundTasks.length > 0) {
      appState.backgroundTasks.forEach(task => {
        startBackgroundMonitoring(task.id, task.fileName);
      });
    }
  }, []);

  // Save background tasks to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('backgroundTasks', JSON.stringify(appState.backgroundTasks));
  }, [appState.backgroundTasks]);

  // 为演示创建虚拟文件
  const createDemoFiles = () => {
    // 创建一个简单的演示文件对象
    const demoFile = new File([""], "demo_photo.jpg", { type: "image/jpeg" });
    return [demoFile, demoFile, demoFile];
  };

  const handleWelcomeStart = () => {
    setCurrentPage("onboarding");
  };

  const handleOnboardingComplete = () => {
    setCurrentPage("permissions");
  };

  const handleOnboardingSkip = () => {
    setCurrentPage("permissions");
  };

  const handlePermissionsGrant = () => {
    setCurrentPage("personalization");
  };

  const handlePermissionsSkip = () => {
    setCurrentPage("personalization");
  };

  const handlePersonalizationComplete = () => {
    setCurrentPage("home");
  };

  const handleNavigate = (page: string) => {
    // 如果导航到处理页面但没有文件，创建演示文件
    if (page === "processing" && uploadedFiles.length === 0) {
      setUploadedFiles(createDemoFiles());
    }
    setCurrentPage(page as Page);
  };

  const handleTabChange = (tab: string) => {
    const tabPageMap: Record<string, Page> = {
      home: "home",
      community: "community",
      diary: "diary-list",
      profile: "profile",
    };
    setCurrentPage(tabPageMap[tab] || "home");
  };

  const handleFileUpload = async (files: File[], taskId?: string) => {
    setUploadedFiles(files);

    if (!appState.isBackendAvailable) {
      toast.error("Backend service is not available. Some features may be limited.");
      setCurrentPage("processing");
      return;
    }

    try {
      const file = files[0];
      if (file) {
        // If taskId is provided (from video upload), use it
        if (taskId) {
          setAppState(prev => ({
            ...prev,
            currentTaskId: taskId,
            processingError: null,
          }));
          toast.success("文件上传成功，开始处理...");
        } else {
          // For image files or when no taskId provided
          if (file.type.startsWith('video/')) {
            const response = await glassApi.uploadVideo(file);
            setAppState(prev => ({
              ...prev,
              currentTaskId: response.task_id,
              processingError: null,
            }));
            toast.success("视频上传成功!");
          } else {
            toast.info(`开始处理 ${file.name}...`);
          }
        }
      }

      setCurrentPage("processing");
    } catch (error) {
      console.error("File upload failed:", error);
      toast.error(`Failed to process file: ${error}`);
      setAppState(prev => ({
        ...prev,
        processingError: `Upload failed: ${error}`
      }));
    }
  };

  const handleCameraCapture = async (file: File) => {
    setUploadedFiles([file]);

    if (!appState.isBackendAvailable) {
      toast.error("Backend service is not available. Please check your connection.");
      return;
    }

    try {
      toast.info(`Processing captured image...`);
      setCurrentPage("processing");
    } catch (error) {
      console.error("Camera capture failed:", error);
      toast.error(`Failed to process capture: ${error}`);
    }
  };

  const handleProcessingComplete = () => {
    // Use the real timeline ID from backend upload response
    if (appState.currentTaskId) {
      setAppState(prev => ({
        ...prev,
        currentTimelineId: appState.currentTaskId, // Use real timeline ID from upload response
      }));
    }
    setCurrentPage("diary-detail");
  };

  const handleProcessingCancel = () => {
    setAppState(prev => ({
      ...prev,
      currentTaskId: null,
      processingError: null,
    }));
    setCurrentPage("home");
    setUploadedFiles([]);
  };

  // Background processing handlers
  const handleBackgroundProcess = (taskId: string) => {
    if (!taskId || !uploadedFiles.length) return;

    // Add to background tasks
    const backgroundTask = {
      id: taskId,
      fileName: uploadedFiles[0].name,
      startTime: new Date(),
    };

    setAppState(prev => ({
      ...prev,
      backgroundTasks: [...prev.backgroundTasks, backgroundTask],
      currentTaskId: null, // Clear current task
    }));

    // Start background monitoring
    startBackgroundMonitoring(taskId, backgroundTask.fileName);

    // Go back to home
    setCurrentPage("home");
    setUploadedFiles([]);
  };

  // Monitor background tasks and notify when complete
  const startBackgroundMonitoring = (taskId: string, fileName: string) => {
    const checkStatus = async () => {
      try {
        const status = await glassApi.getProcessingStatus(taskId);

        if (status.status === 'ready' || status.status === 'completed') {
          // Task completed - show notification
          showCompletionNotification(taskId, fileName);

          // Remove from background tasks
          setAppState(prev => ({
            ...prev,
            backgroundTasks: prev.backgroundTasks.filter(task => task.id !== taskId),
          }));

          return; // Stop monitoring
        }

        if (status.status === 'failed') {
          // Task failed
          toast.error(`视频处理失败: ${fileName}`);
          setAppState(prev => ({
            ...prev,
            backgroundTasks: prev.backgroundTasks.filter(task => task.id !== taskId),
          }));
          return;
        }

        // Handle intermediate states (processing, finalizing)
        if (status.status === 'processing' || status.status === 'finalizing' || status.status === 'pending') {
          // Task is still running, continue monitoring
          console.log(`🔄 Background task ${taskId} status: ${status.status} (${status.progress}%)`);
        } else {
          // Unknown status - log and continue
          console.warn(`⚠️ Unknown status for background task ${taskId}: ${status.status}`);
        }

        // Continue monitoring
        setTimeout(checkStatus, 5000); // Check every 5 seconds

      } catch (error) {
        console.error('Background task monitoring failed:', error);
        toast.error(`后台任务检查失败: ${fileName}`);
      }
    };

    // Start checking after a delay
    setTimeout(checkStatus, 3000);
  };

  // Show completion notification
  const showCompletionNotification = (taskId: string, fileName: string) => {
    // Show in-app notification
    toast.success(`🎉 视频处理完成: ${fileName}`, {
      duration: 5000,
      action: {
        label: "查看",
        onClick: () => {
          // Set as current timeline and navigate to detail
          setAppState(prev => ({
            ...prev,
            currentTimelineId: taskId,
          }));
          setCurrentPage("diary-detail");
        },
      },
    });

    // Request system notification if available
    if ("Notification" in window && Notification.permission === "granted") {
      new Notification("MineContext - 视频处理完成", {
        body: `您的视频 "${fileName}" 已处理完成，点击查看结果`,
        icon: "/icon-192x192.png",
        tag: taskId,
      });
    }
  };

  return (
    <div className="min-h-screen max-w-md mx-auto relative bg-[#FAF3E0]">
      <QuickNav onNavigate={handleNavigate} />

      {/* Background Tasks Indicator */}
      {appState.backgroundTasks.length > 0 && (
        <div className="fixed top-16 right-4 z-50 bg-[#FFA726] text-white px-3 py-2 rounded-full shadow-lg flex items-center gap-2 animate-pulse">
          <div className="w-2 h-2 bg-white rounded-full animate-ping"></div>
          <span className="text-sm font-medium">
            {appState.backgroundTasks.length} 个后台任务处理中
          </span>
        </div>
      )}
      {currentPage === "welcome" && (
        <WelcomeScreen onStart={handleWelcomeStart} />
      )}
      {currentPage === "onboarding" && (
        <OnboardingCarousel
          onComplete={handleOnboardingComplete}
          onSkip={handleOnboardingSkip}
        />
      )}
      {currentPage === "permissions" && (
        <PermissionsScreen
          onGrant={handlePermissionsGrant}
          onSkip={handlePermissionsSkip}
        />
      )}
      {currentPage === "personalization" && (
        <PersonalizationScreen onComplete={handlePersonalizationComplete} />
      )}
      {currentPage === "home" && (
        <HomeScreen onNavigate={handleNavigate} onTabChange={handleTabChange} />
      )}
      {currentPage === "file-upload-photo" && (
        <FileUploadScreen
          onBack={() => setCurrentPage("home")}
          onUpload={handleFileUpload}
          mode="photo"
        />
      )}
      {currentPage === "file-upload-video" && (
        <FileUploadScreen
          onBack={() => setCurrentPage("home")}
          onUpload={handleFileUpload}
          mode="video"
        />
      )}
      {currentPage === "camera" && (
        <CameraScreen
          onBack={() => setCurrentPage("home")}
          onCapture={handleCameraCapture}
        />
      )}
      {currentPage === "processing" && (
        <ProcessingScreen
          fileName={uploadedFiles[0]?.name || "photo_001.jpg"}
          fileCount={uploadedFiles.length}
          taskId={appState.currentTaskId}
          onComplete={handleProcessingComplete}
          onCancel={handleProcessingCancel}
          onBackgroundProcess={handleBackgroundProcess}
        />
      )}
      {currentPage === "diary-detail" && (
        <DiaryDetailScreen
          onBack={() => setCurrentPage("diary-list")}
          onEdit={() => setCurrentPage("diary-edit")}
          timelineId={appState.currentTimelineId}
        />
      )}
      {currentPage === "diary-edit" && (
        <DiaryEditScreen
          onBack={() => setCurrentPage("diary-detail")}
          onSave={() => setCurrentPage("diary-detail")}
        />
      )}
      {currentPage === "diary-list" && (
        <DiaryListScreen
          onNavigate={handleNavigate}
          onTabChange={handleTabChange}
        />
      )}
      {currentPage === "memories" && (
        <MemoriesScreen
          onNavigate={handleNavigate}
          onTabChange={handleTabChange}
        />
      )}
      {currentPage === "profile" && (
        <ProfileScreen
          onTabChange={handleTabChange}
          onNavigate={handleNavigate}
        />
      )}
      {currentPage === "diary-style-setting" && (
        <DiaryStyleSettingScreen onBack={() => setCurrentPage("profile")} />
      )}
      {currentPage === "diary-length-setting" && (
        <DiaryLengthSettingScreen onBack={() => setCurrentPage("profile")} />
      )}
      {currentPage === "notification-setting" && (
        <NotificationSettingScreen onBack={() => setCurrentPage("profile")} />
      )}
      {currentPage === "privacy-setting" && (
        <PrivacySettingScreen onBack={() => setCurrentPage("profile")} />
      )}
      {currentPage === "export-diaries" && (
        <ExportDiariesScreen onBack={() => setCurrentPage("profile")} />
      )}
      {currentPage === "community" && (
        <CommunityScreen
          onNavigate={handleNavigate}
          onTabChange={handleTabChange}
        />
      )}
      {currentPage === "user-profile" && (
        <UserProfileScreen
          onBack={() => setCurrentPage("community")}
          onNavigate={handleNavigate}
        />
      )}
      {currentPage === "community-diary-detail" && (
        <CommunityDiaryDetailScreen
          onBack={() => setCurrentPage("community")}
          onNavigate={handleNavigate}
        />
      )}
      <Toaster />
    </div>
  );
}
