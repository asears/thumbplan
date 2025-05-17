# Plan CLI

A command-line interface for accessing and managing plan files, including a finger protocol client.

## Features

- Finger protocol client to access remote plan files
- Supports standard finger protocol syntax
- Compatible with Windows Finger Service
- Long format output with detailed information
- Configurable port for non-standard setups

## Installation

No additional dependencies required. Just ensure you have Python 3.9 or later installed.

## Usage

The `finger_client.py` script provides access to plan files through the finger protocol.

### Basic Usage

```bash
# List all projects
python finger_client.py localhost

# List projects with details
python finger_client.py -l localhost

# View specific project
python finger_client.py localhost 2025/andrews.project

# View project with details
python finger_client.py -l localhost 2025/andrews.project
```

### Port Configuration

By default, the client uses the standard finger port (79). For non-standard setups:

```bash
# Use alternate port
python finger_client.py --port 1079 localhost

# View project on alternate port
python finger_client.py --port 1079 localhost 2025/andrews.project
```

### Verbose Output

Enable debug logging with the `-v` flag:

```bash
python finger_client.py -v localhost
```

### Windows Finger Service

When using with Windows Finger Service:

1. The server must be running on port 79 (requires admin privileges)
2. Use standard Windows finger command syntax:
   ```cmd
   finger @server               # List all projects
   finger -l @server           # List with details
   finger 2025/project@server  # View specific project
   ```

3. For non-standard ports with Windows finger command:
   ```cmd
   finger user@server port_number
   ```

### Project File Format

Project files are organized by year in the `planfiles` directory:

```
planfiles/
  2025/
    andrews.project      # Individual project file
    andrews_20250517.plan  # Daily plan file
  2024/
    archived.project
```

## Examples of Output

1. Listing all projects (short format):
   ```
   Available projects:
   2025/andrews.project
   2025/andrews_20250517.plan
   2024/archived.project
   ```

2. Viewing project details (long format):
   ```
   Project: andrews.project
   Location: 2025/andrews.project
   Size: 1234 bytes
   Modified: 2025-05-17 10:30:45

   Content:
   - Building .github/instructions
   - Automating new projects with Copilot
   - Implementing finger protocol
   ```

## Error Handling

The client provides informative error messages for common issues:

- Connection refused (server not running)
- Invalid hostname or port
- Permission denied (port 79 access)
- Network connectivity issues

Exit codes:
- 0: Success
- 1: Error (connection failed, invalid hostname, etc.)

## Security Notes

- The finger protocol sends data in plaintext
- Use within trusted networks only
- Consider using SSH tunneling for remote access
- Windows Finger Service requires admin privileges for port 79

## Best Practices

1. For security:
   - Use non-standard ports (e.g., 1079) when possible
   - Limit server access to trusted networks
   - Keep sensitive information out of plan files

2. For reliability:
   - Use verbose mode (-v) to diagnose connection issues
   - Ensure proper file permissions
   - Maintain consistent file naming conventions

## License

This project is licensed under the MIT License.