#!/usr/bin/env python3
"""
Finger daemon server for project and plan files
Compatible with standard finger protocol and Windows Finger Service.
"""
import asyncio
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

FINGER_PORT = 79  # Standard finger port

class FingerServer:
    def __init__(self, plan_dir: Union[str, Path]):
        """Initialize the finger server."""
        self.plan_dir = Path(plan_dir) if isinstance(plan_dir, str) else plan_dir
        self.cache: Dict[str, Tuple[float, str]] = {}
        self.cache_time = 300  # 5 minutes cache

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            data = await reader.read(1024)
            message = data.decode().strip()
            addr = writer.get_extra_info("peername")
            
            print(f"Received {message!r} from {addr!r}")
            
            response = await self.process_request(message)
            
            writer.write(response.encode())
            await writer.drain()
            
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    def _read_project_file(self, filepath: Path) -> Optional[str]:
        """Read and cache project file content."""
        now = datetime.datetime.now().timestamp()
        
        # Use string representation of path as cache key
        cache_key = str(filepath)
        if cache_key in self.cache:
            timestamp, content = self.cache[cache_key]
            if now - timestamp < self.cache_time:
                return content
        
        try:
            if filepath.exists():
                content = filepath.read_text()
                self.cache[cache_key] = (now, content)
                return content
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
        return None

    def _list_projects(self) -> List[str]:
        """List all project files."""
        projects = []
        for year_dir in self.plan_dir.glob("*"):
            if year_dir.is_dir() and year_dir.name.isdigit():
                for project_file in year_dir.glob("*.project"):
                    projects.append(f"{year_dir.name}/{project_file.name}")
        return sorted(projects)

    async def process_request(self, request: str) -> str:
        """Process finger request."""
        request = request.strip()
        
        # List all projects if no specific request
        if not request:
            projects = self._list_projects()
            return "Available projects:\n" + "\n".join(projects) + "\n"
        
        # Handle specific project request
        parts = request.split("/")
        if len(parts) == 2 and parts[0].isdigit():
            year, project = parts
            project_path = self.plan_dir / year / project
            content = self._read_project_file(project_path)
            if content:
                return f"Project: {project}\n\n{content}\n"
            return f"Project {project} not found in year {year}\n"
        
        return "Invalid request. Use: finger @hostname or finger user@hostname\n"

async def main():
    plan_dir = Path(__file__).parent.parent / "planfiles"
    server = FingerServer(plan_dir)
    
    srv = await asyncio.start_server(
        server.handle_client, "127.0.0.1", 7979
    )
    
    addr = srv.sockets[0].getsockname()
    print(f"Serving on {addr}")
    
    async with srv:
        await srv.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
