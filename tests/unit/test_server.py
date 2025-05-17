"""Tests for the finger server using pytest and pytest-mock."""
import asyncio
import os
import shutil
import sys
import tempfile
from pathlib import Path

# Add thumbplanserver directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "thumbplanserver"))

import pytest
from finger_server import FingerServer


@pytest.fixture()
def test_env():
    """Create test environment with temporary files."""
    # Create temporary directory structure for test files
    test_dir = tempfile.mkdtemp()
    year_dir = Path(test_dir) / "2025"
    year_dir.mkdir()
    
    # Create test project file
    test_project = year_dir / "test.project"
    test_project.write_text("Test project content")
    
    yield {
        "test_dir": test_dir,
        "year_dir": year_dir,
        "test_project": test_project,
        "server": FingerServer(test_dir)
    }
    
    # Cleanup
    shutil.rmtree(test_dir)

def test_list_projects(test_env):
    """Test listing of project files."""
    projects = test_env["server"]._list_projects()
    assert projects == ["2025/test.project"]

def test_read_project_file(test_env):
    """Test reading project file content."""
    content = test_env["server"]._read_project_file(test_env["test_project"])
    assert content == "Test project content"

def test_read_nonexistent_project(test_env):
    """Test reading non-existent project file."""
    nonexistent = test_env["year_dir"] / "nonexistent.project"
    content = test_env["server"]._read_project_file(nonexistent)
    assert content is None

def test_cache_invalidation(test_env):
    """Test that cache expires after cache_time."""
    # Read file to cache it
    content1 = test_env["server"]._read_project_file(test_env["test_project"])
    
    # Modify cache time to expire immediately
    test_env["server"].cache_time = -1
    
    # Update file content
    test_env["test_project"].write_text("Updated content")
    
    # Read again - should get updated content due to cache expiration
    content2 = test_env["server"]._read_project_file(test_env["test_project"])
    assert content1 != content2
    assert content2 == "Updated content"

@pytest.mark.asyncio
async def test_process_request_empty(test_env):
    """Test processing empty request."""
    response = await test_env["server"].process_request("")
    assert "2025/test.project" in response

@pytest.mark.asyncio
async def test_process_request_specific_project(test_env):
    """Test processing request for specific project."""
    response = await test_env["server"].process_request("2025/test.project")
    assert "Test project content" in response

@pytest.mark.asyncio
async def test_process_request_nonexistent_project(test_env):
    """Test processing request for non-existent project."""
    response = await test_env["server"].process_request("2025/nonexistent.project")
    assert "not found" in response

@pytest.mark.asyncio
async def test_process_request_invalid_format(test_env):
    """Test processing invalid request format."""
    response = await test_env["server"].process_request("invalid/format")
    assert "Invalid request" in response

@pytest.mark.asyncio
async def test_handle_client(test_env, mocker):
    """Test client connection handling."""
    # Setup mocks
    mock_reader = mocker.AsyncMock()
    mock_writer = mocker.MagicMock()
    
    mock_reader.read.return_value = b"2025/test.project"
    mock_writer.get_extra_info.return_value = ("127.0.0.1", 12345)
    mock_writer.write = mocker.MagicMock()
    mock_writer.drain = mocker.AsyncMock()
    mock_writer.close = mocker.MagicMock()
    mock_writer.wait_closed = mocker.AsyncMock()
    
    # Handle client connection
    await test_env["server"].handle_client(mock_reader, mock_writer)
    
    # Verify response was sent
    mock_writer.write.assert_called_once()
    response = mock_writer.write.call_args[0][0]
    assert b"Test project content" in response

@pytest.mark.asyncio
async def test_handle_client_error(test_env, mocker):
    """Test client connection error handling."""
    # Setup mocks to raise exception
    mock_reader = mocker.AsyncMock()
    mock_writer = mocker.MagicMock()
    
    mock_reader.read = mocker.AsyncMock(side_effect=ConnectionError)
    mock_writer.get_extra_info.return_value = ("127.0.0.1", 12345)
    mock_writer.close = mocker.MagicMock()
    mock_writer.wait_closed = mocker.AsyncMock()
    
    # Handle client connection - should not raise exception
    await test_env["server"].handle_client(mock_reader, mock_writer)
    
    # Verify connection was closed
    mock_writer.close.assert_called_once()
    mock_writer.wait_closed.assert_called_once()
