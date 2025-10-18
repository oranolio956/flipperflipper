import os
import pytest
from web_app_real import app as flask_app

@pytest.fixture
def client_logged_in(monkeypatch):
    monkeypatch.setenv('STITCH_ADMIN_USER', 'admin')
    monkeypatch.setenv('STITCH_ADMIN_PASSWORD', 'SuperSecurePassw0rd!')
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        c.get('/login')
        with c.session_transaction() as sess:
            sess['logged_in'] = True
            sess['user'] = 'admin'
            sess['username'] = 'admin'
        yield c

def test_export_logs_json(client_logged_in):
    resp = client_logged_in.get('/api/export/logs?format=json')
    assert resp.status_code == 200
    assert resp.headers.get('Content-Type').startswith('application/json')
    assert 'Content-Length' in resp.headers
    assert 'ETag' in resp.headers


def test_export_commands_csv(client_logged_in):
    resp = client_logged_in.get('/api/export/commands?format=csv')
    assert resp.status_code == 200
    assert resp.headers.get('Content-Type').startswith('text/csv')
    assert 'Content-Length' in resp.headers
    assert 'ETag' in resp.headers
