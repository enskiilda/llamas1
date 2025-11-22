"""Utility functions for desktop management"""
from typing import Optional
from onkernel import Kernel

RESOLUTION = {"x": 1024, "y": 768}


class DesktopManager:
    def __init__(self, kernel_client: Kernel):
        self.kernel_client = kernel_client
    
    async def get_desktop(self, sandbox_id: Optional[str] = None):
        """Get or create desktop browser session"""
        try:
            if sandbox_id:
                browser = await self.kernel_client.browsers.retrieve(sandbox_id)
                return browser
            
            browser = await self.kernel_client.browsers.create(
                viewport={
                    "width": RESOLUTION["x"],
                    "height": RESOLUTION["y"]
                }
            )
            return browser
        except Exception as error:
            print(f"Error in get_desktop: {error}")
            raise
    
    async def get_desktop_url(self, sandbox_id: Optional[str] = None):
        """Get desktop browser URL and session ID"""
        try:
            desktop = await self.get_desktop(sandbox_id)
            stream_url = getattr(desktop, 'browser_live_view_url', '') or ''
            session_id = getattr(desktop, 'session_id', '')
            
            return {"streamUrl": stream_url, "id": session_id}
        except Exception as error:
            print(f"Error in get_desktop_url: {error}")
            raise
    
    async def kill_desktop(self, sandbox_id: str):
        """Terminate desktop browser session"""
        try:
            await self.kernel_client.browsers.delete_by_id(sandbox_id)
        except Exception as error:
            print(f"Error in kill_desktop: {error}")
