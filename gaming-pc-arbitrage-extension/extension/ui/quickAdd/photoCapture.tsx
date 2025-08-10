/**
 * Photo Capture Component
 * Handles camera capture and photo upload for quick PC spec extraction
 */

import React, { useState, useRef, useCallback } from 'react';
import { tesseractExtractor } from '@arbitrage/core';
import type { ExtractedSpecs, Listing } from '@arbitrage/core';

interface PhotoCaptureProps {
  onSpecsExtracted: (specs: ExtractedSpecs) => void;
  onListingCreated?: (listing: Listing) => void;
  onClose: () => void;
}

export const PhotoCapture: React.FC<PhotoCaptureProps> = ({
  onSpecsExtracted,
  onListingCreated,
  onClose
}) => {
  const [mode, setMode] = useState<'camera' | 'upload'>('upload');
  const [isProcessing, setIsProcessing] = useState(false);
  const [extractedSpecs, setExtractedSpecs] = useState<ExtractedSpecs | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Initialize camera
  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'environment',
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        }
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        streamRef.current = stream;
      }
    } catch (err) {
      console.error('Camera access failed:', err);
      setError('Unable to access camera. Please check permissions.');
      setMode('upload');
    }
  }, []);

  // Stop camera
  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
  }, []);

  // Capture photo from camera
  const capturePhoto = useCallback(async () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');
    
    if (!context) return;

    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw video frame to canvas
    context.drawImage(video, 0, 0);

    // Convert to blob
    canvas.toBlob(async (blob) => {
      if (!blob) {
        setError('Failed to capture photo');
        return;
      }

      // Create preview URL
      const url = URL.createObjectURL(blob);
      setPreviewUrl(url);

      // Stop camera after capture
      stopCamera();

      // Process the image
      await processImage(blob);
    }, 'image/jpeg', 0.95);
  }, [stopCamera]);

  // Process uploaded file
  const handleFileUpload = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    
    // Validate file type
    if (!file.type.startsWith('image/')) {
      setError('Please select an image file');
      return;
    }

    // Create preview
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);

    // Process the image
    await processImage(file);
  }, []);

  // Process image with OCR
  const processImage = async (imageSource: File | Blob) => {
    setIsProcessing(true);
    setError(null);
    setProgress(0);

    try {
      // Initialize Tesseract if needed
      await tesseractExtractor.initialize();

      // Update progress
      setProgress(20);

      // Extract specs with confidence threshold
      const specs = await tesseractExtractor.extractWithConfidence(
        imageSource,
        0.6, // Lower threshold for real-world photos
        3    // Try multiple preprocessing strategies
      );

      setProgress(80);
      setExtractedSpecs(specs);
      onSpecsExtracted(specs);
      setProgress(100);

      // Auto-create listing if confidence is high
      if (specs.confidence > 0.8 && onListingCreated) {
        const listing = createListingFromSpecs(specs);
        onListingCreated(listing);
      }
    } catch (err) {
      console.error('OCR processing failed:', err);
      setError('Failed to extract specifications from image. Please try a clearer photo.');
    } finally {
      setIsProcessing(false);
    }
  };

  // Create listing from extracted specs
  const createListingFromSpecs = (specs: ExtractedSpecs): Listing => {
    const components: any = {};
    
    if (specs.cpu) {
      components.cpu = { model: specs.cpu, brand: detectCPUBrand(specs.cpu) };
    }
    
    if (specs.gpu) {
      components.gpu = { model: specs.gpu, brand: detectGPUBrand(specs.gpu) };
    }
    
    if (specs.ram) {
      const ramMatch = specs.ram.match(/(\d+)\s*GB/i);
      if (ramMatch) {
        components.ram = [{
          capacity: parseInt(ramMatch[1]),
          type: specs.ram.includes('DDR5') ? 'DDR5' : 'DDR4',
          speed: extractRAMSpeed(specs.ram)
        }];
      }
    }
    
    if (specs.storage && specs.storage.length > 0) {
      components.storage = specs.storage.map(s => {
        const match = s.match(/(\d+)\s*(GB|TB)/i);
        const capacity = match ? parseInt(match[1]) * (match[2].toUpperCase() === 'TB' ? 1000 : 1) : 256;
        return {
          capacity,
          type: s.toLowerCase().includes('nvme') ? 'NVMe' : 
                s.toLowerCase().includes('ssd') ? 'SSD' : 'HDD'
        };
      });
    }

    if (specs.motherboard) {
      components.motherboard = { model: specs.motherboard };
    }

    if (specs.psu) {
      const wattMatch = specs.psu.match(/(\d+)\s*W/i);
      if (wattMatch) {
        components.psu = { 
          model: specs.psu,
          wattage: parseInt(wattMatch[1])
        };
      }
    }

    // Generate title from components
    const title = generateTitle(components);

    return {
      id: `photo-${Date.now()}`,
      externalId: '',
      url: '',
      platform: 'photo',
      title,
      description: `Specifications extracted from photo:\n${specs.rawText}`,
      price: 0, // User needs to set price
      location: { city: '', state: '', zipCode: '' },
      seller: { id: '', name: '', responseRate: 0, memberSince: new Date() },
      images: previewUrl ? [previewUrl] : [],
      condition: 'unknown',
      category: 'gaming-pc',
      subcategory: 'desktop',
      attributes: {},
      postedAt: new Date(),
      lastUpdated: new Date(),
      status: 'draft',
      viewCount: 0,
      savedCount: 0,
      components,
      metadata: {
        source: 'photo_capture',
        ocrConfidence: specs.confidence,
        extractedAt: new Date().toISOString()
      }
    };
  };

  // Helper functions
  const detectCPUBrand = (cpu: string): string => {
    const cpuLower = cpu.toLowerCase();
    if (cpuLower.includes('intel') || cpuLower.includes('core')) return 'Intel';
    if (cpuLower.includes('amd') || cpuLower.includes('ryzen')) return 'AMD';
    return 'Unknown';
  };

  const detectGPUBrand = (gpu: string): string => {
    const gpuLower = gpu.toLowerCase();
    if (gpuLower.includes('nvidia') || gpuLower.includes('geforce') || gpuLower.includes('rtx') || gpuLower.includes('gtx')) return 'NVIDIA';
    if (gpuLower.includes('amd') || gpuLower.includes('radeon')) return 'AMD';
    if (gpuLower.includes('intel')) return 'Intel';
    return 'Unknown';
  };

  const extractRAMSpeed = (ram: string): number => {
    const speedMatch = ram.match(/(\d{4})\s*MHz/i);
    return speedMatch ? parseInt(speedMatch[1]) : 3200;
  };

  const generateTitle = (components: any): string => {
    const parts = [];
    
    if (components.cpu) {
      parts.push(components.cpu.model);
    }
    
    if (components.gpu) {
      parts.push(components.gpu.model);
    }
    
    if (components.ram && components.ram[0]) {
      parts.push(`${components.ram[0].capacity}GB RAM`);
    }
    
    if (components.storage && components.storage[0]) {
      parts.push(`${components.storage[0].capacity}GB ${components.storage[0].type}`);
    }
    
    return parts.length > 0 ? `Gaming PC - ${parts.join(', ')}` : 'Gaming PC';
  };

  // Retry with different image
  const retry = () => {
    setExtractedSpecs(null);
    setError(null);
    setPreviewUrl(null);
    setProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Render
  return (
    <div className="photo-capture-modal">
      <div className="modal-content">
        <div className="modal-header">
          <h2>Quick Add from Photo</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        {!previewUrl && !extractedSpecs && (
          <div className="capture-options">
            <div className="mode-selector">
              <button
                className={`mode-btn ${mode === 'upload' ? 'active' : ''}`}
                onClick={() => setMode('upload')}
              >
                📁 Upload Photo
              </button>
              <button
                className={`mode-btn ${mode === 'camera' ? 'active' : ''}`}
                onClick={() => {
                  setMode('camera');
                  startCamera();
                }}
              >
                📷 Take Photo
              </button>
            </div>

            {mode === 'upload' && (
              <div className="upload-section">
                <label className="upload-label">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleFileUpload}
                    style={{ display: 'none' }}
                  />
                  <div className="upload-area">
                    <span className="upload-icon">📸</span>
                    <p>Click to select a photo or drag & drop</p>
                    <p className="hint">Best results with clear spec sheets or labels</p>
                  </div>
                </label>
              </div>
            )}

            {mode === 'camera' && (
              <div className="camera-section">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  className="camera-preview"
                />
                <canvas ref={canvasRef} style={{ display: 'none' }} />
                <button className="capture-btn" onClick={capturePhoto}>
                  📸 Capture Photo
                </button>
              </div>
            )}
          </div>
        )}

        {previewUrl && !extractedSpecs && (
          <div className="preview-section">
            <img src={previewUrl} alt="Captured" className="preview-image" />
            {isProcessing && (
              <div className="processing-overlay">
                <div className="spinner"></div>
                <p>Extracting specifications...</p>
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {extractedSpecs && (
          <div className="results-section">
            <h3>Extracted Specifications</h3>
            <div className="confidence-indicator">
              <span>Confidence: </span>
              <div className="confidence-bar">
                <div 
                  className="confidence-fill"
                  style={{ 
                    width: `${extractedSpecs.confidence * 100}%`,
                    backgroundColor: extractedSpecs.confidence > 0.7 ? '#4CAF50' : 
                                   extractedSpecs.confidence > 0.5 ? '#FFC107' : '#F44336'
                  }}
                />
              </div>
              <span>{(extractedSpecs.confidence * 100).toFixed(0)}%</span>
            </div>

            <div className="specs-grid">
              {extractedSpecs.cpu && (
                <div className="spec-item">
                  <label>CPU:</label>
                  <span>{extractedSpecs.cpu}</span>
                </div>
              )}
              {extractedSpecs.gpu && (
                <div className="spec-item">
                  <label>GPU:</label>
                  <span>{extractedSpecs.gpu}</span>
                </div>
              )}
              {extractedSpecs.ram && (
                <div className="spec-item">
                  <label>RAM:</label>
                  <span>{extractedSpecs.ram}</span>
                </div>
              )}
              {extractedSpecs.storage && extractedSpecs.storage.length > 0 && (
                <div className="spec-item">
                  <label>Storage:</label>
                  <span>{extractedSpecs.storage.join(', ')}</span>
                </div>
              )}
              {extractedSpecs.motherboard && (
                <div className="spec-item">
                  <label>Motherboard:</label>
                  <span>{extractedSpecs.motherboard}</span>
                </div>
              )}
              {extractedSpecs.psu && (
                <div className="spec-item">
                  <label>PSU:</label>
                  <span>{extractedSpecs.psu}</span>
                </div>
              )}
            </div>

            <div className="actions">
              <button className="btn btn-secondary" onClick={retry}>
                Try Another Photo
              </button>
              <button 
                className="btn btn-primary" 
                onClick={() => {
                  if (onListingCreated) {
                    const listing = createListingFromSpecs(extractedSpecs);
                    onListingCreated(listing);
                  }
                  onClose();
                }}
              >
                Create Listing
              </button>
            </div>
          </div>
        )}

        {error && (
          <div className="error-message">
            <p>⚠️ {error}</p>
            <button className="btn btn-secondary" onClick={retry}>
              Try Again
            </button>
          </div>
        )}
      </div>

      <style jsx>{`
        .photo-capture-modal {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.8);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .modal-content {
          background: white;
          border-radius: 12px;
          width: 90%;
          max-width: 600px;
          max-height: 90vh;
          overflow-y: auto;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px;
          border-bottom: 1px solid #e0e0e0;
        }

        .modal-header h2 {
          margin: 0;
          font-size: 24px;
          color: #333;
        }

        .close-btn {
          background: none;
          border: none;
          font-size: 24px;
          cursor: pointer;
          color: #666;
          padding: 0;
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 4px;
          transition: all 0.2s;
        }

        .close-btn:hover {
          background: #f0f0f0;
          color: #333;
        }

        .capture-options {
          padding: 20px;
        }

        .mode-selector {
          display: flex;
          gap: 10px;
          margin-bottom: 20px;
        }

        .mode-btn {
          flex: 1;
          padding: 12px 20px;
          border: 2px solid #e0e0e0;
          background: white;
          border-radius: 8px;
          font-size: 16px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .mode-btn.active {
          background: #2196F3;
          color: white;
          border-color: #2196F3;
        }

        .mode-btn:hover:not(.active) {
          background: #f5f5f5;
        }

        .upload-section {
          margin-top: 20px;
        }

        .upload-area {
          border: 2px dashed #2196F3;
          border-radius: 12px;
          padding: 60px 20px;
          text-align: center;
          cursor: pointer;
          transition: all 0.2s;
          background: #f8f9fa;
        }

        .upload-area:hover {
          background: #e3f2fd;
          border-color: #1976D2;
        }

        .upload-icon {
          font-size: 48px;
          display: block;
          margin-bottom: 10px;
        }

        .upload-area p {
          margin: 5px 0;
          color: #666;
        }

        .upload-area .hint {
          font-size: 14px;
          color: #999;
        }

        .camera-section {
          position: relative;
        }

        .camera-preview {
          width: 100%;
          border-radius: 8px;
          background: #000;
        }

        .capture-btn {
          position: absolute;
          bottom: 20px;
          left: 50%;
          transform: translateX(-50%);
          padding: 12px 24px;
          background: #4CAF50;
          color: white;
          border: none;
          border-radius: 24px;
          font-size: 16px;
          cursor: pointer;
          box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
          transition: all 0.2s;
        }

        .capture-btn:hover {
          background: #45a049;
          transform: translateX(-50%) translateY(-2px);
          box-shadow: 0 6px 16px rgba(76, 175, 80, 0.4);
        }

        .preview-section {
          padding: 20px;
          position: relative;
        }

        .preview-image {
          width: 100%;
          border-radius: 8px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        .processing-overlay {
          position: absolute;
          top: 20px;
          left: 20px;
          right: 20px;
          bottom: 20px;
          background: rgba(255, 255, 255, 0.95);
          border-radius: 8px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
        }

        .spinner {
          width: 48px;
          height: 48px;
          border: 4px solid #f3f3f3;
          border-top: 4px solid #2196F3;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin-bottom: 16px;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .progress-bar {
          width: 200px;
          height: 4px;
          background: #e0e0e0;
          border-radius: 2px;
          overflow: hidden;
          margin-top: 10px;
        }

        .progress-fill {
          height: 100%;
          background: #2196F3;
          transition: width 0.3s ease;
        }

        .results-section {
          padding: 20px;
        }

        .results-section h3 {
          margin: 0 0 16px 0;
          color: #333;
        }

        .confidence-indicator {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 20px;
          font-size: 14px;
        }

        .confidence-bar {
          flex: 1;
          height: 8px;
          background: #e0e0e0;
          border-radius: 4px;
          overflow: hidden;
        }

        .confidence-fill {
          height: 100%;
          transition: width 0.3s ease;
        }

        .specs-grid {
          display: grid;
          gap: 12px;
          margin-bottom: 20px;
        }

        .spec-item {
          display: flex;
          padding: 12px;
          background: #f5f5f5;
          border-radius: 6px;
        }

        .spec-item label {
          font-weight: 600;
          color: #666;
          width: 120px;
        }

        .spec-item span {
          flex: 1;
          color: #333;
        }

        .actions {
          display: flex;
          gap: 10px;
        }

        .btn {
          padding: 10px 20px;
          border: none;
          border-radius: 6px;
          font-size: 16px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-primary {
          background: #2196F3;
          color: white;
        }

        .btn-primary:hover {
          background: #1976D2;
        }

        .btn-secondary {
          background: #f5f5f5;
          color: #666;
        }

        .btn-secondary:hover {
          background: #e0e0e0;
        }

        .error-message {
          padding: 20px;
          text-align: center;
        }

        .error-message p {
          color: #f44336;
          margin-bottom: 16px;
        }
      `}</style>
    </div>
  );
};