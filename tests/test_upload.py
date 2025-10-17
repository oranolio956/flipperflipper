import os
import pytest
import tempfile
from io import BytesIO
from unittest.mock import Mock, patch
from web_app_real import app as flask_app

class FakeSocket:
    """Mock socket for testing"""
    def __init__(self):
        self.timeout = None
        
    def settimeout(self, timeout):
        self.timeout = timeout
    
    def gettimeout(self):
        return self.timeout

class FakeStitchServer:
    """Mock Stitch server for testing"""
    def __init__(self):
        self.inf_sock = {'192.168.1.100': FakeSocket()}
        self.inf_port = {'192.168.1.100': '4040'}

@pytest.fixture
def client_logged_in(monkeypatch):
    """Setup test client with logged in session"""
    monkeypatch.setenv('STITCH_ADMIN_USER', 'admin')
    monkeypatch.setenv('STITCH_ADMIN_PASSWORD', 'SuperSecurePassw0rd!')
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for most tests
    
    with flask_app.test_client() as c:
        with c.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user'] = 'admin'
            sess['username'] = 'admin'
        yield c

@pytest.fixture
def client_with_csrf(monkeypatch):
    """Setup test client with CSRF enabled"""
    monkeypatch.setenv('STITCH_ADMIN_USER', 'admin')
    monkeypatch.setenv('STITCH_ADMIN_PASSWORD', 'SuperSecurePassw0rd!')
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = True  # Enable CSRF for this test
    
    with flask_app.test_client() as c:
        with c.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user'] = 'admin'
            sess['username'] = 'admin'
        yield c

@pytest.fixture
def mock_stitch_server():
    """Mock the Stitch server"""
    return FakeStitchServer()

def test_upload_no_file(client_logged_in):
    """Test upload endpoint with no file provided"""
    response = client_logged_in.post('/api/upload', data={
        'target_id': '192.168.1.100'
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'No file provided' in data['error']

def test_upload_no_target_id(client_logged_in):
    """Test upload endpoint with no target_id"""
    test_file = BytesIO(b'test file content')
    test_file.name = 'test.txt'
    
    response = client_logged_in.post('/api/upload', data={
        'file': (test_file, 'test.txt')
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'No target connection selected' in data['error']

def test_upload_empty_target_id(client_logged_in):
    """Test upload endpoint with empty target_id"""
    test_file = BytesIO(b'test file content')
    test_file.name = 'test.txt'
    
    response = client_logged_in.post('/api/upload', data={
        'file': (test_file, 'test.txt'),
        'target_id': ''
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'No target connection selected' in data['error']

def test_upload_whitespace_target_id(client_logged_in):
    """Test upload endpoint with whitespace-only target_id"""
    test_file = BytesIO(b'test file content')
    test_file.name = 'test.txt'
    
    response = client_logged_in.post('/api/upload', data={
        'file': (test_file, 'test.txt'),
        'target_id': '   '
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'No target connection selected' in data['error']

def test_upload_empty_filename(client_logged_in):
    """Test upload endpoint with empty filename"""
    test_file = BytesIO(b'test file content')
    test_file.name = ''
    
    response = client_logged_in.post('/api/upload', data={
        'file': (test_file, ''),
        'target_id': '192.168.1.100'
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'No file selected' in data['error']

def test_upload_file_too_large(client_logged_in):
    """Test upload endpoint with file exceeding size limit"""
    # Create a file larger than 100MB
    large_content = b'x' * (101 * 1024 * 1024)  # 101MB
    test_file = BytesIO(large_content)
    test_file.name = 'large_file.txt'
    
    response = client_logged_in.post('/api/upload', data={
        'file': (test_file, 'large_file.txt'),
        'target_id': '192.168.1.100'
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'File too large' in data['error']

@patch('web_app_real.get_stitch_server')
def test_upload_offline_target(mock_get_server, client_logged_in, mock_stitch_server):
    """Test upload to offline target"""
    mock_stitch_server.inf_sock = {}  # No active connections
    mock_get_server.return_value = mock_stitch_server
    
    test_file = BytesIO(b'test file content')
    test_file.name = 'test.txt'
    
    response = client_logged_in.post('/api/upload', data={
        'file': (test_file, 'test.txt'),
        'target_id': '192.168.1.100'
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'OFFLINE' in data['error']

@patch('web_app_real.get_stitch_server')
def test_upload_invalid_socket(mock_get_server, client_logged_in, mock_stitch_server):
    """Test upload with invalid socket object"""
    mock_stitch_server.inf_sock = {'192.168.1.100': None}
    mock_get_server.return_value = mock_stitch_server
    
    test_file = BytesIO(b'test file content')
    test_file.name = 'test.txt'
    
    response = client_logged_in.post('/api/upload', data={
        'file': (test_file, 'test.txt'),
        'target_id': '192.168.1.100'
    })
    
    assert response.status_code == 500
    data = response.get_json()
    assert 'Invalid connection state' in data['error']

@patch('web_app_real.get_stitch_server')
@patch('web_app_real.execute_real_command')
def test_upload_success(mock_execute, mock_get_server, client_logged_in, mock_stitch_server):
    """Test successful file upload"""
    mock_get_server.return_value = mock_stitch_server
    mock_execute.return_value = "✅ File uploaded successfully to target"
    
    test_content = b'test file content for upload'
    test_file = BytesIO(test_content)
    test_file.name = 'test.txt'
    
    response = client_logged_in.post('/api/upload', data={
        'file': (test_file, 'test.txt'),
        'target_id': '192.168.1.100'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert 'uploaded successfully' in data['output']
    assert data['filename'] == 'test.txt'
    
    # Verify execute_real_command was called with upload command
    mock_execute.assert_called_once()
    args = mock_execute.call_args[0]
    assert args[0].startswith('upload ')
    assert args[1] == '192.168.1.100'

@patch('web_app_real.get_stitch_server')
@patch('web_app_real.execute_real_command')
def test_upload_command_failure(mock_execute, mock_get_server, client_logged_in, mock_stitch_server):
    """Test upload when command execution fails"""
    mock_get_server.return_value = mock_stitch_server
    mock_execute.side_effect = Exception("Command execution failed")
    
    test_file = BytesIO(b'test content')
    test_file.name = 'test.txt'
    
    response = client_logged_in.post('/api/upload', data={
        'file': (test_file, 'test.txt'),
        'target_id': '192.168.1.100'
    })
    
    assert response.status_code == 500
    data = response.get_json()
    assert 'Command execution failed' in data['error']

def test_upload_various_file_types(client_logged_in):
    """Test upload with various file types and extensions"""
    file_types = [
        ('test.txt', b'text content'),
        ('image.jpg', b'\xff\xd8\xff\xe0'),  # JPEG header
        ('document.pdf', b'%PDF-1.4'),  # PDF header
        ('script.py', b'#!/usr/bin/env python3\nprint("hello")'),
        ('data.json', b'{"key": "value"}'),
        ('archive.zip', b'PK\x03\x04'),  # ZIP header
    ]
    
    for filename, content in file_types:
        test_file = BytesIO(content)
        test_file.name = filename
        
        # All should fail due to no target connection, but should pass file validation
        response = client_logged_in.post('/api/upload', data={
            'file': (test_file, filename),
            'target_id': '192.168.1.100'
        })
        
        # Should fail because target is offline, not because of file type
        assert response.status_code == 400
        data = response.get_json()
        assert 'OFFLINE' in data['error']

def test_upload_special_characters_filename(client_logged_in):
    """Test upload with special characters in filename"""
    special_filenames = [
        'file with spaces.txt',
        'file-with-dashes.txt',
        'file_with_underscores.txt',
        'file.with.dots.txt',
        'file(with)parentheses.txt',
        'file[with]brackets.txt',
    ]
    
    for filename in special_filenames:
        test_file = BytesIO(b'test content')
        test_file.name = filename
        
        response = client_logged_in.post('/api/upload', data={
            'file': (test_file, filename),
            'target_id': '192.168.1.100'
        })
        
        # Should fail due to offline target, not filename issues
        assert response.status_code == 400
        data = response.get_json()
        assert 'OFFLINE' in data['error']

@patch('web_app_real.get_stitch_server')
@patch('web_app_real.execute_real_command')
def test_upload_binary_file(mock_execute, mock_get_server, client_logged_in, mock_stitch_server):
    """Test upload of binary file"""
    mock_get_server.return_value = mock_stitch_server
    mock_execute.return_value = "Binary file uploaded successfully"
    
    # Create binary content (simulated executable)
    binary_content = bytes(range(256))  # All byte values 0-255
    test_file = BytesIO(binary_content)
    test_file.name = 'binary_file.exe'
    
    response = client_logged_in.post('/api/upload', data={
        'file': (test_file, 'binary_file.exe'),
        'target_id': '192.168.1.100'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True

def test_upload_without_login():
    """Test upload endpoint without authentication"""
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    
    with flask_app.test_client() as c:
        test_file = BytesIO(b'test content')
        test_file.name = 'test.txt'
        
        response = c.post('/api/upload', data={
            'file': (test_file, 'test.txt'),
            'target_id': '192.168.1.100'
        })
        
        # Should redirect to login
        assert response.status_code == 302

@patch('web_app_real.get_stitch_server')
@patch('web_app_real.execute_real_command')
@patch('tempfile.NamedTemporaryFile')
def test_upload_temp_file_cleanup(mock_tempfile, mock_execute, mock_get_server, client_logged_in, mock_stitch_server):
    """Test that temporary files are cleaned up after upload"""
    mock_get_server.return_value = mock_stitch_server
    mock_execute.return_value = "Upload successful"
    
    # Mock temporary file
    mock_temp = Mock()
    mock_temp.name = '/tmp/test_upload_file'
    mock_temp.__enter__ = Mock(return_value=mock_temp)
    mock_temp.__exit__ = Mock(return_value=None)
    mock_tempfile.return_value = mock_temp
    
    test_file = BytesIO(b'test content')
    test_file.name = 'test.txt'
    
    with patch('os.unlink') as mock_unlink:
        response = client_logged_in.post('/api/upload', data={
            'file': (test_file, 'test.txt'),
            'target_id': '192.168.1.100'
        })
        
        assert response.status_code == 200
        # Verify temp file cleanup was attempted
        mock_unlink.assert_called_once_with('/tmp/test_upload_file')

def test_upload_csrf_protection(client_with_csrf):
    """Test CSRF protection on upload endpoint"""
    # First get CSRF token by visiting a page
    login_response = client_with_csrf.get('/login')
    assert login_response.status_code == 200
    
    test_file = BytesIO(b'test content')
    test_file.name = 'test.txt'
    
    # Upload without CSRF token should fail
    response = client_with_csrf.post('/api/upload', data={
        'file': (test_file, 'test.txt'),
        'target_id': '192.168.1.100'
    })
    
    # Should be rejected due to CSRF
    assert response.status_code == 400

@patch('web_app_real.get_stitch_server')
@patch('web_app_real.execute_real_command')
def test_upload_metrics_tracking(mock_execute, mock_get_server, client_logged_in, mock_stitch_server):
    """Test that upload endpoint increments metrics"""
    mock_get_server.return_value = mock_stitch_server
    mock_execute.return_value = "Upload successful"
    
    with patch('web_app_real.metrics_collector') as mock_metrics:
        test_file = BytesIO(b'test content')
        test_file.name = 'test.txt'
        
        response = client_logged_in.post('/api/upload', data={
            'file': (test_file, 'test.txt'),
            'target_id': '192.168.1.100'
        })
        
        assert response.status_code == 200
        # Verify metrics were incremented
        mock_metrics.increment_counter.assert_called_with('api_requests')

def test_upload_edge_case_sizes(client_logged_in):
    """Test upload with edge case file sizes"""
    # Test exactly at the limit (100MB)
    max_size_content = b'x' * (100 * 1024 * 1024)  # Exactly 100MB
    test_file = BytesIO(max_size_content)
    test_file.name = 'max_size.txt'
    
    response = client_logged_in.post('/api/upload', data={
        'file': (test_file, 'max_size.txt'),
        'target_id': '192.168.1.100'
    })
    
    # Should fail due to offline target, not size
    assert response.status_code == 400
    data = response.get_json()
    assert 'OFFLINE' in data['error']
    
    # Test empty file
    empty_file = BytesIO(b'')
    empty_file.name = 'empty.txt'
    
    response = client_logged_in.post('/api/upload', data={
        'file': (empty_file, 'empty.txt'),
        'target_id': '192.168.1.100'
    })
    
    # Should fail due to offline target, not empty content
    assert response.status_code == 400
    data = response.get_json()
    assert 'OFFLINE' in data['error']