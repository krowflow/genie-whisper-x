"""
WebSocket Server for Genie Whisper X
Bi-directional real-time communication between backend and UI
"""
import asyncio
import websockets
import json
import logging
from typing import Set

class GenieWebSocketServer:
    """WebSocket server for real-time UI communication"""
    
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.logger = logging.getLogger(__name__)
        
    async def register(self, websocket):
        """Register a new client connection"""
        self.clients.add(websocket)
        self.logger.info(f"Client connected. Total clients: {len(self.clients)}")
        
        # Send backend ready status
        await self.send_to_client(websocket, {
            "type": "status",
            "message": "Backend Ready",
            "timestamp": asyncio.get_event_loop().time()
        })
        
    async def unregister(self, websocket):
        """Remove client connection"""
        self.clients.discard(websocket)
        self.logger.info(f"Client disconnected. Total clients: {len(self.clients)}")
        
    async def send_to_client(self, websocket, data):
        """Send data to specific client"""
        try:
            await websocket.send(json.dumps(data))
        except websockets.exceptions.ConnectionClosed:
            await self.unregister(websocket)
            
    async def broadcast(self, data):
        """Broadcast data to all connected clients"""
        if self.clients:
            await asyncio.gather(
                *[self.send_to_client(client, data) for client in self.clients],
                return_exceptions=True
            )
            
    async def handle_client_message(self, websocket, message):
        """Handle incoming message from client"""
        try:
            data = json.loads(message)
            self.logger.info(f"Received from client: {data}")
            
            # Echo back for now (placeholder)
            response = {
                "type": "response",
                "original": data,
                "timestamp": asyncio.get_event_loop().time()
            }
            await self.send_to_client(websocket, response)
            
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON received: {message}")
            
    async def client_handler(self, websocket, path):
        """Handle individual client connection"""
        await self.register(websocket)
        try:
            async for message in websocket:
                await self.handle_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)
            
    async def start_server(self):
        """Start the WebSocket server"""
        self.logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        
        start_server = websockets.serve(
            self.client_handler,
            self.host,
            self.port
        )
        
        await start_server
        self.logger.info("WebSocket server started successfully")
        
    async def send_voice_status(self, is_listening: bool):
        """Send voice activity status to UI"""
        await self.broadcast({
            "type": "voice_status",
            "listening": is_listening,
            "timestamp": asyncio.get_event_loop().time()
        })
        
    async def send_transcript(self, text: str):
        """Send transcript to UI"""
        await self.broadcast({
            "type": "transcript",
            "text": text,
            "timestamp": asyncio.get_event_loop().time()
        })
        
    async def send_command_result(self, command: str, result: str):
        """Send command execution result to UI"""
        await self.broadcast({
            "type": "command_result",
            "command": command,
            "result": result,
            "timestamp": asyncio.get_event_loop().time()
        })

async def main():
    """Entry point for WebSocket server"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    server = GenieWebSocketServer()
    await server.start_server()
    
    # Keep server running
    await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())