import React, { useState, useEffect } from 'react';

interface BackendStatus {
  connected: boolean;
  message: string;
  timestamp?: number;
}

interface WebSocketMessage {
  type: string;
  message?: string;
  listening?: boolean;
  text?: string;
  command?: string;
  result?: string;
  timestamp: number;
}

const App: React.FC = () => {
  const [backendStatus, setBackendStatus] = useState<BackendStatus>({
    connected: false,
    message: 'Connecting to backend...'
  });
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [transcript, setTranscript] = useState<string>('');
  const [isListening, setIsListening] = useState<boolean>(false);

  useEffect(() => {
    // Connect to WebSocket server
    const websocket = new WebSocket('ws://localhost:8765');
    
    websocket.onopen = () => {
      console.log('Connected to Genie backend');
      setBackendStatus({
        connected: true,
        message: 'Connected to backend'
      });
    };
    
    websocket.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);
        
        switch (data.type) {
          case 'status':
            setBackendStatus({
              connected: true,
              message: data.message || 'Backend Ready',
              timestamp: data.timestamp
            });
            break;
            
          case 'voice_status':
            setIsListening(data.listening || false);
            break;
            
          case 'transcript':
            setTranscript(data.text || '');
            break;
            
          case 'command_result':
            console.log(`Command executed: ${data.command} -> ${data.result}`);
            break;
            
          default:
            console.log('Unknown message type:', data);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    websocket.onclose = () => {
      console.log('Disconnected from backend');
      setBackendStatus({
        connected: false,
        message: 'Disconnected from backend'
      });
    };
    
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setBackendStatus({
        connected: false,
        message: 'Connection error'
      });
    };
    
    setWs(websocket);
    
    // Cleanup on unmount
    return () => {
      websocket.close();
    };
  }, []);

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>🧞 Genie Whisper X</h1>
      
      {/* Backend Status */}
      <div style={{ 
        padding: '10px', 
        marginBottom: '20px',
        backgroundColor: backendStatus.connected ? '#d4edda' : '#f8d7da',
        border: `1px solid ${backendStatus.connected ? '#c3e6cb' : '#f5c6cb'}`,
        borderRadius: '5px'
      }}>
        <strong>Status:</strong> {backendStatus.message}
        {backendStatus.connected && (
          <span style={{ color: '#28a745', marginLeft: '10px' }}>✓</span>
        )}
      </div>

      {/* Voice Activity Indicator */}
      <div style={{ marginBottom: '20px' }}>
        <h3>🎤 Voice Activity</h3>
        <div style={{
          padding: '10px',
          backgroundColor: isListening ? '#fff3cd' : '#f8f9fa',
          border: `1px solid ${isListening ? '#ffeaa7' : '#e9ecef'}`,
          borderRadius: '5px'
        }}>
          {isListening ? '🔴 Listening...' : '⚪ Idle'}
        </div>
      </div>

      {/* Transcript Panel */}
      <div style={{ marginBottom: '20px' }}>
        <h3>📝 Transcript</h3>
        <div style={{
          padding: '10px',
          minHeight: '100px',
          backgroundColor: '#f8f9fa',
          border: '1px solid #e9ecef',
          borderRadius: '5px',
          whiteSpace: 'pre-wrap'
        }}>
          {transcript || 'No transcript yet...'}
        </div>
      </div>

      {/* Waveform Placeholder */}
      <div style={{ marginBottom: '20px' }}>
        <h3>🌊 Waveform</h3>
        <div style={{
          height: '100px',
          backgroundColor: '#000',
          border: '1px solid #ccc',
          borderRadius: '5px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff'
        }}>
          [Waveform Visualization - Coming Soon]
        </div>
      </div>

      {/* Action Console */}
      <div>
        <h3>⚡ Action Console</h3>
        <div style={{
          padding: '10px',
          minHeight: '80px',
          backgroundColor: '#f8f9fa',
          border: '1px solid #e9ecef',
          borderRadius: '5px'
        }}>
          Command execution results will appear here...
        </div>
      </div>
    </div>
  );
};

export default App;