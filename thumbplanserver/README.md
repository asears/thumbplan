# Plan Server

A modern implementation of a finger daemon that serves project and plan files over the network.

## Features

- Lightweight finger protocol implementation
- Project file browsing and retrieval
- File content caching
- Year-based organization
- Simple text-based interface

## Requirements

- Python 3.9+
- asyncio library (built into Python)

## Installation

1. Clone the repository
2. Ensure you have Python 3.9 or later installed
3. No additional dependencies required

## Usage

### Starting the Server

```bash
# Run on standard finger port (requires admin/root)
python finger_server.py

# Run on alternate port
python finger_server.py --port 1079 --host 0.0.0.0
```

The server will start on port 79 by default (standard finger port) or your specified port.

### Windows Finger Service Integration

To use with Windows Finger Service:

1. Enable Windows Finger Service (optional):
   - Open Control Panel > Programs > Turn Windows features on or off
   - Enable "Simple TCPIP services (i.e. echo, daytime etc)"
   - This allows using the standard finger port (79)

2. Run the server with appropriate permissions:
   - As administrator on port 79: `python finger_server.py`
   - As regular user on alternate port: `python finger_server.py --port 1079`

### Querying Projects

Standard finger command syntax:

```bash
# List all projects (short format)
finger @hostname

# List all projects with details
finger -l @hostname

# View specific project (short format)
finger 2025/andrews.project@hostname

# View specific project with details
finger -l 2025/andrews.project@hostname
```

When using non-standard port:
```bash
# Windows (PowerShell)
finger user@hostname port_number

# Unix-like systems
finger -p port_number user@hostname
```

Or using netcat:

```bash
# List all projects
echo "" | nc localhost 7979

# View specific project
echo "2025/andrews.project" | nc localhost 7979
```

### Project File Format

Project files should be stored in the `planfiles` directory, organized by year:

```
planfiles/
  2025/
    andrews.project
    smith.project
  2024/
    archived.project
```

## Security Considerations

- The server only serves files from the planfiles directory
- Files are read-only
- Server runs on localhost by default
- Simple rate limiting implemented
- Content caching to prevent excessive file system access

## Caching

- Project file contents are cached for 5 minutes
- Cache is automatically invalidated when files are modified
- Memory-efficient caching implementation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

This project is licensed under the MIT License.
