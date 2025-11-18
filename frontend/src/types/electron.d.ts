/**
 * Electron API Type Definitions
 *
 * Type definitions for Electron preload scripts and main process APIs
 */

export interface ElectronAPI {
  /**
   * Check if running in Electron environment
   */
  isElectron: boolean;

  /**
   * Get application version
   */
  getAppVersion: () => Promise<string>;

  /**
   * Show file dialog for selecting files
   */
  showOpenDialog: (options: {
    title?: string;
    defaultPath?: string;
    filters?: Array<{
      name: string;
      extensions: string[];
    }>;
    properties?: Array<'openFile' | 'openDirectory' | 'multiSelections'>;
  }) => Promise<{
    canceled: boolean;
    filePaths: string[];
  }>;

  /**
   * Show file dialog for saving files
   */
  showSaveDialog: (options: {
    title?: string;
    defaultPath?: string;
    filters?: Array<{
      name: string;
      extensions: string[];
    }>;
  }) => Promise<{
    canceled: boolean;
    filePath?: string;
  }>;

  /**
   * Get system information
   */
  getSystemInfo: () => Promise<{
    platform: string;
    arch: string;
    version: string;
  }>;

  /**
   * Show notification
   */
  showNotification: (options: {
    title: string;
    body: string;
    icon?: string;
  }) => Promise<void>;

  /**
   * Minimize application window
   */
  minimizeWindow: () => Promise<void>;

  /**
   * Maximize application window
   */
  maximizeWindow: () => Promise<void>;

  /**
   * Close application window
   */
  closeWindow: () => Promise<void>;

  /**
   * Check if backend service is running
   */
  checkBackendService: () => Promise<{
    running: boolean;
    port?: number;
    url?: string;
  }>;

  /**
   * Start backend service
   */
  startBackendService: () => Promise<{
    success: boolean;
    port?: number;
    url?: string;
    error?: string;
  }>;

  /**
   * Stop backend service
   */
  stopBackendService: () => Promise<void>;

  /**
   * Get available ports for backend detection
   */
  scanAvailablePorts: () => Promise<number[]>;

  /**
   * Write to application log
   */
  log: (level: 'info' | 'warn' | 'error', message: string) => Promise<void>;
}

declare global {
  interface Window {
    electronAPI?: ElectronAPI;
  }
}

export {};