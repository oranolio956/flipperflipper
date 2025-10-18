import os
import re
import json
from pathlib import Path

# Ensure creds before importing app
os.environ.setdefault('STITCH_ADMIN_USER', 'admin')
os.environ.setdefault('STITCH_ADMIN_PASSWORD', 'SuperSecurePassw0rd!')

from web_app_real import app  # noqa: E402

# Disable CSRF for API/login form in this smoke test
app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True


def extract_csrf(html: str) -> str:
    m = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
    return m.group(1) if m else ''


def run_smoke():
    results = []
    with app.test_client() as c:
        # Health
        r = c.get('/health')
        results.append(('GET /health', r.status_code == 200))

        # Login page
        r = c.get('/login')
        results.append(('GET /login 200', r.status_code == 200))
        results.append(('Branding Oranolio on login', b'Oranolio' in r.data))

        # Login (CSRF disabled for test)
        r = c.post('/login', data={'username': os.environ['STITCH_ADMIN_USER'],
                                   'password': os.environ['STITCH_ADMIN_PASSWORD']}, follow_redirects=True)
        results.append(('POST /login redirects to dashboard', r.status_code == 200 and b'Active Connections Dashboard' in r.data))

        # Server status
        r = c.get('/api/server/status')
        ok = r.status_code == 200 and 'application/json' in (r.content_type or '')
        results.append(('GET /api/server/status', ok))

        # Prepare a download file
        downloads_dir = Path('Downloads') / '1.2.3.4'
        downloads_dir.mkdir(parents=True, exist_ok=True)
        test_file = downloads_dir / 'test.txt'
        test_file.write_text('hello')

        # Files listing
        r = c.get('/api/files/downloads')
        ok = r.status_code == 200 and isinstance(r.get_json(silent=True), list)
        results.append(('GET /api/files/downloads', ok))

        # Negative upload (no file)
        r = c.post('/api/upload', data={'target_id': '1.2.3.4'})
        results.append(('POST /api/upload missing file -> 400', r.status_code == 400))

        # Payload generation
        payload_req = {
            'enable_bind': True,
            'bind_host': '',
            'bind_port': 4433,
            'enable_listen': True,
            'listen_host': 'localhost',
            'listen_port': 4455
        }
        r = c.post('/api/generate-payload', data=json.dumps(payload_req), content_type='application/json')
        j = r.get_json(silent=True) or {}
        ok = r.status_code == 200 and j.get('success') is True and j.get('payload_size', 0) > 0
        results.append(('POST /api/generate-payload', ok))

    # Print summary
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    for name, ok in results:
        print(f"{name}: {'OK' if ok else 'FAIL'}")
    print(f"\nSmoke test: {passed}/{total} checks passed")


if __name__ == '__main__':
    run_smoke()
