"""
Platform Manager Module

Responsible for integrating with various meeting platforms (Zoom, Google Meet, Microsoft Teams).
"""

import os
import logging
import asyncio
import json
import webbrowser
import time
from typing import Dict, Any, Optional

import aiohttp
from msal import ConfidentialClientApplication
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
try:
    from zoomus import ZoomClient
except Exception:  # pragma: no cover - optional dependency
    ZoomClient = None

from audio_capture.audio_service import AudioService

# Configure logging
logger = logging.getLogger(__name__)

class PlatformManager:
    def __init__(self, audio_service: Optional[AudioService] = None):
        self.audio_service = audio_service or AudioService()
        self.current_platform = None
        self.current_meeting_id = None
        self.platform_handlers = {
            "zoom": self._handle_zoom,
            "teams": self._handle_teams,
            "meet": self._handle_meet,
            "default": self._handle_default
        }
        self.connection_status = {
            "connected": False,
            "platform": None,
            "meeting_id": None,
            "error": None
        }

        # Credentials from environment variables
        self.zoom_api_key = os.getenv("ZOOM_API_KEY")
        self.zoom_api_secret = os.getenv("ZOOM_API_SECRET")
        self.teams_client_id = os.getenv("TEAMS_CLIENT_ID")
        self.teams_client_secret = os.getenv("TEAMS_CLIENT_SECRET")
        self.teams_tenant_id = os.getenv("TEAMS_TENANT_ID")
        self.google_credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE")
    
    async def connect_to_meeting(self, platform: str, meeting_id: str = "") -> Dict[str, Any]:
        """
        Connect to a meeting using the specified platform
        
        Args:
            platform: The platform to connect to (zoom, teams, meet, default)
            meeting_id: Optional meeting ID or URL
        
        Returns:
            Connection status dictionary
        """
        logger.info(f"Attempting to connect to {platform} meeting: {meeting_id}")
        
        # Reset status
        self.connection_status = {
            "connected": False,
            "platform": platform,
            "meeting_id": meeting_id,
            "error": None
        }
        
        # Get appropriate handler for the platform
        handler = self.platform_handlers.get(platform.lower(), self.platform_handlers["default"])
        
        try:
            # Call platform-specific handler
            success = await handler(meeting_id)
            
            if success:
                self.current_platform = platform
                self.current_meeting_id = meeting_id
                self.connection_status["connected"] = True
                logger.info(f"Successfully connected to {platform} meeting")
            else:
                self.connection_status["error"] = f"Failed to connect to {platform} meeting"
                logger.error(self.connection_status["error"])
        
        except Exception as e:
            error_msg = f"Error connecting to {platform} meeting: {str(e)}"
            self.connection_status["error"] = error_msg
            logger.error(error_msg)
        
        return self.connection_status
    
    async def disconnect(self) -> Dict[str, Any]:
        """Disconnect from the current meeting"""
        if not self.current_platform:
            logger.info("No active meeting connection to disconnect")
            return {"connected": False, "message": "No active connection"}
        
        platform = self.current_platform
        logger.info(f"Disconnecting from {platform} meeting")
        
        try:
            # Perform platform-specific cleanup
            if platform == "zoom":
                try:
                    if ZoomClient and self.zoom_api_key and self.zoom_api_secret and self.current_meeting_id:
                        client = ZoomClient(self.zoom_api_key, self.zoom_api_secret)
                        client.meeting.end(id=self.current_meeting_id)
                except Exception as exc:
                    logger.warning(f"Zoom disconnect issue: {exc}")
            elif platform == "teams":
                # There is no explicit disconnect via API; cleaning up audio
                pass
            elif platform == "meet":
                pass

            await self.audio_service.cleanup()
            
            # Reset connection state
            self.current_platform = None
            self.current_meeting_id = None
            self.connection_status = {
                "connected": False,
                "platform": None,
                "meeting_id": None,
                "error": None
            }
            
            logger.info(f"Successfully disconnected from {platform} meeting")
            return {"connected": False, "message": f"Disconnected from {platform} meeting"}
            
        except Exception as e:
            error_msg = f"Error disconnecting from {platform} meeting: {str(e)}"
            logger.error(error_msg)
            return {"connected": True, "error": error_msg}
    
    async def get_connection_status(self) -> Dict[str, Any]:
        """Get the current connection status"""
        return self.connection_status
    
    async def _handle_zoom(self, meeting_id: str) -> bool:
        """Connect to a Zoom meeting using the Zoom API."""
        if not ZoomClient or not self.zoom_api_key or not self.zoom_api_secret:
            logger.error("Zoom SDK not available or credentials missing")
            return False

        try:
            client = ZoomClient(self.zoom_api_key, self.zoom_api_secret)
            meeting_info = client.meeting.get(id=meeting_id)
            join_url = meeting_info.get("join_url") if meeting_info else None
            if not join_url:
                logger.error("Unable to retrieve Zoom meeting join URL")
                return False

            webbrowser.open(join_url)
            await self.audio_service.connect_to_audio_source("zoom", {"meeting_id": meeting_id})
            return True
        except Exception as exc:
            logger.error(f"Zoom connection failed: {exc}")
            return False
    
    async def _handle_teams(self, meeting_id: str) -> bool:
        """Connect to a Microsoft Teams meeting using Microsoft Graph."""
        if not (self.teams_client_id and self.teams_client_secret and self.teams_tenant_id):
            logger.error("Microsoft Teams credentials missing")
            return False

        try:
            app = ConfidentialClientApplication(
                self.teams_client_id,
                authority=f"https://login.microsoftonline.com/{self.teams_tenant_id}",
                client_credential=self.teams_client_secret,
            )
            token = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
            if "access_token" not in token:
                logger.error("Failed to acquire Microsoft Graph token")
                return False

            access_token = token["access_token"]
            if meeting_id.startswith("http"):
                join_url = meeting_id
            else:
                async with aiohttp.ClientSession() as session:
                    graph_url = f"https://graph.microsoft.com/v1.0/me/onlineMeetings/{meeting_id}"
                    headers = {"Authorization": f"Bearer {access_token}"}
                    async with session.get(graph_url, headers=headers) as resp:
                        if resp.status != 200:
                            logger.error(f"Graph API error {resp.status}")
                            return False
                        data = await resp.json()
                        join_url = data.get("joinUrl")

            if not join_url:
                logger.error("No join URL for Teams meeting")
                return False

            webbrowser.open(join_url)
            await self.audio_service.connect_to_audio_source("teams", {"meeting_id": meeting_id})
            return True
        except Exception as exc:
            logger.error(f"Teams connection failed: {exc}")
            return False
    
    async def _handle_meet(self, meeting_id: str) -> bool:
        """Connect to a Google Meet session using Google APIs."""
        if not self.google_credentials_file or not os.path.exists(self.google_credentials_file):
            logger.error("Google credentials file not configured")
            return False

        try:
            creds = Credentials.from_service_account_file(
                self.google_credentials_file,
                scopes=["https://www.googleapis.com/auth/calendar.readonly"],
            )
            service = build("calendar", "v3", credentials=creds)

            if meeting_id.startswith("http"):
                join_url = meeting_id
            else:
                # Attempt to fetch event info assuming meeting_id is event id
                event = service.events().get(calendarId="primary", eventId=meeting_id).execute()
                join_url = event.get("hangoutLink")

            if not join_url:
                logger.error("Could not determine Google Meet join URL")
                return False

            webbrowser.open(join_url)
            await self.audio_service.connect_to_audio_source("meet", {"meeting_id": meeting_id})
            return True
        except Exception as exc:
            logger.error(f"Google Meet connection failed: {exc}")
            return False
    
    async def _handle_default(self, meeting_id: str) -> bool:
        """
        Handle connection to default audio source (system microphone)
        
        This is used when no specific platform is selected or when
        platform integration isn't available.
        """
        logger.info("Using default audio source (system microphone)")
        
        # No special setup needed, as we'll use the system's default audio input
        
        return True
