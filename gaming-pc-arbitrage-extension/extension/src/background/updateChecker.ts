/**
 * Auto-Update Checker
 * Checks for extension updates and manages update flow
 */

export interface UpdateStatus {
  currentVersion: string;
  latestVersion?: string;
  updateAvailable: boolean;
  lastCheck: Date;
  channel: 'production' | 'beta' | 'dev';
  buildHash?: string;
  releaseNotes?: string;
}

export class UpdateChecker {
  private updateCheckInterval = 24 * 60 * 60 * 1000; // 24 hours
  private updateStatus: UpdateStatus;
  private checkTimer?: number;
  
  constructor() {
    const manifest = chrome.runtime.getManifest();
    this.updateStatus = {
      currentVersion: manifest.version,
      updateAvailable: false,
      lastCheck: new Date(),
      channel: this.detectChannel(manifest.version)
    };
    
    this.initialize();
  }
  
  private async initialize() {
    // Set up periodic check alarm
    chrome.alarms.create('update-check', {
      periodInMinutes: 60 * 24 // Daily
    });
    
    chrome.alarms.onAlarm.addListener((alarm) => {
      if (alarm.name === 'update-check') {
        this.checkForUpdates();
      }
    });
    
    // Listen for runtime update events
    chrome.runtime.onUpdateAvailable.addListener((details) => {
      console.log('Update available:', details);
      this.handleUpdateAvailable(details);
    });
    
    // Check on startup
    this.checkForUpdates();
  }
  
  private detectChannel(version: string): 'production' | 'beta' | 'dev' {
    if (version.includes('beta')) return 'beta';
    if (version.includes('dev') || version.includes('alpha')) return 'dev';
    return 'production';
  }
  
  async checkForUpdates() {
    console.log('Checking for updates...');
    
    try {
      // For Chrome Web Store installs
      if (chrome.runtime.id && !chrome.runtime.id.includes('development')) {
        // Request update check from Chrome
        const [status, details] = await new Promise<[chrome.runtime.RequestUpdateCheckStatus, any]>(
          (resolve) => chrome.runtime.requestUpdateCheck(resolve)
        );
        
        this.updateStatus.lastCheck = new Date();
        
        if (status === 'update_available') {
          this.updateStatus.updateAvailable = true;
          this.updateStatus.latestVersion = details?.version;
          
          // Notify UI
          this.notifyUpdateAvailable();
          
          // Store status
          await chrome.storage.local.set({ updateStatus: this.updateStatus });
          
          return true;
        } else if (status === 'no_update') {
          this.updateStatus.updateAvailable = false;
          console.log('No update available');
        } else if (status === 'throttled') {
          console.log('Update check throttled, will retry later');
        }
      }
      
      // For self-hosted/enterprise installs with update_url
      if (chrome.runtime.getManifest().update_url) {
        await this.checkSelfHostedUpdate();
      }
      
      // For development - check GitHub releases
      if (this.updateStatus.channel === 'dev') {
        await this.checkGitHubReleases();
      }
      
    } catch (error) {
      console.error('Update check failed:', error);
    }
    
    return false;
  }
  
  private async checkSelfHostedUpdate() {
    const manifest = chrome.runtime.getManifest();
    if (!manifest.update_url) return;
    
    try {
      // Fetch update manifest
      const response = await fetch(manifest.update_url);
      const updateManifest = await response.text();
      
      // Parse XML (basic parser)
      const versionMatch = updateManifest.match(/version=['"]([^'"]+)['"]/);
      if (versionMatch && versionMatch[1] !== manifest.version) {
        this.updateStatus.updateAvailable = true;
        this.updateStatus.latestVersion = versionMatch[1];
        this.notifyUpdateAvailable();
      }
    } catch (error) {
      console.error('Self-hosted update check failed:', error);
    }
  }
  
  private async checkGitHubReleases() {
    try {
      // Check releases.json from CI/CD
      const response = await fetch('https://raw.githubusercontent.com/oranolio956/flipperflipper/main/releases.json');
      const releases = await response.json();
      
      const latestRelease = releases[0];
      if (latestRelease && this.compareVersions(latestRelease.version, this.updateStatus.currentVersion) > 0) {
        this.updateStatus.updateAvailable = true;
        this.updateStatus.latestVersion = latestRelease.version;
        this.updateStatus.releaseNotes = latestRelease.notes;
        this.updateStatus.buildHash = latestRelease.hash;
        
        this.notifyUpdateAvailable();
      }
    } catch (error) {
      console.error('GitHub release check failed:', error);
    }
  }
  
  private compareVersions(v1: string, v2: string): number {
    const parts1 = v1.split('.').map(Number);
    const parts2 = v2.split('.').map(Number);
    
    for (let i = 0; i < Math.max(parts1.length, parts2.length); i++) {
      const part1 = parts1[i] || 0;
      const part2 = parts2[i] || 0;
      
      if (part1 > part2) return 1;
      if (part1 < part2) return -1;
    }
    
    return 0;
  }
  
  private handleUpdateAvailable(details: any) {
    this.updateStatus.updateAvailable = true;
    this.updateStatus.latestVersion = details?.version;
    
    // Chrome will automatically update on browser restart
    // We just need to notify the user
    this.notifyUpdateAvailable();
  }
  
  private async notifyUpdateAvailable() {
    // Send message to all extension pages
    chrome.runtime.sendMessage({
      type: 'UPDATE_AVAILABLE',
      status: this.updateStatus
    });
    
    // Create notification
    chrome.notifications.create('update-available', {
      type: 'basic',
      iconUrl: chrome.runtime.getURL('icons/icon-128.png'),
      title: 'Update Available',
      message: `Version ${this.updateStatus.latestVersion} is ready to install. Restart browser to update.`,
      buttons: [
        { title: 'Update Now' },
        { title: 'Later' }
      ],
      requireInteraction: true
    });
    
    // Handle notification clicks
    chrome.notifications.onButtonClicked.addListener((notifId, btnIdx) => {
      if (notifId === 'update-available' && btnIdx === 0) {
        // Trigger browser restart for update
        chrome.runtime.reload();
      }
    });
  }
  
  async getStatus(): Promise<UpdateStatus> {
    return {
      ...this.updateStatus,
      buildHash: await this.getBuildHash()
    };
  }
  
  private async getBuildHash(): Promise<string> {
    // Try to get from manifest
    const manifest = chrome.runtime.getManifest();
    if (manifest.version_name && manifest.version_name.includes('+')) {
      return manifest.version_name.split('+')[1];
    }
    
    // Try to get from build info file
    try {
      const response = await fetch(chrome.runtime.getURL('build-info.json'));
      const buildInfo = await response.json();
      return buildInfo.hash?.substring(0, 7) || 'unknown';
    } catch {
      return 'dev';
    }
  }
  
  async applyUpdate() {
    if (this.updateStatus.updateAvailable) {
      // For Chrome Web Store, just reload
      chrome.runtime.reload();
    }
  }
}

// Export singleton
export const updateChecker = new UpdateChecker();