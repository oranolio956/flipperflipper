/**
 * Voice Transcription Module
 * Handles voice note recording and transcription using Web Speech API
 */

import { VoiceNote } from '../types';

export interface TranscriptionResult {
  text: string;
  confidence: number;
  alternatives: Array<{
    text: string;
    confidence: number;
  }>;
  language: string;
  isFinal: boolean;
}

export interface VoiceTranscriberOptions {
  language?: string;
  continuous?: boolean;
  interimResults?: boolean;
  maxAlternatives?: number;
  profanityFilter?: boolean;
}

export class VoiceTranscriber {
  private recognition: any; // SpeechRecognition
  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks: Blob[] = [];
  private isRecording = false;
  private stream: MediaStream | null = null;
  
  private readonly defaultOptions: VoiceTranscriberOptions = {
    language: 'en-US',
    continuous: true,
    interimResults: true,
    maxAlternatives: 3,
    profanityFilter: false
  };

  constructor(options: VoiceTranscriberOptions = {}) {
    this.initializeSpeechRecognition(options);
  }

  /**
   * Initialize Web Speech API
   */
  private initializeSpeechRecognition(options: VoiceTranscriberOptions): void {
    // Check for browser support
    const SpeechRecognition = (window as any).SpeechRecognition || 
                             (window as any).webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      console.warn('Speech recognition not supported in this browser');
      return;
    }

    this.recognition = new SpeechRecognition();
    const config = { ...this.defaultOptions, ...options };
    
    // Configure recognition
    this.recognition.lang = config.language!;
    this.recognition.continuous = config.continuous!;
    this.recognition.interimResults = config.interimResults!;
    this.recognition.maxAlternatives = config.maxAlternatives!;
  }

  /**
   * Start voice recording and transcription
   */
  async startRecording(): Promise<void> {
    if (this.isRecording) {
      throw new Error('Already recording');
    }

    try {
      // Get user media
      this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Start audio recording
      this.mediaRecorder = new MediaRecorder(this.stream);
      this.audioChunks = [];
      
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };
      
      this.mediaRecorder.start();
      
      // Start speech recognition
      if (this.recognition) {
        this.recognition.start();
      }
      
      this.isRecording = true;
    } catch (error) {
      console.error('Failed to start recording:', error);
      throw new Error('Microphone access denied or not available');
    }
  }

  /**
   * Stop recording and return results
   */
  async stopRecording(): Promise<{ audio: Blob; duration: number }> {
    if (!this.isRecording) {
      throw new Error('Not recording');
    }

    return new Promise((resolve, reject) => {
      if (this.mediaRecorder) {
        this.mediaRecorder.onstop = () => {
          const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
          const duration = this.audioChunks.length > 0 ? 
            this.mediaRecorder!.state === 'inactive' ? 
              Date.now() - (this.mediaRecorder as any).startTime : 0 
            : 0;
          
          // Stop all tracks
          if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
          }
          
          this.isRecording = false;
          resolve({ audio: audioBlob, duration });
        };
        
        this.mediaRecorder.stop();
        
        // Stop speech recognition
        if (this.recognition) {
          this.recognition.stop();
        }
      } else {
        reject(new Error('No media recorder available'));
      }
    });
  }

  /**
   * Set up transcription event handlers
   */
  onTranscription(
    callback: (result: TranscriptionResult) => void
  ): () => void {
    if (!this.recognition) {
      console.warn('Speech recognition not available');
      return () => {};
    }

    const handleResult = (event: any) => {
      const result = event.results[event.results.length - 1];
      const transcript = result[0].transcript;
      const confidence = result[0].confidence || 0.9; // Chrome doesn't always provide confidence
      
      // Get alternatives
      const alternatives: Array<{ text: string; confidence: number }> = [];
      for (let i = 1; i < result.length && i <= 3; i++) {
        if (result[i]) {
          alternatives.push({
            text: result[i].transcript,
            confidence: result[i].confidence || 0.8
          });
        }
      }
      
      callback({
        text: transcript,
        confidence,
        alternatives,
        language: this.recognition.lang,
        isFinal: result.isFinal
      });
    };

    this.recognition.addEventListener('result', handleResult);
    
    // Return cleanup function
    return () => {
      this.recognition.removeEventListener('result', handleResult);
    };
  }

  /**
   * Set up error handler
   */
  onError(callback: (error: Error) => void): () => void {
    if (!this.recognition) {
      return () => {};
    }

    const handleError = (event: any) => {
      let errorMessage = 'Speech recognition error';
      
      switch (event.error) {
        case 'no-speech':
          errorMessage = 'No speech detected';
          break;
        case 'audio-capture':
          errorMessage = 'Microphone not available';
          break;
        case 'not-allowed':
          errorMessage = 'Microphone permission denied';
          break;
        case 'network':
          errorMessage = 'Network error during recognition';
          break;
      }
      
      callback(new Error(errorMessage));
    };

    this.recognition.addEventListener('error', handleError);
    
    return () => {
      this.recognition.removeEventListener('error', handleError);
    };
  }

  /**
   * Process voice note with enhanced features
   */
  async processVoiceNote(
    audioBlob: Blob,
    metadata?: Partial<VoiceNote>
  ): Promise<VoiceNote> {
    // Generate unique ID
    const id = `voice_${Date.now()}`;
    
    // Convert blob to base64 for storage
    const audioUrl = await this.blobToDataUrl(audioBlob);
    
    // Get audio duration
    const duration = await this.getAudioDuration(audioBlob);
    
    // Create voice note
    const voiceNote: VoiceNote = {
      id,
      audioUrl,
      duration,
      transcript: metadata?.transcript || '',
      confidence: metadata?.confidence || 0,
      createdAt: new Date(),
      processed: false,
      tags: metadata?.tags || [],
      category: metadata?.category || 'general'
    };
    
    return voiceNote;
  }

  /**
   * Extract key information from transcript
   */
  extractKeyInfo(transcript: string): {
    price?: number;
    location?: string;
    items?: string[];
    action?: string;
  } {
    const extracted: any = {};
    
    // Extract price mentions
    const priceMatch = transcript.match(/\$?\d+(?:,\d{3})*(?:\.\d{2})?|\d+\s*dollars?/i);
    if (priceMatch) {
      const priceStr = priceMatch[0].replace(/[$,]/g, '');
      extracted.price = parseFloat(priceStr);
    }
    
    // Extract location
    const locationPatterns = [
      /(?:at|in|near)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)/,
      /(?:meet|meeting)\s+(?:at|in)\s+([^.]+)/i
    ];
    
    for (const pattern of locationPatterns) {
      const match = transcript.match(pattern);
      if (match) {
        extracted.location = match[1].trim();
        break;
      }
    }
    
    // Extract mentioned items
    const itemKeywords = [
      'gpu', 'graphics card', 'cpu', 'processor', 'ram', 'memory',
      'ssd', 'hard drive', 'motherboard', 'power supply', 'psu',
      'case', 'monitor', 'keyboard', 'mouse'
    ];
    
    const mentionedItems = itemKeywords.filter(item => 
      transcript.toLowerCase().includes(item)
    );
    
    if (mentionedItems.length > 0) {
      extracted.items = mentionedItems;
    }
    
    // Extract action keywords
    const actionKeywords = {
      'check': ['check', 'verify', 'look into', 'investigate'],
      'buy': ['buy', 'purchase', 'get', 'acquire'],
      'sell': ['sell', 'list', 'post'],
      'message': ['message', 'contact', 'reach out', 'email'],
      'meet': ['meet', 'meeting', 'see', 'inspect']
    };
    
    for (const [action, keywords] of Object.entries(actionKeywords)) {
      if (keywords.some(keyword => transcript.toLowerCase().includes(keyword))) {
        extracted.action = action;
        break;
      }
    }
    
    return extracted;
  }

  /**
   * Summarize transcript
   */
  summarizeTranscript(transcript: string): string {
    // Remove filler words
    const fillers = [
      'um', 'uh', 'like', 'you know', 'basically', 'actually',
      'literally', 'right', 'so', 'well', 'I mean'
    ];
    
    let cleaned = transcript;
    fillers.forEach(filler => {
      const regex = new RegExp(`\\b${filler}\\b`, 'gi');
      cleaned = cleaned.replace(regex, '');
    });
    
    // Clean up extra spaces
    cleaned = cleaned.replace(/\s+/g, ' ').trim();
    
    // Extract key sentences (simple approach)
    const sentences = cleaned.split(/[.!?]+/).filter(s => s.trim().length > 0);
    
    if (sentences.length <= 2) {
      return cleaned;
    }
    
    // Return first and last sentence as summary
    return `${sentences[0].trim()}. ${sentences[sentences.length - 1].trim()}.`;
  }

  /**
   * Convert audio blob to data URL
   */
  private async blobToDataUrl(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }

  /**
   * Get audio duration from blob
   */
  private async getAudioDuration(blob: Blob): Promise<number> {
    return new Promise((resolve) => {
      const audio = new Audio();
      audio.onloadedmetadata = () => {
        resolve(audio.duration);
      };
      audio.onerror = () => {
        // Fallback to estimated duration
        resolve(blob.size / 16000); // Rough estimate based on file size
      };
      audio.src = URL.createObjectURL(blob);
    });
  }

  /**
   * Check if recording is active
   */
  get isActive(): boolean {
    return this.isRecording;
  }

  /**
   * Get supported languages
   */
  static getSupportedLanguages(): Array<{ code: string; name: string }> {
    return [
      { code: 'en-US', name: 'English (US)' },
      { code: 'en-GB', name: 'English (UK)' },
      { code: 'es-ES', name: 'Spanish' },
      { code: 'fr-FR', name: 'French' },
      { code: 'de-DE', name: 'German' },
      { code: 'it-IT', name: 'Italian' },
      { code: 'pt-BR', name: 'Portuguese (Brazil)' },
      { code: 'ru-RU', name: 'Russian' },
      { code: 'zh-CN', name: 'Chinese (Mandarin)' },
      { code: 'ja-JP', name: 'Japanese' },
      { code: 'ko-KR', name: 'Korean' }
    ];
  }
}

// Export singleton instance
export const voiceTranscriber = new VoiceTranscriber();