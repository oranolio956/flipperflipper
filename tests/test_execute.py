import os
import pytest
import base64
import tempfile
import configparser
from unittest.mock import Mock, patch, MagicMock
from web_app_real import app as flask_app

class FakeSocket:
    """Mock socket for testing"""
    def __init__(self):
        self.data_queue = []
        self.timeout = None
        
    def recv(self, size):
        if self.data_queue:
            return self.data_queue.pop(0)
        return b''
    
    def settimeout(self, timeout):
        self.timeout = timeout
    
    def gettimeout(self):
        return self.timeout

class FakeStitchServer:
    """Mock Stitch server for testing"""
    def __init__(self):
        self.inf_sock = {'192.168.1.100': FakeSocket()}
        self.inf_port = {'192.168.1.100': '4040'}
        self.listen_port = 4040
        self.server_thread = Mock()
        
    def receive(self, sock, encryption=False):
        if encryption:
            return base64.b64encode(b'stitch_shell').decode()
        else:
            # Return handshake confirmation and AES ID
            return base64.b64encode(b'stitch_shell').decode()

@pytest.fixture
def client_logged_in(monkeypatch):
    """Setup test client with logged in session"""
    monkeypatch.setenv('STITCH_ADMIN_USER', 'admin')
    monkeypatch.setenv('STITCH_ADMIN_PASSWORD', 'SuperSecurePassw0rd!')
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for tests
    
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

@pytest.fixture
def mock_aes_lib(tmp_path):
    """Create a temporary AES library file"""
    aes_lib_path = tmp_path / "st_aes_lib.ini"
    config = configparser.ConfigParser()
    config.add_section('test_aes_id')
    config.set('test_aes_id', 'aes_key', base64.b64encode(b'test_key_32_bytes_long_padding!!').decode())
    
    with open(aes_lib_path, 'w') as f:
        config.write(f)
    
    return str(aes_lib_path)

def test_execute_without_connection(client_logged_in):
    """Test execute endpoint without selecting a connection"""
    response = client_logged_in.post('/api/execute', json={
        'command': 'sysinfo'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert 'requires selecting a target connection' in data['output']

def test_execute_invalid_command(client_logged_in):
    """Test execute endpoint with invalid command"""
    response = client_logged_in.post('/api/execute', json={
        'command': ''
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] == False
    assert 'Missing command' in data['error']

def test_execute_command_too_long(client_logged_in):
    """Test execute endpoint with command too long"""
    long_command = 'a' * 501  # Exceeds 500 char limit
    
    response = client_logged_in.post('/api/execute', json={
        'command': long_command
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] == False
    assert 'Command too long' in data['error']

def test_execute_command_with_control_chars(client_logged_in):
    """Test execute endpoint with control characters"""
    response = client_logged_in.post('/api/execute', json={
        'command': 'test\x00command'
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] == False
    assert 'invalid control characters' in data['error']

@patch('web_app_real.get_stitch_server')
def test_execute_sessions_command(mock_get_server, client_logged_in, mock_stitch_server):
    """Test executing sessions command (server-only command)"""
    mock_get_server.return_value = mock_stitch_server
    
    response = client_logged_in.post('/api/execute', json={
        'command': 'sessions'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert 'Server Status' in data['output']
    assert 'Active Connections' in data['output']

@patch('web_app_real.get_stitch_server')
def test_execute_history_command(mock_get_server, client_logged_in, mock_stitch_server):
    """Test executing history command"""
    mock_get_server.return_value = mock_stitch_server
    
    response = client_logged_in.post('/api/execute', json={
        'command': 'history'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert 'Connection History' in data['output']

@patch('web_app_real.get_stitch_server')
def test_execute_showkey_command(mock_get_server, client_logged_in, mock_stitch_server):
    """Test executing showkey command"""
    mock_get_server.return_value = mock_stitch_server
    
    response = client_logged_in.post('/api/execute', json={
        'command': 'showkey'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert 'AES Encryption Keys' in data['output']

@patch('web_app_real.get_stitch_server')
@patch('web_app_real.connection_context')
@patch('web_app_real.st_aes_lib')
def test_execute_with_offline_connection(mock_aes_lib_patch, mock_connection_context, mock_get_server, client_logged_in, mock_stitch_server, mock_aes_lib):
    """Test execute with offline connection"""
    # Setup mocks
    mock_get_server.return_value = mock_stitch_server
    mock_stitch_server.inf_sock = {}  # No active connections
    mock_aes_lib_patch.return_value = mock_aes_lib
    
    response = client_logged_in.post('/api/execute', json={
        'connection_id': '192.168.1.100',
        'command': 'sysinfo'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert 'OFFLINE' in data['output']

@patch('web_app_real.get_stitch_server')
@patch('web_app_real.connection_context')
@patch('web_app_real.st_aes_lib')
@patch('web_app_real.stitch_lib')
def test_execute_with_online_connection_success(mock_stitch_lib, mock_aes_lib_path, mock_connection_context, mock_get_server, client_logged_in, mock_stitch_server, mock_aes_lib):
    """Test successful command execution with online connection"""
    # Setup mocks
    mock_get_server.return_value = mock_stitch_server
    mock_aes_lib_path = mock_aes_lib
    
    # Mock connection context with handshake data
    mock_connection_context.__contains__ = Mock(return_value=True)
    mock_connection_context.get = Mock(return_value={
        'aes_key': b'test_key_32_bytes_long_padding!!',
        'os': 'Windows 10',
        'platform': 'Windows',
        'hostname': 'test-host',
        'user': 'test-user',
        'port': '4040',
        'connected_at': '2024-01-01T12:00:00'
    })
    
    # Mock stitch_lib
    mock_stlib = Mock()
    mock_stlib.sysinfo = Mock()
    mock_stitch_lib.stitch_commands_library = Mock(return_value=mock_stlib)
    
    # Mock stdout capture
    with patch('builtins.print') as mock_print:
        response = client_logged_in.post('/api/execute', json={
            'connection_id': '192.168.1.100',
            'command': 'sysinfo'
        })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert 'Target:' in data['output']
    assert 'Command: sysinfo' in data['output']

@patch('web_app_real.get_stitch_server')
@patch('web_app_real.connection_context')
@patch('web_app_real._perform_handshake')
def test_execute_triggers_handshake(mock_handshake, mock_connection_context, mock_get_server, client_logged_in, mock_stitch_server):
    """Test that missing connection context triggers handshake"""
    # Setup mocks
    mock_get_server.return_value = mock_stitch_server
    mock_connection_context.__contains__ = Mock(return_value=False)  # No existing context
    mock_handshake.return_value = (True, {
        'aes_key': b'test_key_32_bytes_long_padding!!',
        'os': 'Windows 10',
        'platform': 'Windows',
        'hostname': 'test-host',
        'user': 'test-user',
        'port': '4040'
    })
    
    with patch('web_app_real.stitch_lib') as mock_stitch_lib:
        mock_stlib = Mock()
        mock_stitch_lib.stitch_commands_library = Mock(return_value=mock_stlib)
        
        response = client_logged_in.post('/api/execute', json={
            'connection_id': '192.168.1.100',
            'command': 'sysinfo'
        })
    
    assert response.status_code == 200
    mock_handshake.assert_called_once_with('192.168.1.100')

@patch('web_app_real.get_stitch_server')
@patch('web_app_real.connection_context')
@patch('web_app_real._perform_handshake')
def test_execute_handshake_failure(mock_handshake, mock_connection_context, mock_get_server, client_logged_in, mock_stitch_server):
    """Test command execution when handshake fails"""
    # Setup mocks
    mock_get_server.return_value = mock_stitch_server
    mock_connection_context.__contains__ = Mock(return_value=False)
    mock_handshake.return_value = (False, "❌ Handshake failed: Connection timeout")
    
    response = client_logged_in.post('/api/execute', json={
        'connection_id': '192.168.1.100',
        'command': 'sysinfo'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert 'Handshake failed' in data['output']

def test_execute_missing_json_body(client_logged_in):
    """Test execute endpoint with missing JSON body"""
    response = client_logged_in.post('/api/execute')
    
    assert response.status_code == 500  # Should trigger exception handling

def test_execute_invalid_json(client_logged_in):
    """Test execute endpoint with invalid JSON"""
    response = client_logged_in.post('/api/execute', 
                                   data='invalid json',
                                   content_type='application/json')
    
    # Should return 500 due to JSON parsing error (which is correct)
    assert response.status_code == 500

def test_execute_command_with_parameters(client_logged_in):
    """Test execute endpoint with command parameters"""
    response = client_logged_in.post('/api/execute', json={
        'command': 'firewall open',
        'parameters': {
            'port': '80',
            'protocol': 'TCP',
            'direction': 'IN'
        }
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    # Should require connection for firewall commands
    assert 'requires selecting a target connection' in data['output']

@patch('web_app_real.get_stitch_server')
def test_execute_clear_command(mock_get_server, client_logged_in, mock_stitch_server):
    """Test executing clear command (UI-specific)"""
    mock_get_server.return_value = mock_stitch_server
    
    response = client_logged_in.post('/api/execute', json={
        'command': 'clear'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert 'screen clear is UI-specific' in data['output']

def test_get_command_definitions(client_logged_in):
    """Test getting command definitions"""
    response = client_logged_in.get('/api/command_definitions')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True
    assert 'definitions' in data
    assert 'firewall' in data['definitions']
    assert 'hostsfile' in data['definitions']
    assert 'popup' in data['definitions']
    assert 'clearev' in data['definitions']

def test_rate_limiting_execute(client_logged_in):
    """Test rate limiting on execute endpoint"""
    # This test would need to be run with rate limiting enabled
    # For now, just verify the endpoint works normally
    response = client_logged_in.post('/api/execute', json={
        'command': 'home'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True