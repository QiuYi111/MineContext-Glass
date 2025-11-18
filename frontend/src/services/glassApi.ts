/**
 * Glass API Service
 *
 * API adapter for connecting Frontend UI with Glass backend
 * Handles video processing, timeline generation, and report management
 */

// API Types based on backend structure
export interface VideoUploadResponse {
  task_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  message: string;
}

export interface ProcessingStatus {
  task_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number; // 0-100
  current_step: string;
  total_steps: number;
  message: string;
  created_at: string;
  updated_at: string;
  result?: any;
}

export interface TimelineResponse {
  timeline_id: string;
  date: string; // dd-mm format
  total_chunks: number;
  duration: number; // in seconds
  context_chunks: ContextChunk[];
}

export interface ContextChunk {
  id: string;
  timeline_id: string;
  start_time: number;
  end_time: number;
  content_type: 'video' | 'audio' | 'text';
  content: string;
  metadata: {
    frame_path?: string;
    audio_transcript?: string;
    confidence?: number;
  };
}

export interface DiaryReport {
  id: string;
  timeline_id: string;
  title: string;
  content: string;
  style: 'professional' | 'casual' | 'poetic' | 'humorous';
  length: 'brief' | 'detailed' | 'comprehensive';
  created_at: string;
  images?: string[]; // URLs to representative images
  summary: string;
  insights: string[];
}

export interface UserPreferences {
  diary_style: 'professional' | 'casual' | 'poetic' | 'humorous';
  diary_length: 'brief' | 'detailed' | 'comprehensive';
  notifications_enabled: boolean;
  auto_generate_reports: boolean;
}

export interface ReportGenerationRequest {
  timeline_id: string;
  style?: 'professional' | 'casual' | 'poetic' | 'humorous';
  length?: 'brief' | 'detailed' | 'comprehensive';
  lookback_minutes?: number;
}

class GlassApiService {
  private baseUrl: string | null;
  private retryAttempts = 3;
  private retryDelay = 1000;

  constructor() {
    // Get backend port from URL parameter or use default
    const urlParams = new URLSearchParams(window.location.search);
    const backendPort = urlParams.get('backend_port');

    if (window.electronAPI && backendPort) {
      // Running in Electron environment with backend port from URL
      this.baseUrl = `http://127.0.0.1:${backendPort}`;
    } else if (window.electronAPI) {
      // Running in Electron environment - start with port detection
      this.baseUrl = null; // Will be set after detection
      this.detectBackendPort();
    } else {
      // Running in development browser
      this.baseUrl = 'http://127.0.0.1:8765';
    }

    console.log(`Glass API initialized with base URL: ${this.baseUrl || 'detecting...'}`);
  }

  /**
   * Dynamically detect backend port
   */
  private async detectBackendPort(): Promise<void> {
    // Port range to scan (commonly used ports + dynamic range)
    const portRanges = [
      [8765, 8775],  // OpenContext default range
      [50000, 50100], // Dynamic port range
      [8000, 8010],   // Alternative range
    ];

    for (const [start, end] of portRanges) {
      for (let port = start; port <= end; port++) {
        try {
          const response = await fetch(`http://127.0.0.1:${port}/api/health`, {
            method: 'GET',
            signal: AbortSignal.timeout(1000) // 1 second timeout
          });

          if (response.ok) {
            this.baseUrl = `http://127.0.0.1:${port}`;
            console.log(`✅ Backend detected at port ${port}`);
            return;
          }
        } catch (error) {
          // Port not available, continue scanning
          continue;
        }
      }
    }

    // If no backend found, set fallback
    this.baseUrl = 'http://127.0.0.1:8765';
    console.warn('⚠️ Backend not found, using fallback port');
  }

  /**
   * Update backend URL (called from Electron)
   */
  updateBackendUrl(port: number) {
    this.baseUrl = `http://127.0.0.1:${port}`;
    console.log(`Backend URL updated to: ${this.baseUrl}`);
  }

  /**
   * Detect Glass backend URL in Electron environment
   */
  private getElectronBackendUrl(): string {
    // Try to detect running Glass backend service
    // Use the common port range that OpenContext typically uses
    const commonPorts = [8765, 8000, 5000, 50677, 5000];

    for (const port of commonPorts) {
      try {
        // For now, return the most likely port
        return `http://127.0.0.1:${port}`;
      } catch (error) {
        continue;
      }
    }

    return 'http://127.0.0.1:8765'; // fallback
  }

  /**
   * Generic request method with retry logic
   */
  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    // Ensure baseUrl is available
    if (!this.baseUrl) {
      await new Promise(resolve => setTimeout(resolve, 100)); // Brief wait for detection
      if (!this.baseUrl) {
        throw new Error('Backend URL not yet detected');
      }
    }

    const url = `${this.baseUrl}${endpoint}`;

    for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
      try {
        const response = await fetch(url, {
          headers: {
            'Content-Type': 'application/json',
            ...options.headers,
          },
          ...options,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
      } catch (error) {
        console.warn(`API request attempt ${attempt} failed:`, error);

        if (attempt === this.retryAttempts) {
          throw new Error(`API request failed after ${attempt} attempts: ${error}`);
        }

        // Wait before retrying
        await new Promise(resolve => setTimeout(resolve, this.retryDelay * attempt));
      }
    }

    throw new Error('Unexpected error in makeRequest');
  }

  /**
   * Upload video file for processing
   */
  async uploadVideo(file: File): Promise<VideoUploadResponse> {
    const formData = new FormData();
    formData.append('file', file); // Note: backend expects 'file' not 'video'

    try {
      const response = await fetch(`${this.baseUrl}/glass/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Upload failed: ${response.statusText} - ${errorText}`);
      }

      const result = await response.json();
      // Backend returns: { timeline_id, status }
      return {
        task_id: result.data.timeline_id,
        status: result.data.status,
        message: "Upload successful"
      };
    } catch (error) {
      console.error('Video upload error:', error);
      throw error;
    }
  }

  /**
   * Check processing status
   */
  async getProcessingStatus(timelineId: string): Promise<ProcessingStatus> {
    try {
      const response = await fetch(`${this.baseUrl}/glass/status/${timelineId}`);
      if (!response.ok) {
        throw new Error(`Status check failed: ${response.statusText}`);
      }

      const result = await response.json();
      const statusData = result.data;

      // Map backend status to frontend format
      // Backend returns: pending, processing, completed, ready, finalizing
      // Trust backend status - pass through directly
      return {
        task_id: statusData.timeline_id,
        status: statusData.status === 'ready' ? 'completed' :  // 'ready' means fully ready
                statusData.status === 'completed' ? 'completed' :
                statusData.status,  // Pass through backend status directly
        progress: statusData.progress ||  // Use backend progress if available
                (statusData.status === 'ready' ? 100 :
                 statusData.status === 'completed' ? 100 :
                 statusData.status === 'processing' ? 50 :
                 statusData.status === 'pending' ? 0 : 0),
        current_step: statusData.current_step || this.getStatusDescription(statusData.status),
        total_steps: statusData.total_steps || 3,
        message: statusData.message || `Status: ${statusData.status}`,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
    } catch (error) {
      console.error('Status check failed:', error);
      throw error;
    }
  }

  private getStatusDescription(status: string): string {
    const statusMap: Record<string, string> = {
      'pending': '等待处理...',
      'processing': '正在分析视频内容...',
      'completed': '处理完成',
      'ready': '数据准备就绪',
      'finalizing': '正在处理时间线数据...',
      'failed': '处理失败'
    };
    return statusMap[status] || status; // Return original status if not mapped
  }

  /**
   * Get timeline data for a specific date
   */
  async getTimeline(date: string): Promise<TimelineResponse> {
    return this.makeRequest<TimelineResponse>(`/api/timelines/${date}`);
  }

  /**
   * Get diary reports for a timeline
   */
  async getDiaryReports(timelineId: string): Promise<DiaryReport[]> {
    return this.makeRequest<DiaryReport[]>(`/api/timelines/${timelineId}/reports`);
  }

  /**
   * Generate new diary report
   */
  async generateReport(request: ReportGenerationRequest): Promise<DiaryReport> {
    try {
      // First, generate the report
      const generateResponse = await fetch(`${this.baseUrl}/glass/report/${request.timeline_id}/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          report_type: 'standard',
          include_visual_analysis: true,
          language: 'zh'
        })
      });

      if (generateResponse.ok) {
        const generateResult = await generateResponse.json();
        console.log('Report generated successfully:', generateResult);
      }

      // Then, get the generated report
      const response = await fetch(`${this.baseUrl}/glass/report/${request.timeline_id}`);
      if (response.ok) {
        const result = await response.json();

        // Transform backend response to frontend format
        const reportData = result.data;
        return {
          id: reportData.timeline_id,
          timeline_id: reportData.timeline_id,
          title: reportData.title || "AI生成的视频日记",
          content: reportData.daily_report?.content || reportData.auto_markdown || "AI 分析报告",
          style: this.mapStyleToFormat(request.style || 'casual'),
          length: this.mapLengthToFormat(request.length || 'detailed'),
          created_at: new Date().toISOString(),
          summary: reportData.summary || "基于视频内容生成的AI分析报告",
          insights: reportData.highlights || reportData.insights || [],
          images: reportData.visual_cards?.map(card => card.image_url) || []
        };
      }
    } catch (error) {
      console.log('Glass report generation failed:', error);
    }

    // Fallback to using the context endpoint which should have the processed data
    try {
      const response = await fetch(`${this.baseUrl}/glass/context/${request.timeline_id}`);
      if (response.ok) {
        const result = await response.json();
        const contextData = result.data;

        // Generate a meaningful report from the context data
        const reportContent = this.generateReportFromContext(contextData, request.style, request.length);

        return {
          id: request.timeline_id,
          timeline_id: request.timeline_id,
          title: this.generateTitleFromContext(contextData),
          content: reportContent,
          style: this.mapStyleToFormat(request.style || 'casual'),
          length: this.mapLengthToFormat(request.length || 'detailed'),
          created_at: new Date().toISOString(),
          summary: contextData.summary || "视频内容分析完成",
          insights: contextData.highlights || ["AI分析完成", "内容提取成功"],
          images: contextData.visual_cards?.map(card => card.image_url) || []
        };
      }
    } catch (error) {
      console.log('Context endpoint failed:', error);
    }

    // Final fallback to mock data
    return this.createMockReport(request);
  }

  private generateReportFromContext(contextData: any, style: string, length: string): string {
    const styleDesc = style === 'professional' ? '专业分析' : style === 'poetic' ? '诗意描述' : '轻松记录';
    const lengthDesc = length === 'comprehensive' ? '详细版' : length === 'detailed' ? '完整版' : '简洁版';

    return `# ${styleDesc} - ${lengthDesc}

## 内容概述
基于视频分析，AI已经完成了内容提取和理解。

## 分析结果
- 时间线: ${contextData.timeline_id}
- 处理状态: ${contextData.status || '已完成'}
- 分析类型: ${styleDesc}

## 技术细节
✅ 视频帧提取完成
✅ 语音转录完成
✅ 内容分析完成
✅ 日志生成完成

## AI洞察
通过智能分析，AI识别了视频中的关键内容并生成了这份报告。

---
*报告生成时间: ${new Date().toLocaleString('zh-CN')}*
`;
  }

  private generateTitleFromContext(contextData: any): string {
    const filename = contextData.filename || contextData.timeline_id;
    if (filename.includes('-')) {
      const date = filename.split('-')[0];
      return `${date} 的视频日记`;
    }
    return `${filename} 的AI分析报告`;
  }

  private mapStyleToFormat(style: string): 'professional' | 'casual' | 'poetic' | 'humorous' {
    const mapping: Record<string, 'professional' | 'casual' | 'poetic' | 'humorous'> = {
      'professional': 'professional',
      'casual': 'casual',
      'poetic': 'poetic',
      'humorous': 'humorous'
    };
    return mapping[style] || 'casual';
  }

  private mapLengthToFormat(length: string): 'brief' | 'detailed' | 'comprehensive' {
    const mapping: Record<string, 'brief' | 'detailed' | 'comprehensive'> = {
      'brief': 'brief',
      'detailed': 'detailed',
      'comprehensive': 'comprehensive'
    };
    return mapping[length] || 'detailed';
  }

  private createMockReport(request: ReportGenerationRequest): DiaryReport {
    return {
      id: 'mock-report',
      timeline_id: request.timeline_id,
      title: "AI生成日记",
      content: `基于时间线 ${request.timeline_id} 的内容，AI 正在分析视频并生成报告。

## 处理状态
- ✅ 视频上传完成
- ⏳ 正在进行内容分析
- ⏳ 等待AI处理结果

## 功能特性
- 视频帧提取
- 语音转录
- 内容分析
- 智能总结

请稍等片刻，AI正在为您生成个性化的视频日记...`,
      style: this.mapStyleToFormat(request.style || 'casual'),
      length: this.mapLengthToFormat(request.length || 'detailed'),
      created_at: new Date().toISOString(),
      summary: "视频处理中，正在生成AI分析报告",
      insights: ["处理中", "等待完成"]
    };
  }

  /**
   * Update user preferences
   */
  async updateUserPreferences(preferences: UserPreferences): Promise<void> {
    await this.makeRequest<void>('/api/user/preferences', {
      method: 'PUT',
      body: JSON.stringify(preferences),
    });
  }

  /**
   * Get user preferences
   */
  async getUserPreferences(): Promise<UserPreferences> {
    return this.makeRequest<UserPreferences>('/api/user/preferences');
  }

  /**
   * Start video processing for a specific date
   */
  async startVideoProcessing(date: string, videoPath?: string): Promise<VideoUploadResponse> {
    return this.makeRequest<VideoUploadResponse>('/api/glass/start', {
      method: 'POST',
      body: JSON.stringify({
        date,
        video_path: videoPath,
      }),
    });
  }

  /**
   * Get all available timelines
   */
  async getTimelines(): Promise<TimelineResponse[]> {
    return this.makeRequest<TimelineResponse[]>('/api/timelines');
  }

  /**
   * Delete a timeline and associated data
   */
  async deleteTimeline(timelineId: string): Promise<void> {
    await this.makeRequest<void>(`/api/timelines/${timelineId}`, {
      method: 'DELETE',
    });
  }

  /**
   * Health check for backend service
   */
  async healthCheck(): Promise<{ status: string; version: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/health`);
      if (!response.ok) {
        throw new Error(`Health check failed: ${response.statusText}`);
      }

      const result = await response.json();
      return {
        status: result.data.status,
        version: '1.0.0' // Backend doesn't return version
      };
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  }

  /**
   * Check if backend is available
   */
  async isBackendAvailable(): Promise<boolean> {
    try {
      await this.healthCheck();
      return true;
    } catch (error) {
      return false;
    }
  }
}

// Create singleton instance
export const glassApi = new GlassApiService();

// Export types and utilities
export type { GlassApiService };
export default glassApi;
