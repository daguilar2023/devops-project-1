"""Minimal Blog (Flask + SQLite)

Public: list & view non-archived posts.
Admin: CRUD, archive/unarchive, and action history.

Built for SDLC/DevOps coursework. Kept intentionally small and readable,
with a simple three-layer split: templates (presentation), routes/controllers
(application), and SQLAlchemy + SQLite (data).
"""
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, abort, Blueprint, g, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
import os
from typing import Any, Optional
from time import perf_counter
from prometheus_client import Counter, generate_latest

db = SQLAlchemy()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'blog.db')



class Config:
    """Tiny config wrapper so secrets/paths can come from env, with sane defaults."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{DB_PATH}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

bp = Blueprint("main", __name__)

# Prometheus metrics
REQUEST_COUNT = Counter("request_count", "Total requests", ["endpoint"])

# In-memory metrics used for /health JSON
REQUEST_TOTAL = 0          # plain integer counter
ERROR_COUNT = 0
TOTAL_LATENCY = 0.0

# ----------------------
# Models
# ----------------------
class Post(db.Model):
    def __init__(self, title: str, content: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.title = title
        self.content = content
    """Blog post entity stored in 'posts'.

    Archived posts are hidden from the public homepage.
    """
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_archived = db.Column(db.Boolean, default=False, nullable=False)
    # Note: naive UTC for simplicity; in production you'd likely use timezone-aware timestamps.
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Post {self.id} {self.title!r}>"

# ----------------------
# Action log model
# ----------------------
class ActionLog(db.Model):
    """Audit record of admin actions (CREATE/UPDATE/DELETE/ARCHIVE/UNARCHIVE).

    post_id is nullable so DELETE can be logged after the row is removed.
    """
    def __init__(self, action: str, post_id: Optional[int] = None, note: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.action = action
        self.post_id = post_id
        self.note = note
    __tablename__ = 'action_logs'
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(100), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    post = db.relationship('Post', backref=db.backref('logs', lazy=True))

    def __repr__(self):
        return f"<ActionLog {self.id} {self.action} post={self.post_id}>"

# ----------------------
# Utility: log actions
# ----------------------

def log_action(action: str, post: Post | None = None, note: str | None = None):
    """Append an audit entry to action_logs.

    Args:
        action: One of CREATE/UPDATE/DELETE/ARCHIVE/UNARCHIVE.
        post: The Post affected (None for DELETE after removal).
        note: Short human-readable context.
    """
    entry = ActionLog(action=action, post_id=(post.id if post else None), note=note)
    db.session.add(entry)
    db.session.commit()

# ----------------------
# Public routes
# ----------------------
@bp.route('/')
def index():
    # Public view: only non-archived posts, newest first.
    posts = Post.query.filter_by(is_archived=False).order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts)

@bp.route('/posts/<int:post_id>')
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.is_archived:
        abort(404)
    return render_template('post_form.html', post=post, readonly=True)

# ----------------------
# Admin routes (auth to be added in a later iteration)
# ----------------------
@bp.route('/admin')
def admin_home():
    # Show all posts including archived
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('admin.html', posts=posts)

@bp.route('/admin/posts/new', methods=['GET', 'POST'])
def admin_create_post():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        if not title or not content:
            flash('Title and content are required.', 'error')
            return redirect(url_for('main.admin_create_post'))
        post = Post(title=title, content=content)
        db.session.add(post)
        db.session.commit()
        log_action('CREATE', post, note=f'Created post "{post.title}"')
        flash('Post created.', 'success')
        return redirect(url_for('main.admin_home'))
    return render_template('post_form.html', post=None, readonly=False)

@bp.route('/admin/posts/<int:post_id>/edit', methods=['GET', 'POST'])
def admin_edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if request.method == 'POST':
        old_title, old_content = post.title, post.content
        post.title = request.form.get('title', '').strip()
        post.content = request.form.get('content', '').strip()
        if not post.title or not post.content:
            flash('Title and content are required.', 'error')
            return redirect(url_for('main.admin_edit_post', post_id=post.id))
        db.session.commit()
        log_action('UPDATE', post, note=f'Updated title from {old_title!r} to {post.title!r}')
        flash('Post updated.', 'success')
        return redirect(url_for('main.admin_home'))
    return render_template('post_form.html', post=post, readonly=False)

@bp.route('/admin/posts/<int:post_id>/delete', methods=['POST'])
def admin_delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    title = post.title
    db.session.delete(post)
    db.session.commit()
    # Log after deletion; post_id is None because the row is gone.
    log_action('DELETE', None, note=f'Deleted post id={post_id} title={title!r}')
    flash('Post deleted.', 'success')
    return redirect(url_for('main.admin_home'))

@bp.route('/admin/posts/<int:post_id>/archive', methods=['POST'])
def admin_archive_post(post_id):
    post = Post.query.get_or_404(post_id)
    if not post.is_archived:
        post.is_archived = True
        db.session.commit()
        # Record the archive event for history/auditing.
        log_action('ARCHIVE', post, note=f'Archived post "{post.title}"')
        flash('Post archived.', 'success')
    return redirect(url_for('main.admin_home'))

@bp.route('/admin/posts/<int:post_id>/unarchive', methods=['POST'])
def admin_unarchive_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.is_archived:
        post.is_archived = False
        db.session.commit()
        # Record the unarchive event for history/auditing.
        log_action('UNARCHIVE', post, note=f'Unarchived post "{post.title}"')
        flash('Post unarchived.', 'success')
    return redirect(url_for('main.admin_home'))

@bp.route('/admin/history')
def admin_history():
    logs = ActionLog.query.order_by(ActionLog.created_at.desc()).limit(200).all()
    return render_template('history.html', logs=logs)

@bp.route("/health")
def health():
    """Basic health + metrics endpoint for monitoring."""
    avg_latency = (TOTAL_LATENCY / REQUEST_TOTAL) if REQUEST_TOTAL else 0.0
    payload = {
        "status": "ok",
        "request_count": REQUEST_TOTAL,
        "error_count": ERROR_COUNT,
        "avg_latency_ms": round(avg_latency * 1000, 2),
    }
    # jsonify ensures proper JSON + mimetype
    return jsonify(payload), 200

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    
    db.init_app(app)

    @app.before_request
    def before_request_metrics():
        REQUEST_COUNT.labels(endpoint=request.path).inc()

    # ---- metrics hooks ----
    @app.before_request
    def _start_timer():
        g._start_time = perf_counter()

    @app.after_request
    def _record_metrics(response):
        global REQUEST_TOTAL, TOTAL_LATENCY
        REQUEST_TOTAL += 1
        start = getattr(g, "_start_time", None)
        if start is not None:
            TOTAL_LATENCY += perf_counter() - start
        return response
    
    @app.teardown_request
    def _count_errors(exc):
        global ERROR_COUNT
        if exc is not None:
            ERROR_COUNT += 1

    # register blueprint
    app.register_blueprint(bp)

    # ensure tables exist on first run (safe if they already exist)
    with app.app_context():
        existing = set(inspect(db.engine).get_table_names())
        needed = {"posts", "action_logs"}
        if not needed.issubset(existing):
            db.create_all()

    # CLI helper to init the DB
    @app.cli.command("init-db")
    def init_db_cmd():
        """Initialize database tables (safe to run multiple times)."""
        db.create_all()
        print("Database initialized at", DB_PATH)

    return app

# Expose a global WSGI app for Azure and other WSGI servers
app = create_app()

@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": "text/plain"}

if __name__ == "__main__":
    # Local development entrypoint
    app.run(debug=True)

    #comment to test deployment