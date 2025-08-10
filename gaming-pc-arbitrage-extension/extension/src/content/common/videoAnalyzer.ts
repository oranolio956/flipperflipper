/**
 * Video Analyzer
 * Extract metadata from embedded videos
 */

export interface VideoMetadata {
  url: string;
  duration?: number; // seconds
  resolution?: {
    width: number;
    height: number;
  };
  thumbnail?: string;
  title?: string;
  source: 'facebook' | 'youtube' | 'vimeo' | 'other';
}

/**
 * Analyze all videos on page
 */
export function analyzeVideos(): VideoMetadata[] {
  const videos: VideoMetadata[] = [];
  
  // Find video elements
  const videoElements = findVideoElements();
  
  videoElements.forEach(element => {
    const metadata = extractVideoMetadata(element);
    if (metadata) {
      videos.push(metadata);
    }
  });
  
  // Also check for embedded iframes
  const iframes = document.querySelectorAll('iframe');
  iframes.forEach(iframe => {
    const metadata = extractIframeVideo(iframe);
    if (metadata) {
      videos.push(metadata);
    }
  });
  
  return videos;
}

/**
 * Find all video elements
 */
function findVideoElements(): HTMLVideoElement[] {
  const videos: HTMLVideoElement[] = [];
  
  // Direct video elements
  document.querySelectorAll('video').forEach(video => {
    videos.push(video);
  });
  
  // Facebook video containers
  document.querySelectorAll('[data-video-id], [data-pagelet*="Video"]').forEach(container => {
    const video = container.querySelector('video');
    if (video && !videos.includes(video)) {
      videos.push(video);
    }
  });
  
  return videos;
}

/**
 * Extract metadata from video element
 */
function extractVideoMetadata(video: HTMLVideoElement): VideoMetadata | null {
  if (!video.src && !video.currentSrc) return null;
  
  const url = video.currentSrc || video.src;
  
  const metadata: VideoMetadata = {
    url,
    source: detectVideoSource(url),
  };
  
  // Duration
  if (video.duration && !isNaN(video.duration)) {
    metadata.duration = Math.round(video.duration);
  }
  
  // Resolution
  if (video.videoWidth && video.videoHeight) {
    metadata.resolution = {
      width: video.videoWidth,
      height: video.videoHeight,
    };
  }
  
  // Poster/thumbnail
  if (video.poster) {
    metadata.thumbnail = video.poster;
  }
  
  // Title from attributes or nearby text
  const title = video.getAttribute('aria-label') || 
                video.getAttribute('title') ||
                findVideoTitle(video);
  if (title) {
    metadata.title = title;
  }
  
  return metadata;
}

/**
 * Extract video from iframe
 */
function extractIframeVideo(iframe: HTMLIFrameElement): VideoMetadata | null {
  const src = iframe.src;
  if (!src) return null;
  
  // YouTube
  const ytMatch = src.match(/(?:youtube\.com\/embed\/|youtu\.be\/)([a-zA-Z0-9_-]+)/);
  if (ytMatch) {
    return {
      url: src,
      source: 'youtube',
      title: iframe.title || undefined,
      thumbnail: `https://img.youtube.com/vi/${ytMatch[1]}/hqdefault.jpg`,
    };
  }
  
  // Vimeo
  const vimeoMatch = src.match(/vimeo\.com\/video\/(\d+)/);
  if (vimeoMatch) {
    return {
      url: src,
      source: 'vimeo',
      title: iframe.title || undefined,
    };
  }
  
  // Facebook
  if (src.includes('facebook.com/plugins/video')) {
    return {
      url: src,
      source: 'facebook',
      title: iframe.title || undefined,
    };
  }
  
  return null;
}

/**
 * Detect video source
 */
function detectVideoSource(url: string): VideoMetadata['source'] {
  if (url.includes('fbcdn.net') || url.includes('facebook')) {
    return 'facebook';
  }
  if (url.includes('youtube.com') || url.includes('youtu.be')) {
    return 'youtube';
  }
  if (url.includes('vimeo.com')) {
    return 'vimeo';
  }
  return 'other';
}

/**
 * Find video title from nearby elements
 */
function findVideoTitle(video: HTMLElement): string | null {
  // Check parent containers
  let parent = video.parentElement;
  let depth = 0;
  
  while (parent && depth < 3) {
    // Look for headings
    const heading = parent.querySelector('h1, h2, h3, h4');
    if (heading?.textContent) {
      return heading.textContent.trim();
    }
    
    // Look for aria-label
    const label = parent.getAttribute('aria-label');
    if (label) {
      return label;
    }
    
    parent = parent.parentElement;
    depth++;
  }
  
  return null;
}

/**
 * Format duration for display
 */
export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Create video info display
 */
export function createVideoInfoDisplay(videos: VideoMetadata[]): HTMLElement {
  const container = document.createElement('div');
  container.className = 'arbitrage-video-info';
  
  if (videos.length === 0) {
    container.innerHTML = '<p>No videos found</p>';
    return container;
  }
  
  container.innerHTML = `
    <h4>Videos (${videos.length})</h4>
    <div class="video-list">
      ${videos.map((video, i) => `
        <div class="video-item">
          ${video.thumbnail ? `<img src="${video.thumbnail}" alt="">` : ''}
          <div class="video-details">
            <div class="video-title">${video.title || `Video ${i + 1}`}</div>
            <div class="video-meta">
              ${video.duration ? `<span>${formatDuration(video.duration)}</span>` : ''}
              ${video.resolution ? `<span>${video.resolution.width}×${video.resolution.height}</span>` : ''}
              <span class="video-source">${video.source}</span>
            </div>
          </div>
        </div>
      `).join('')}
    </div>
  `;
  
  // Add styles
  const style = document.createElement('style');
  style.textContent = `
    .arbitrage-video-info {
      background: #f9fafb;
      border: 1px solid #e5e7eb;
      border-radius: 8px;
      padding: 12px;
      margin-top: 12px;
    }
    
    .arbitrage-video-info h4 {
      margin: 0 0 12px 0;
      font-size: 14px;
      font-weight: 600;
    }
    
    .video-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    
    .video-item {
      display: flex;
      gap: 8px;
      padding: 8px;
      background: white;
      border-radius: 6px;
      border: 1px solid #e5e7eb;
    }
    
    .video-item img {
      width: 60px;
      height: 40px;
      object-fit: cover;
      border-radius: 4px;
    }
    
    .video-details {
      flex: 1;
    }
    
    .video-title {
      font-size: 13px;
      font-weight: 500;
      margin-bottom: 4px;
    }
    
    .video-meta {
      display: flex;
      gap: 8px;
      font-size: 11px;
      color: #6b7280;
    }
    
    .video-source {
      text-transform: capitalize;
      background: #f3f4f6;
      padding: 2px 6px;
      border-radius: 3px;
    }
  `;
  
  document.head.appendChild(style);
  
  return container;
}