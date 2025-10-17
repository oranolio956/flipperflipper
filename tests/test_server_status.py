import os
import pytest
from web_app_real import app as flask_app

@pytest.fixture
def client_logged_in(monkeypatch):
    monkeypatch.setenv('STITCH_ADMIN_USER', 'admin')
    monkeypatch.setenv('STITCH_ADMIN_PASSWORD', 'SuperSecurePassw0rd!')
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        # Fetch login page to get CSRF token
        c.get('/login')
        with c.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user'] = 'admin'
            sess['username'] = 'admin'
        yield c

def test_server_status(client_logged_in):
    resp = client_logged_in.get('/api/server/status')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'listening' in data
    assert 'active_connections' in data
