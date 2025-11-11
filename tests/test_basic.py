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