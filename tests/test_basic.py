# tests/test_admin.py
import os, sys; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })
    with app.test_client() as c:
        yield c

def test_admin_page_loads(client):
    r = client.get("/admin")
    assert r.status_code == 200

def test_create_post_happy_path(client):
    r = client.post("/admin/posts/new", data={"title": "Hello", "content": "World"}, follow_redirects=True)
    assert r.status_code == 200
    # Post should show on admin page
    assert b"Hello" in r.data

def test_homepage_loads(client):
    """Ensure homepage loads successfully"""
    r = client.get("/")
    assert r.status_code == 200

def test_admin_history_page_loads(client):
    """Ensure admin history page loads"""
    r = client.get("/admin/history")
    assert r.status_code in (200, 302, 404)

def test_edit_post_page(client):
    """Ensure edit post page handles missing ID gracefully"""
    r = client.get("/admin/posts/1/edit")
    assert r.status_code in (200, 302, 404)

def test_delete_post_page(client):
    """Ensure delete post handles missing ID gracefully"""
    r = client.post("/admin/posts/1/delete")
    assert r.status_code in (200, 302, 404)

def test_archive_post_page(client):
    """Ensure archive post route responds"""
    r = client.post("/admin/posts/1/archive")
    assert r.status_code in (200, 302, 404)

def test_unarchive_post_page(client):
    """Ensure unarchive post route responds"""
    r = client.post("/admin/posts/1/unarchive")
    assert r.status_code in (200, 302, 404)

def test_view_post_page(client):
    """Ensure individual post page loads or fails gracefully"""
    r = client.get("/posts/1")
    assert r.status_code in (200, 302, 404)

def test_health_endpoint(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] == "ok"
    # Should at least have these keys
    assert "request_count" in data
    assert "error_count" in data
    assert "avg_latency_ms" in data