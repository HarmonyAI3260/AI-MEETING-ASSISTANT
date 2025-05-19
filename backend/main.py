#!/usr/bin/env python3
"""
AI Meeting Assistant - Main Application
"""

import os
import logging
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import modules
from audio_capture.audio_service import AudioService
from question_detection.question_detector import QuestionDetector
from answer_generation.answer_generator import AnswerGenerator
from platform_integration.platform_manager import PlatformManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="AI Meeting Assistant")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
audio_service = AudioService()
question_detector = QuestionDetector()
answer_generator = AnswerGenerator()
platform_manager = PlatformManager()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)


manager = ConnectionManager()

@app.get("/")
async def root():
    return {"message": "AI Meeting Assistant API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Start meeting assistant process
        async def process_audio_stream():
            conversation_history = []
            
            while True:
                # Get audio from meeting
                audio_data = await audio_service.capture_audio()
                
                # Transcribe audio
                transcript = await audio_service.transcribe_audio(audio_data)
                if transcript:
                    # Add to conversation history
                    conversation_history.append(transcript)
                    # Keep conversation history to a manageable size (last 10 minutes approx)
                    if len(conversation_history) > 30:  # Assuming ~20s chunks
                        conversation_history.pop(0)
                    
                    # Detect questions
                    detected_question = question_detector.detect_question(transcript)
                    if detected_question:
                        # Generate answer
                        answer = await answer_generator.generate_answer(
                            question=detected_question,
                            context=conversation_history
                        )
                        
                        # Send answer to frontend
                        await manager.broadcast({
                            "type": "answer",
                            "question": detected_question,
                            "answer": answer,
                            "timestamp": answer_generator.get_timestamp()
                        })
                
                # Short pause to prevent CPU overload
                await asyncio.sleep(0.1)
        
        # Start audio processing task
        audio_task = asyncio.create_task(process_audio_stream())
        
        # Listen for messages from frontend
        while True:
            data = await websocket.receive_json()
            if data.get("action") == "start_meeting":
                platform = data.get("platform", "default")
                meeting_id = data.get("meeting_id", "")
                await platform_manager.connect_to_meeting(platform, meeting_id)
            elif data.get("action") == "stop_meeting":
                await platform_manager.disconnect()
            # Add other actions as needed
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error in websocket: {str(e)}")
        manager.disconnect(websocket)
    finally:
        # Cancel any running tasks
        if 'audio_task' in locals() and not audio_task.done():
            audio_task.cancel()
        
@app.on_event("startup")
async def startup_event():
    logger.info("Starting AI Meeting Assistant")
    # Initialize components
    await audio_service.initialize()
    await answer_generator.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down AI Meeting Assistant")
    # Cleanup
    await audio_service.cleanup()
    await answer_generator.cleanup()
    await platform_manager.disconnect()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
