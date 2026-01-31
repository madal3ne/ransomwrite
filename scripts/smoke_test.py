#!/usr/bin/env python3
"""Simple smoke test for the ransomwrite app.

Usage:
  python scripts/smoke_test.py --url https://your-deploy-url.com

This checks:
- GET / returns 200
- POST /api/render with sample text returns 200 and JSON with items
- POST /export_png returns image/png or 400 when input short
"""
import argparse
import sys
import requests


def check_root(url):
    r = requests.get(url, timeout=10)
    if r.status_code != 200:
        raise RuntimeError(f"GET / returned status {r.status_code}")
    print("/ OK")


def check_api_render(url):
    r = requests.post(f"{url.rstrip('/')}/api/render", json={"text": "HELLO WORLD"}, timeout=10)
    if r.status_code != 200:
        raise RuntimeError(f"POST /api/render returned {r.status_code}: {r.text[:200]}")
    data = r.json()
    if 'items' not in data:
        raise RuntimeError("/api/render response missing 'items' key")
    print("/api/render OK")


def check_export(url):
    r = requests.post(f"{url.rstrip('/')}/export_png", data={'user_input': 'TEST NOTE'}, timeout=20)
    if r.status_code == 200:
        ctype = r.headers.get('Content-Type', '')
        if 'image/' not in ctype:
            raise RuntimeError(f"/export_png returned 200 but Content-Type is {ctype}")
        print("/export_png OK (image returned)")
    elif r.status_code in (400, 413):
        print(f"/export_png returned {r.status_code}; acceptable (input validation)")
    else:
        raise RuntimeError(f"/export_png returned unexpected status {r.status_code}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True, help='Base URL of deployed service (e.g., https://ransom.example.com)')
    args = parser.parse_args()
    url = args.url
    try:
        check_root(url)
        check_api_render(url)
        check_export(url)
    except Exception as e:
        print('Smoke test FAILED:', e)
        sys.exit(2)
    print('Smoke test PASSED')
    sys.exit(0)
