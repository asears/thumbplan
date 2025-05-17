"""Tests for the finger client using pytest and pytest-mock."""
import socket
import sys
from pathlib import Path

# Add plancli directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "plancli"))

import pytest
from finger_client import query_finger_server


@pytest.fixture
def test_config():
    """Test configuration fixture."""
    return {
        "host": "localhost",
        "port": 1079,
        "query": "2025/test.project"
    }

def test_query_finger_server_success(mocker, test_config):
    """Test successful query to finger server."""
    # Mock the socket context manager
    mock_sock = mocker.MagicMock()
    mock_socket = mocker.patch("socket.socket")
    mock_socket.return_value.__enter__.return_value = mock_sock
    
    # Mock successful response
    mock_sock.recv.side_effect = [b"Test response", b""]
    
    response = query_finger_server(test_config["host"], test_config["query"], test_config["port"])
    
    # Verify socket operations
    mock_sock.connect.assert_called_once_with((test_config["host"], test_config["port"]))
    mock_sock.send.assert_called_once_with(f"{test_config['query']}@{test_config['host']}\r\n".encode())
    assert response == "Test response"

def test_query_finger_server_with_long_format(mocker, test_config):
    """Test query with long format flag."""
    mock_sock = mocker.MagicMock()
    mock_socket = mocker.patch("socket.socket")
    mock_socket.return_value.__enter__.return_value = mock_sock
    mock_sock.recv.side_effect = [b"Detailed response", b""]
    
    response = query_finger_server(test_config["host"], test_config["query"], test_config["port"], long_format=True)
    
    expected_query = f"-l {test_config['query']}@{test_config['host']}\r\n"
    mock_sock.send.assert_called_once_with(expected_query.encode())
    assert response == "Detailed response"

def test_query_finger_server_connection_refused(mocker, test_config):
    """Test handling of connection refused error."""
    mock_socket = mocker.patch("socket.socket")
    mock_socket.return_value.__enter__.side_effect = ConnectionRefusedError
    
    response = query_finger_server(test_config["host"], test_config["query"], test_config["port"])
    
    assert response is None

def test_query_finger_server_hostname_resolution_error(mocker, test_config):
    """Test handling of hostname resolution error."""
    mock_socket = mocker.patch("socket.socket")
    mock_socket.return_value.__enter__.side_effect = socket.gaierror
    
    response = query_finger_server("nonexistent.host", test_config["query"], test_config["port"])
    
    assert response is None

def test_query_finger_server_empty_query(mocker, test_config):
    """Test query with no specific project requested."""
    mock_sock = mocker.MagicMock()
    mock_socket = mocker.patch("socket.socket")
    mock_socket.return_value.__enter__.return_value = mock_sock
    mock_sock.recv.side_effect = [b"Project list", b""]
    
    response = query_finger_server(test_config["host"], "", test_config["port"])
    
    expected_query = f"@{test_config['host']}\r\n"
    mock_sock.send.assert_called_once_with(expected_query.encode())
    assert response == "Project list"

def test_query_finger_server_connection_timeout(mocker, test_config):
    """Test handling of connection timeout."""
    mock_socket = mocker.patch("socket.socket")
    mock_socket.return_value.__enter__.side_effect = socket.timeout
    
    response = query_finger_server(test_config["host"], test_config["query"], test_config["port"])
    
    assert response is None
