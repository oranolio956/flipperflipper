import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Mic, 
  MicOff, 
  Play, 
  Pause, 
  Download, 
  Trash2, 
  Volume2,
  FileAudio,
  AlertCircle,
  Clock,
  Tag,
  Search
} from 'lucide-react';
import { voiceTranscriber, TranscriptionResult } from '@arbitrage/core/voice/voiceTranscriber';
import { VoiceNote } from '@arbitrage/core/types';
import WaveSurfer from 'wavesurfer.js';

interface VoiceNoteWithPlayback extends VoiceNote {
  isPlaying?: boolean;
  waveform?: WaveSurfer;
}

export const VoiceNoteRecorder: React.FC = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [liveTranscript, setLiveTranscript] = useState('');
  const [confidence, setConfidence] = useState(0);
  const [voiceNotes, setVoiceNotes] = useState<VoiceNoteWithPlayback[]>([]);
  const [selectedLanguage, setSelectedLanguage] = useState('en-US');
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [error, setError] = useState<string | null>(null);
  
  const recordingIntervalRef = useRef<NodeJS.Timeout>();
  const transcriptionCleanupRef = useRef<(() => void) | null>(null);
  const errorCleanupRef = useRef<(() => void) | null>(null);
  const waveformRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  useEffect(() => {
    loadVoiceNotes();
    return () => {
      // Cleanup on unmount
      if (transcriptionCleanupRef.current) {
        transcriptionCleanupRef.current();
      }
      if (errorCleanupRef.current) {
        errorCleanupRef.current();
      }
    };
  }, []);

  const loadVoiceNotes = async () => {
    const { voiceNotes: stored } = await chrome.storage.local.get('voiceNotes');
    if (stored) {
      setVoiceNotes(stored);
      // Initialize waveforms after component mounts
      setTimeout(() => initializeWaveforms(stored), 100);
    }
  };

  const initializeWaveforms = (notes: VoiceNoteWithPlayback[]) => {
    notes.forEach(note => {
      const container = waveformRefs.current.get(note.id);
      if (container && !note.waveform) {
        const wavesurfer = WaveSurfer.create({
          container,
          waveColor: '#4F46E5',
          progressColor: '#6366F1',
          cursorColor: '#6366F1',
          barWidth: 2,
          barRadius: 3,
          cursorWidth: 1,
          height: 60,
          barGap: 3
        });
        
        wavesurfer.load(note.audioUrl);
        note.waveform = wavesurfer;
        
        wavesurfer.on('finish', () => {
          setVoiceNotes(prev => prev.map(n => 
            n.id === note.id ? { ...n, isPlaying: false } : n
          ));
        });
      }
    });
  };

  const startRecording = async () => {
    try {
      setError(null);
      setTranscript('');
      setLiveTranscript('');
      setConfidence(0);
      
      // Set up transcription handlers
      transcriptionCleanupRef.current = voiceTranscriber.onTranscription(
        (result: TranscriptionResult) => {
          setLiveTranscript(result.text);
          setConfidence(result.confidence);
          
          if (result.isFinal) {
            setTranscript(prev => prev + ' ' + result.text);
          }
        }
      );
      
      errorCleanupRef.current = voiceTranscriber.onError((err) => {
        setError(err.message);
        stopRecording();
      });
      
      // Start recording
      await voiceTranscriber.startRecording();
      setIsRecording(true);
      
      // Start duration counter
      const startTime = Date.now();
      recordingIntervalRef.current = setInterval(() => {
        setRecordingDuration(Math.floor((Date.now() - startTime) / 1000));
      }, 1000);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to start recording');
    }
  };

  const stopRecording = async () => {
    try {
      // Stop duration counter
      if (recordingIntervalRef.current) {
        clearInterval(recordingIntervalRef.current);
      }
      
      // Stop recording
      const { audio, duration } = await voiceTranscriber.stopRecording();
      setIsRecording(false);
      setRecordingDuration(0);
      
      // Process the voice note
      const finalTranscript = transcript + ' ' + liveTranscript;
      const keyInfo = voiceTranscriber.extractKeyInfo(finalTranscript);
      const summary = voiceTranscriber.summarizeTranscript(finalTranscript);
      
      const voiceNote = await voiceTranscriber.processVoiceNote(audio, {
        transcript: finalTranscript.trim(),
        confidence,
        tags: keyInfo.items || [],
        category: keyInfo.action || 'general'
      });
      
      // Add extracted info to metadata
      (voiceNote as any).extractedInfo = keyInfo;
      (voiceNote as any).summary = summary;
      
      // Save voice note
      const updated = [...voiceNotes, voiceNote];
      await chrome.storage.local.set({ voiceNotes: updated });
      setVoiceNotes(updated);
      
      // Initialize waveform for new note
      setTimeout(() => initializeWaveforms([voiceNote]), 100);
      
      // Cleanup handlers
      if (transcriptionCleanupRef.current) {
        transcriptionCleanupRef.current();
        transcriptionCleanupRef.current = null;
      }
      if (errorCleanupRef.current) {
        errorCleanupRef.current();
        errorCleanupRef.current = null;
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to stop recording');
    }
  };

  const playPauseNote = (noteId: string) => {
    const note = voiceNotes.find(n => n.id === noteId);
    if (!note?.waveform) return;
    
    if (note.isPlaying) {
      note.waveform.pause();
    } else {
      // Pause all other notes
      voiceNotes.forEach(n => {
        if (n.id !== noteId && n.waveform && n.isPlaying) {
          n.waveform.pause();
        }
      });
      note.waveform.play();
    }
    
    setVoiceNotes(prev => prev.map(n => ({
      ...n,
      isPlaying: n.id === noteId ? !n.isPlaying : false
    })));
  };

  const deleteNote = async (noteId: string) => {
    const note = voiceNotes.find(n => n.id === noteId);
    if (note?.waveform) {
      note.waveform.destroy();
    }
    
    const updated = voiceNotes.filter(n => n.id !== noteId);
    await chrome.storage.local.set({ voiceNotes: updated });
    setVoiceNotes(updated);
  };

  const downloadNote = (note: VoiceNote) => {
    const link = document.createElement('a');
    link.href = note.audioUrl;
    link.download = `voice-note-${note.id}.webm`;
    link.click();
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const supportedLanguages = voiceTranscriber.constructor.getSupportedLanguages();

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Voice Notes</h1>
          <p className="text-muted-foreground">Record voice notes with automatic transcription</p>
        </div>
        <Select value={selectedLanguage} onValueChange={setSelectedLanguage} disabled={isRecording}>
          <SelectTrigger className="w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {supportedLanguages.map(lang => (
              <SelectItem key={lang.code} value={lang.code}>
                {lang.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="record" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="record">Record</TabsTrigger>
          <TabsTrigger value="notes">My Notes ({voiceNotes.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="record" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>New Voice Note</CardTitle>
              <CardDescription>
                Press and hold to record. Release to stop.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-col items-center space-y-4">
                <Button
                  size="lg"
                  variant={isRecording ? "destructive" : "default"}
                  className="w-32 h-32 rounded-full"
                  onMouseDown={startRecording}
                  onMouseUp={stopRecording}
                  onMouseLeave={isRecording ? stopRecording : undefined}
                  disabled={error !== null}
                >
                  {isRecording ? (
                    <MicOff className="h-12 w-12" />
                  ) : (
                    <Mic className="h-12 w-12" />
                  )}
                </Button>
                
                {isRecording && (
                  <div className="text-center space-y-2">
                    <p className="text-2xl font-mono">{formatDuration(recordingDuration)}</p>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                      <span className="text-sm text-muted-foreground">Recording...</span>
                    </div>
                  </div>
                )}
              </div>

              {(transcript || liveTranscript) && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Live Transcription</CardTitle>
                    {confidence > 0 && (
                      <Badge variant="outline">
                        Confidence: {(confidence * 100).toFixed(0)}%
                      </Badge>
                    )}
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm">
                      {transcript}
                      {liveTranscript && (
                        <span className="text-muted-foreground"> {liveTranscript}</span>
                      )}
                    </p>
                  </CardContent>
                </Card>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notes" className="space-y-4">
          {voiceNotes.length === 0 ? (
            <Card>
              <CardContent className="p-6 text-center">
                <FileAudio className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No voice notes yet. Record your first note!</p>
              </CardContent>
            </Card>
          ) : (
            <ScrollArea className="h-[600px]">
              <div className="space-y-4">
                {voiceNotes.map((note) => (
                  <Card key={note.id}>
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <div>
                          <CardTitle className="text-sm">
                            {new Date(note.createdAt).toLocaleString()}
                          </CardTitle>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge variant="outline">
                              <Clock className="h-3 w-3 mr-1" />
                              {formatDuration(Math.round(note.duration))}
                            </Badge>
                            {note.category && (
                              <Badge variant="secondary">{note.category}</Badge>
                            )}
                            {note.confidence > 0 && (
                              <Badge variant="outline">
                                {(note.confidence * 100).toFixed(0)}% accurate
                              </Badge>
                            )}
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            size="icon"
                            variant="ghost"
                            onClick={() => playPauseNote(note.id)}
                          >
                            {note.isPlaying ? (
                              <Pause className="h-4 w-4" />
                            ) : (
                              <Play className="h-4 w-4" />
                            )}
                          </Button>
                          <Button
                            size="icon"
                            variant="ghost"
                            onClick={() => downloadNote(note)}
                          >
                            <Download className="h-4 w-4" />
                          </Button>
                          <Button
                            size="icon"
                            variant="ghost"
                            onClick={() => deleteNote(note.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div
                        ref={(el) => {
                          if (el) waveformRefs.current.set(note.id, el);
                        }}
                        className="w-full"
                      />
                      
                      {note.transcript && (
                        <div className="space-y-2">
                          <p className="text-sm">{note.transcript}</p>
                          
                          {(note as any).summary && (
                            <Card>
                              <CardContent className="p-3">
                                <p className="text-xs font-medium mb-1">Summary</p>
                                <p className="text-xs text-muted-foreground">
                                  {(note as any).summary}
                                </p>
                              </CardContent>
                            </Card>
                          )}
                          
                          {(note as any).extractedInfo && Object.keys((note as any).extractedInfo).length > 0 && (
                            <Card>
                              <CardContent className="p-3">
                                <p className="text-xs font-medium mb-1">Extracted Information</p>
                                <div className="space-y-1">
                                  {(note as any).extractedInfo.price && (
                                    <p className="text-xs">
                                      <span className="text-muted-foreground">Price:</span> ${(note as any).extractedInfo.price}
                                    </p>
                                  )}
                                  {(note as any).extractedInfo.location && (
                                    <p className="text-xs">
                                      <span className="text-muted-foreground">Location:</span> {(note as any).extractedInfo.location}
                                    </p>
                                  )}
                                  {(note as any).extractedInfo.items && (
                                    <div className="flex gap-1 flex-wrap">
                                      {(note as any).extractedInfo.items.map((item: string, i: number) => (
                                        <Badge key={i} variant="secondary" className="text-xs">
                                          {item}
                                        </Badge>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              </CardContent>
                            </Card>
                          )}
                        </div>
                      )}
                      
                      {note.tags.length > 0 && (
                        <div className="flex gap-1 flex-wrap">
                          {note.tags.map((tag, i) => (
                            <Badge key={i} variant="outline" className="text-xs">
                              <Tag className="h-3 w-3 mr-1" />
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};