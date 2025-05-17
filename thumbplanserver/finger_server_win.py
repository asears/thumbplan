#!/usr/bin/env python3
"""
Finger daemon server for project and plan files
Compatible with standard finger protocol and Windows Finger Service.
"""
import argparse
import asyncio
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

FINGER_PORT = 79  # Standard finger protocol port

class FingerServer:
    def __init__(self, plan_dir: Union[str, Path]):
        """
        Initialize the finger server.
        
        Args:
            plan_dir: Directory containing project files organized by year
        """
        self.plan_dir = Path(plan_dir)
        self.cache: Dict[str, tuple[float, str]] = {}
        self.cache_time = 300  # 5 minutes cache

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle incoming finger protocol connection."""
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
        """Process finger request following standard finger protocol."""
        request = request.strip()
        
        # Parse standard finger format: [user]@host or -l [user]@host
        is_long_format = False
        if request.startswith("-l "):
            is_long_format = True
            request = request[3:].strip()
            
        # Handle standard finger protocol format
        if "@" in request:
            parts = request.split("@")
            if len(parts) != 2:
                return "Invalid request format. Use: finger [-l] [user]@host\n"
            user = parts[0].strip()
            
            # No user specified, list all projects
            if not user:
                projects = self._list_projects()
                header = "Project listing (detailed):\n" if is_long_format else "Available projects:\n"
                if is_long_format:
                    # Add extra details for -l format
                    project_details = []
                    for proj in projects:
                        year, name = proj.split("/")
                        path = self.plan_dir / year / name
                        try:
                            stats = path.stat()
                            size = stats.st_size
                            modified = datetime.datetime.fromtimestamp(stats.st_mtime)
                            project_details.append(f"{proj:<30} {size:>8} bytes  {modified}")
                        except Exception as e:
                            project_details.append(f"{proj:<30} (error reading file: {e})")
                    return header + "\n".join(project_details) + "\n"
                return header + "\n".join(projects) + "\n"
            
            # Specific project request - expect year/project format
            if "/" in user:
                year, project = user.split("/", 1)
                if year.isdigit():
                    project_path = self.plan_dir / year / project
                    content = self._read_project_file(project_path)
                    if content:
                        if is_long_format:
                            try:
                                # Add metadata for -l format
                                stats = project_path.stat()
                                header = f"Project: {project}\n"
                                header += f"Location: {year}/{project}\n"
                                header += f"Size: {stats.st_size} bytes\n"
                                header += f"Modified: {datetime.datetime.fromtimestamp(stats.st_mtime)}\n"
                                header += "\nContent:\n"
                                return header + content + "\n"
                            except Exception as e:
                                return f"Error reading project metadata: {e}\n\n{content}\n"
                        return f"Project: {project}\n\n{content}\n"
                    return f"Project {project} not found in year {year}\n"
            
        return "Usage: finger [-l] [year/project]@host\nExamples:\n" + \
               "  finger @host              - List all projects\n" + \
               "  finger -l @host           - List all projects with details\n" + \
               "  finger 2025/proj@host     - View specific project\n" + \
               "  finger -l 2025/proj@host  - View project with details\n"

async def main():
    parser = argparse.ArgumentParser(description="Finger daemon for project files")
    parser.add_argument("--host", default="127.0.0.1",
                       help="Host to bind to (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=FINGER_PORT,
                       help=f"Port to listen on (default: {FINGER_PORT}, standard finger port)")
    args = parser.parse_args()

    plan_dir = str(Path(__file__).parent.parent / "planfiles")
    server = FingerServer(plan_dir)
    
    try:
        srv = await asyncio.start_server(
            server.handle_client, args.host, args.port
        )
        
        addr = srv.sockets[0].getsockname()
        print(f"Finger daemon serving on {addr}")
        print("For access through Windows Finger Service:")
        print("1. Enable Windows Finger Service (optional):")
        print("   - Open Control Panel > Programs > Turn Windows features on or off")
        print('   - Enable "Simple TCPIP services (i.e. echo, daytime etc)"')
        print("2. Use standard finger command syntax:")
        print("   finger @hostname               - List all projects")
        print("   finger -l @hostname           - List projects with details")
        print("   finger 2025/project@hostname  - View specific project")
        
        async with srv:
            await srv.serve_forever()
    except PermissionError:
        print("Error: Cannot bind to port 79. Try:")
        print("1. Run with administrator privileges for port 79, or")
        print("2. Use an alternate port: --port 1079")
        print("\nExample with alternate port:")
        print(f"python {Path(__file__).name} --port 1079")
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == "__main__":
    asyncio.run(main())
