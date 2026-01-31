import io
import os
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_index_loads(client):
    res = client.get('/')
    assert res.status_code == 200
    assert b'Enter Your Text' in res.data


def test_api_render_no_text(client):
    res = client.post('/api/render', json={})
    assert res.status_code == 400


def test_export_png_no_text(client):
    res = client.post('/export_png', data={})
    assert res.status_code == 400


def test_export_png_short(client):
    res = client.post('/export_png', data={'user_input': 'A'})
    # should return PNG or error depending on server state; expect 200 or 400
    assert res.status_code in (200, 400)
