import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Grid,
  Paper,
  IconButton,
  Typography,
  Chip,
  Tooltip,
  AppBar,
  Toolbar,
  Badge,
  Drawer,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Button,
} from '@mui/material';
import {
  Mic,
  MicOff,
  Videocam,
  VideocamOff,
  ScreenShare,
  StopScreenShare,
  Chat as ChatIcon,
  People,
  Code,
  Settings,
  CallEnd,
  FiberManualRecord,
  PlayArrow,
  Stop,
  BugReport,
  CheckCircle,
  Warning,
  Error as ErrorIcon,
} from '@mui/icons-material';
import MonacoEditor from '@monaco-editor/react';
import { motion, AnimatePresence } from 'framer-motion';

interface MeetingRoomProps {
  meetingId: string;
  userName: string;
  localStream: MediaStream | null;
  remoteStreams: Map<string, MediaStream>;
}

const MeetingRoom: React.FC<MeetingRoomProps> = ({
  meetingId,
  userName,
  localStream,
  remoteStreams,
}) => {
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOff, setIsVideoOff] = useState(false);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [participantsOpen, setParticipantsOpen] = useState(false);
  const [code, setCode] = useState(`// Welcome to InterviewHub Pro
// Problem: Implement a function to find the nth Fibonacci number

function fibonacci(n) {
  // Your code here
  
}

// Test cases
console.log(fibonacci(0));  // Expected: 0
console.log(fibonacci(1));  // Expected: 1
console.log(fibonacci(10)); // Expected: 55`);
  const [output, setOutput] = useState('');
  const [testResults, setTestResults] = useState<Array<{
    name: string;
    passed: boolean;
    message: string;
  }>>([]);
  const [elapsedTime, setElapsedTime] = useState(0);

  const localVideoRef = useRef<HTMLVideoElement>(null);
  const remoteVideoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    // Attach local stream to video element
    if (localVideoRef.current && localStream) {
      localVideoRef.current.srcObject = localStream;
    }
  }, [localStream]);

  useEffect(() => {
    // Timer for meeting duration
    const timer = setInterval(() => {
      setElapsedTime((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes
      .toString()
      .padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleMicToggle = () => {
    if (localStream) {
      const audioTrack = localStream.getAudioTracks()[0];
      if (audioTrack) {
        audioTrack.enabled = !audioTrack.enabled;
        setIsMuted(!audioTrack.enabled);
      }
    }
  };

  const handleVideoToggle = () => {
    if (localStream) {
      const videoTrack = localStream.getVideoTracks()[0];
      if (videoTrack) {
        videoTrack.enabled = !videoTrack.enabled;
        setIsVideoOff(!videoTrack.enabled);
      }
    }
  };

  const handleScreenShare = async () => {
    if (!isScreenSharing) {
      try {
        const screenStream = await navigator.mediaDevices.getDisplayMedia({
          video: true,
          audio: false,
        });
        // Handle screen share stream
        setIsScreenSharing(true);
      } catch (error) {
        console.error('Error sharing screen:', error);
      }
    } else {
      // Stop screen sharing
      setIsScreenSharing(false);
    }
  };

  const handleRunCode = () => {
    try {
      // In production, this would be sent to a sandboxed environment
      const result = eval(code);
      setOutput(`Output: ${result}`);
      
      // Mock test results
      setTestResults([
        { name: 'Test 1: fibonacci(0)', passed: true, message: 'Passed' },
        { name: 'Test 2: fibonacci(1)', passed: true, message: 'Passed' },
        { name: 'Test 3: fibonacci(10)', passed: false, message: 'Expected 55, got undefined' },
      ]);
    } catch (error: any) {
      setOutput(`Error: ${error.message}`);
    }
  };

  const handleEndCall = () => {
    // Clean up and return to lobby
    window.location.reload();
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', bgcolor: '#0A0A0A' }}>
      {/* Header Bar */}
      <AppBar position="static" sx={{ bgcolor: '#1A1A1A' }}>
        <Toolbar variant="dense">
          <Typography variant="h6" sx={{ flexGrow: 0, mr: 3, fontWeight: 600 }}>
            InterviewHub Pro
          </Typography>
          <Chip
            label={`Room: ${meetingId}`}
            size="small"
            sx={{ mr: 2, bgcolor: '#2A2A2A' }}
          />
          <Chip
            label={formatTime(elapsedTime)}
            size="small"
            icon={<FiberManualRecord sx={{ color: 'red !important' }} />}
            sx={{ mr: 2, bgcolor: isRecording ? '#FF4444' : '#2A2A2A' }}
          />
          <Box sx={{ flexGrow: 1 }} />
          <Tooltip title="Participants">
            <IconButton color="inherit" onClick={() => setParticipantsOpen(true)}>
              <Badge badgeContent={2} color="primary">
                <People />
              </Badge>
            </IconButton>
          </Tooltip>
          <Tooltip title="Chat">
            <IconButton color="inherit" onClick={() => setChatOpen(true)}>
              <Badge badgeContent={3} color="error">
                <ChatIcon />
              </Badge>
            </IconButton>
          </Tooltip>
          <Tooltip title="Settings">
            <IconButton color="inherit">
              <Settings />
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>

      {/* Main Content Area */}
      <Box sx={{ flex: 1, display: 'flex', p: 2, gap: 2 }}>
        {/* Left Panel - Video Feeds */}
        <Box sx={{ width: 350, display: 'flex', flexDirection: 'column', gap: 2 }}>
          {/* Local Video */}
          <Paper
            elevation={3}
            sx={{
              position: 'relative',
              borderRadius: 2,
              overflow: 'hidden',
              bgcolor: '#1A1A1A',
              height: 260,
            }}
          >
            <video
              ref={localVideoRef}
              autoPlay
              muted
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
              }}
            />
            <Box
              sx={{
                position: 'absolute',
                bottom: 8,
                left: 8,
                display: 'flex',
                alignItems: 'center',
                gap: 1,
              }}
            >
              <Chip
                label={userName}
                size="small"
                sx={{
                  bgcolor: 'rgba(0, 0, 0, 0.7)',
                  color: 'white',
                }}
              />
              {isMuted && <MicOff sx={{ color: 'red', fontSize: 18 }} />}
            </Box>
          </Paper>

          {/* Remote Video */}
          <Paper
            elevation={3}
            sx={{
              position: 'relative',
              borderRadius: 2,
              overflow: 'hidden',
              bgcolor: '#1A1A1A',
              height: 260,
            }}
          >
            <video
              ref={remoteVideoRef}
              autoPlay
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
              }}
            />
            <Box
              sx={{
                position: 'absolute',
                bottom: 8,
                left: 8,
                display: 'flex',
                alignItems: 'center',
                gap: 1,
              }}
            >
              <Chip
                label="Candidate"
                size="small"
                sx={{
                  bgcolor: 'rgba(0, 0, 0, 0.7)',
                  color: 'white',
                }}
              />
            </Box>
          </Paper>

          {/* Problem Description */}
          <Paper
            elevation={3}
            sx={{
              flex: 1,
              p: 2,
              borderRadius: 2,
              bgcolor: '#1A1A1A',
              overflow: 'auto',
            }}
          >
            <Typography variant="h6" gutterBottom>
              Problem: Fibonacci Sequence
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Implement a function that returns the nth number in the Fibonacci sequence.
              The sequence starts with 0 and 1, and each subsequent number is the sum of
              the previous two.
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Examples:
              </Typography>
              <Typography variant="body2" component="pre" sx={{ fontFamily: 'monospace' }}>
                {`fibonacci(0) → 0
fibonacci(1) → 1
fibonacci(10) → 55`}
              </Typography>
            </Box>
          </Paper>
        </Box>

        {/* Center Panel - Code Editor */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Paper
            elevation={3}
            sx={{
              flex: 1,
              borderRadius: 2,
              overflow: 'hidden',
              bgcolor: '#1A1A1A',
            }}
          >
            <MonacoEditor
              height="100%"
              defaultLanguage="javascript"
              theme="vs-dark"
              value={code}
              onChange={(value) => setCode(value || '')}
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                fontFamily: 'JetBrains Mono, monospace',
                lineNumbers: 'on',
                scrollBeyondLastLine: false,
                automaticLayout: true,
                tabSize: 2,
              }}
            />
          </Paper>

          {/* Output Panel */}
          <Paper
            elevation={3}
            sx={{
              height: 200,
              borderRadius: 2,
              bgcolor: '#1A1A1A',
              p: 2,
              overflow: 'auto',
            }}
          >
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="subtitle1">Output</Typography>
              <Box>
                <IconButton size="small" color="primary" onClick={handleRunCode}>
                  <PlayArrow />
                </IconButton>
                <IconButton size="small" color="secondary">
                  <BugReport />
                </IconButton>
              </Box>
            </Box>
            <Divider sx={{ mb: 1 }} />
            {output && (
              <Typography
                variant="body2"
                component="pre"
                sx={{ fontFamily: 'monospace', color: '#4CAF50' }}
              >
                {output}
              </Typography>
            )}
            {testResults.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Test Results:
                </Typography>
                {testResults.map((test, index) => (
                  <Box key={index} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                    {test.passed ? (
                      <CheckCircle sx={{ color: '#4CAF50', fontSize: 16 }} />
                    ) : (
                      <ErrorIcon sx={{ color: '#FF5252', fontSize: 16 }} />
                    )}
                    <Typography variant="body2">
                      {test.name}: {test.message}
                    </Typography>
                  </Box>
                ))}
              </Box>
            )}
          </Paper>
        </Box>
      </Box>

      {/* Bottom Controls */}
      <Paper
        elevation={3}
        sx={{
          p: 2,
          bgcolor: '#1A1A1A',
          borderRadius: 0,
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2 }}>
          <Tooltip title={isMuted ? 'Unmute' : 'Mute'}>
            <IconButton
              onClick={handleMicToggle}
              sx={{
                bgcolor: isMuted ? '#FF5252' : '#2A2A2A',
                '&:hover': { bgcolor: isMuted ? '#FF7070' : '#3A3A3A' },
              }}
            >
              {isMuted ? <MicOff /> : <Mic />}
            </IconButton>
          </Tooltip>

          <Tooltip title={isVideoOff ? 'Turn On Video' : 'Turn Off Video'}>
            <IconButton
              onClick={handleVideoToggle}
              sx={{
                bgcolor: isVideoOff ? '#FF5252' : '#2A2A2A',
                '&:hover': { bgcolor: isVideoOff ? '#FF7070' : '#3A3A3A' },
              }}
            >
              {isVideoOff ? <VideocamOff /> : <Videocam />}
            </IconButton>
          </Tooltip>

          <Tooltip title={isScreenSharing ? 'Stop Sharing' : 'Share Screen'}>
            <IconButton
              onClick={handleScreenShare}
              sx={{
                bgcolor: isScreenSharing ? '#4CAF50' : '#2A2A2A',
                '&:hover': { bgcolor: isScreenSharing ? '#66BB6A' : '#3A3A3A' },
              }}
            >
              {isScreenSharing ? <StopScreenShare /> : <ScreenShare />}
            </IconButton>
          </Tooltip>

          <Tooltip title={isRecording ? 'Stop Recording' : 'Start Recording'}>
            <IconButton
              onClick={() => setIsRecording(!isRecording)}
              sx={{
                bgcolor: isRecording ? '#FF5252' : '#2A2A2A',
                '&:hover': { bgcolor: isRecording ? '#FF7070' : '#3A3A3A' },
              }}
            >
              <FiberManualRecord />
            </IconButton>
          </Tooltip>

          <Box sx={{ mx: 2 }} />

          <Button
            variant="contained"
            color="error"
            startIcon={<CallEnd />}
            onClick={handleEndCall}
            sx={{
              px: 3,
              bgcolor: '#FF5252',
              '&:hover': { bgcolor: '#FF7070' },
            }}
          >
            End Call
          </Button>
        </Box>
      </Paper>

      {/* Chat Drawer */}
      <Drawer
        anchor="right"
        open={chatOpen}
        onClose={() => setChatOpen(false)}
        sx={{
          '& .MuiDrawer-paper': {
            width: 350,
            bgcolor: '#1A1A1A',
          },
        }}
      >
        <Box sx={{ p: 2 }}>
          <Typography variant="h6">Chat</Typography>
          {/* Chat implementation */}
        </Box>
      </Drawer>

      {/* Participants Drawer */}
      <Drawer
        anchor="right"
        open={participantsOpen}
        onClose={() => setParticipantsOpen(false)}
        sx={{
          '& .MuiDrawer-paper': {
            width: 350,
            bgcolor: '#1A1A1A',
          },
        }}
      >
        <Box sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Participants (2)
          </Typography>
          <List>
            <ListItem>
              <ListItemIcon>
                <People />
              </ListItemIcon>
              <ListItemText primary={userName} secondary="Host" />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <People />
              </ListItemIcon>
              <ListItemText primary="Candidate" secondary="Participant" />
            </ListItem>
          </List>
        </Box>
      </Drawer>
    </Box>
  );
};

export default MeetingRoom;