"""
Audio Service Module

Responsible for capturing, processing, and transcribing audio from meeting platforms.
"""

import os
import logging
import asyncio
import numpy as np
import sounddevice as sd
import webrtcvad
from typing import List, Dict, Any, Optional
import wave
import struct
import openai
from datetime import datetime

logger = logging.getLogger(__name__)

class AudioService:
    def __init__(self):
        self.sample_rate = 16000  # 16kHz sample rate for optimal speech recognition
        self.frame_duration = 30  # Frame duration in milliseconds
        self.buffer = []
        self.is_recording = False
        self.vad = None
        self.audio_device = None
        self.openai_client = None
        self.api_key = os.getenv("OPENAI_API_KEY")
        
    async def initialize(self):
        """Initialize audio services and connections"""
        logger.info("Initializing Audio Service")
        try:
            # Initialize Voice Activity Detection
            self.vad = webrtcvad.Vad(3)  # Aggressiveness level 3 (most aggressive)
            
            # Initialize OpenAI client for transcription
            if self.api_key:
                self.openai_client = openai.AsyncClient(api_key=self.api_key)
            else:
                logger.warning("OpenAI API key not found. Transcription service may not work.")
            
            logger.info("Audio Service initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Audio Service: {str(e)}")
            return False
    
    async def connect_to_audio_source(self, platform: str, meeting_info: Dict[str, Any] = None):
        """Connect to the audio source based on the platform"""
        try:
            if platform == "system":
                # Use system microphone as the default audio source
                self.audio_device = sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype='int16',
                    callback=self._audio_callback
                )
                self.audio_device.start()
                logger.info("Connected to system microphone")
                return True
            elif platform == "zoom":
                # Connect to Zoom API (placeholder - actual implementation would depend on Zoom SDK)
                logger.info("Connecting to Zoom audio")
                # Implement Zoom integration here
                return True
            elif platform == "teams":
                # Connect to Microsoft Teams (placeholder)
                logger.info("Connecting to Microsoft Teams audio")
                # Implement Teams integration here
                return True
            elif platform == "meet":
                # Connect to Google Meet (placeholder)
                logger.info("Connecting to Google Meet audio")
                # Implement Google Meet integration here
                return True
            else:
                logger.error(f"Unsupported platform: {platform}")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to audio source: {str(e)}")
            return False
    
    def _audio_callback(self, indata, frames, time, status):
        """Callback function for audio stream processing"""
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        # Add audio data to buffer
        self.buffer.append(indata.copy())
    
    async def capture_audio(self) -> np.ndarray:
        """Capture audio from the current source"""
        if not self.is_recording:
            self.is_recording = True
            await self.connect_to_audio_source("system")  # Default to system microphone
        
        # Wait for sufficient audio data (e.g., 2 seconds)
        await asyncio.sleep(2)
        
        # Process and return audio data
        if self.buffer:
            # Combine all buffered audio
            audio_data = np.concatenate(self.buffer)
            # Clear buffer
            self.buffer = []
            return audio_data
        
        return np.array([])
    
    def _is_speech(self, audio_segment: np.ndarray) -> bool:
        """Detect if an audio segment contains speech"""
        if self.vad is None:
            return True
        
        # Prepare audio for VAD
        raw_data = audio_segment.tobytes()
        frame_length = int(self.sample_rate * self.frame_duration / 1000)
        
        # Check for speech in each frame
        speech_frames = 0
        total_frames = 0
        
        for i in range(0, len(raw_data) - frame_length, frame_length):
            frame = raw_data[i:i+frame_length]
            if len(frame) == frame_length:
                total_frames += 1
                if self.vad.is_speech(frame, self.sample_rate):
                    speech_frames += 1
        
        # Consider it speech if at least 30% of frames contain speech
        return total_frames > 0 and (speech_frames / total_frames) >= 0.3
    
    async def transcribe_audio(self, audio_data: np.ndarray) -> Optional[str]:
        """Transcribe audio data to text"""
        if audio_data.size == 0:
            return None
        
        # Check if audio contains speech
        if not self._is_speech(audio_data):
            logger.debug("No speech detected in audio segment")
            return None
        
        try:
            if self.openai_client:
                # Save audio to a temporary file
                temp_filename = f"temp_audio_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.wav"
                with wave.open(temp_filename, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)  # 2 bytes = 16 bits
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(audio_data.tobytes())
                
                # Use OpenAI's Whisper API for transcription
                with open(temp_filename, "rb") as audio_file:
                    response = await self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                
                # Clean up temporary file
                try:
                    os.remove(temp_filename)
                except:
                    pass
                
                transcript = response.text
                if transcript:
                    logger.info(f"Transcription: {transcript}")
                    return transcript
            else:
                logger.warning("OpenAI client not initialized, cannot transcribe audio")
            
            return None
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            return None
    
    async def cleanup(self):
        """Clean up resources"""
        if self.audio_device and hasattr(self.audio_device, 'stop'):
            self.audio_device.stop()
        self.is_recording = False
        logger.info("Audio Service resources cleaned up")
