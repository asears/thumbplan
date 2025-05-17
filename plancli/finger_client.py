#!/usr/bin/env python3
"""Finger client for accessing plan files from the thumbplanserver."""

import argparse
import logging
import socket
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

DEFAULT_PORT = 79

def query_finger_server(
    host: str,
    query: str = "",
    port: int = DEFAULT_PORT,
    long_format: bool = False
) -> str | None:
    """
    Query the finger server for plan information.
    
    Args:
        host: Hostname or IP of the finger server
        query: Query string (e.g., "2025/andrews.project")
        port: Port number (default: 79, standard finger port)
        long_format: Whether to use long format (-l flag)
        
    Returns:
        Server response as string, or None if error occurred
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            
            # Format query according to finger protocol
            if long_format:
                query = f"-l {query}"
            query = f"{query}@{host}\r\n"
            
            s.send(query.encode())
            
            # Receive response
            chunks = []
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
            
            return b"".join(chunks).decode()
    except ConnectionRefusedError:
        logging.error(f"Connection refused to {host}:{port}")
        logging.error("Make sure the finger server is running and the port is correct")
    except socket.gaierror:
        logging.error(f"Could not resolve hostname {host}")
    except Exception as e:
        logging.error(f"Error querying finger server: {e}")
    return None

def main():
    """Run the finger client main entry point."""
    parser = argparse.ArgumentParser(
        description="Finger client for plan files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  List all projects:
    finger_client.py localhost
    finger_client.py --port 1079 localhost
        
  List projects with details:
    finger_client.py -l localhost
        
  View specific project:
    finger_client.py localhost 2025/andrews.project
    finger_client.py -l localhost 2025/andrews.project
"""
    )
    
    parser.add_argument("host",
                       help="Hostname or IP address of the finger server")
    parser.add_argument("query", nargs="?", default="",
                       help="Optional query (e.g., 2025/andrews.project)")
    parser.add_argument("-l", "--long", action="store_true",
                       help="Use long format (more details)")
    parser.add_argument("-p", "--port", type=int, default=DEFAULT_PORT,
                       help=f"Port number (default: {DEFAULT_PORT})")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Set logging level based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logging.debug(f"Connecting to {args.host}:{args.port}")
    if args.query:
        logging.debug(f"Query: {args.query}")
    
    response = query_finger_server(
        args.host,
        args.query,
        args.port,
        args.long
    )
    
    if response:
        sys.stdout.write(response.rstrip() + "\n")
        return 0
    return 1

if __name__ == "__main__":
    sys.exit(main())
