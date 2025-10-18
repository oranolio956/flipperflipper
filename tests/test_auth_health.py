import os
import pytest
from web_app_real import app as flask_app

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv('STITCH_ADMIN_USER', 'admin')
    monkeypatch.setenv('STITCH_ADMIN_PASSWORD', 'SuperSecurePassw0rd!')
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        yield c

def test_health(client):
    resp = client.get('/health')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'healthy'

def test_login_page(client):
    resp = client.get('/login')
    assert resp.status_code == 200
    assert b'Oranolio' in resp.data
