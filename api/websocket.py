import asyncio
import json
import logging
import datetime
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List

logger = logging.getLogger("websocket")

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.logger = logging.getLogger("websocket")

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        self.logger.info(f"New connection in session {session_id}")

    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        self.logger.info(f"Connection closed in session {session_id}")

    async def send_message(self, message: dict, session_id: str):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                    self.logger.debug(f"Sent message to session {session_id}: {message.get('type')}")
                except Exception as e:
                    self.logger.error(f"Error sending message to session {session_id}: {str(e)}")
        else:
            self.logger.warning(f"No active connections for session {session_id}")

    async def broadcast(self, message: dict):
        for session_id in self.active_connections:
            await self.send_message(message, session_id)

connection_manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await connection_manager.connect(websocket, session_id)
    try:
        # Send initial connection success message
        await connection_manager.send_message({
            "type": "connection_established",
            "session_id": session_id,
            "timestamp": datetime.datetime.now().isoformat()
        }, session_id)
        
        while True:
            try:
                # Set a reasonable timeout for receiving messages
                data = await asyncio.wait_for(websocket.receive_text(), timeout=300)  # 5 minute timeout
                
                try:
                    message = json.loads(data)
                    logger.info(f"Received message: {message}")
                    
                    # Process message based on type
                    if message.get("type") == "chat":
                        # Handle chat message
                        await connection_manager.send_message({
                            "type": "received",
                            "message_id": message.get("id", ""),
                            "timestamp": datetime.datetime.now().isoformat()
                        }, session_id)
                        
                        # Process the message with the Agent
                        try:
                            # Import here to avoid circular imports
                            from agent.base import Agent
                            from agent.thinking import ThinkingProcess
                            
                            # Create thinking process
                            thinking_process = ThinkingProcess(session_id, connection_manager)
                            
                            # Create an agent instance
                            agent = Agent(
                                session_id=session_id,
                                websocket_manager=connection_manager,
                                thinking_process=thinking_process
                            )
                            
                            # Process the message
                            await agent.process_message(message)
                            
                        except Exception as e:
                            logger.error(f"Error processing message: {str(e)}")
                            # Send error message to client
                            await connection_manager.send_message({
                                "type": "chat_message",
                                "message": {
                                    "role": "assistant",
                                    "content": f"I encountered an error processing your message: {str(e)}",
                                    "timestamp": datetime.datetime.now().isoformat(),
                                    "id": f"error-{datetime.datetime.now().timestamp()}"
                                }
                            }, session_id)
                            
                    elif message.get("type") == "ping":
                        # Respond to ping with pong to keep connection alive
                        await connection_manager.send_message({
                            "type": "pong",
                            "timestamp": datetime.datetime.now().isoformat()
                        }, session_id)
                        
                    elif message.get("type") == "command":
                        # Handle command
                        logger.info(f"Received command: {message}")
                        
                    else:
                        # Unknown message type
                        logger.warning(f"Received unknown message type: {message.get('type')}")
                        
                except json.JSONDecodeError:
                    logger.error(f"Received invalid JSON: {data}")
                    
            except asyncio.TimeoutError:
                # Send a ping to check if client is still connected
                try:
                    await connection_manager.send_message({
                        "type": "ping",
                        "timestamp": datetime.datetime.now().isoformat()
                    }, session_id)
                except Exception:
                    # Client probably disconnected
                    break
            except WebSocketDisconnect:
                connection_manager.disconnect(websocket, session_id)
                break
            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}")
                # Try to notify client of error
                try:
                    await connection_manager.send_message({
                        "type": "error",
                        "error": str(e),
                        "timestamp": datetime.datetime.now().isoformat()
                    }, session_id)
                except:
                    pass
                
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        connection_manager.disconnect(websocket, session_id)
