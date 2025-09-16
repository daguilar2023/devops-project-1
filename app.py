from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'blog.db')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ----------------------
# Models
# ----------------------
class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_archived = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Post {self.id} {self.title!r}>"

# New model for action logs
class ActionLog(db.Model):
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
    entry = ActionLog(action=action, post_id=(post.id if post else None), note=note)
    db.session.add(entry)
    db.session.commit()

# ----------------------
# Public routes
# ----------------------
@app.route('/')
def index():
    posts = Post.query.filter_by(is_archived=False).order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts)

@app.route('/posts/<int:post_id>')
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.is_archived:
        abort(404)
    return render_template('post_form.html', post=post, readonly=True)

# ----------------------
# Admin routes (no auth yet)
# ----------------------
@app.route('/admin')
def admin_home():
    # Show all posts including archived
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('admin.html', posts=posts)

@app.route('/admin/posts/new', methods=['GET', 'POST'])
def admin_create_post():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        if not title or not content:
            flash('Title and content are required.', 'error')
            return redirect(url_for('admin_create_post'))
        post = Post(title=title, content=content)
        db.session.add(post)
        db.session.commit()
        log_action('CREATE', post, note=f'Created post "{post.title}"')
        flash('Post created.', 'success')
        return redirect(url_for('admin_home'))
    return render_template('post_form.html', post=None, readonly=False)

@app.route('/admin/posts/<int:post_id>/edit', methods=['GET', 'POST'])
def admin_edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if request.method == 'POST':
        old_title, old_content = post.title, post.content
        post.title = request.form.get('title', '').strip()
        post.content = request.form.get('content', '').strip()
        if not post.title or not post.content:
            flash('Title and content are required.', 'error')
            return redirect(url_for('admin_edit_post', post_id=post.id))
        db.session.commit()
        log_action('UPDATE', post, note=f'Updated title from {old_title!r} to {post.title!r}')
        flash('Post updated.', 'success')
        return redirect(url_for('admin_home'))
    return render_template('post_form.html', post=post, readonly=False)

@app.route('/admin/posts/<int:post_id>/delete', methods=['POST'])
def admin_delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    title = post.title
    db.session.delete(post)
    db.session.commit()
    log_action('DELETE', None, note=f'Deleted post id={post_id} title={title!r}')
    flash('Post deleted.', 'success')
    return redirect(url_for('admin_home'))

@app.route('/admin/posts/<int:post_id>/archive', methods=['POST'])
def admin_archive_post(post_id):
    post = Post.query.get_or_404(post_id)
    if not post.is_archived:
        post.is_archived = True
        db.session.commit()
        log_action('ARCHIVE', post, note=f'Archived post "{post.title}"')
        flash('Post archived.', 'success')
    return redirect(url_for('admin_home'))

@app.route('/admin/posts/<int:post_id>/unarchive', methods=['POST'])
def admin_unarchive_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.is_archived:
        post.is_archived = False
        db.session.commit()
        log_action('UNARCHIVE', post, note=f'Unarchived post "{post.title}"')
        flash('Post unarchived.', 'success')
    return redirect(url_for('admin_home'))

@app.route('/admin/history')
def admin_history():
    logs = ActionLog.query.order_by(ActionLog.created_at.desc()).limit(200).all()
    return render_template('history.html', logs=logs)

# ----------------------
# CLI helper to init the DB
# ----------------------
@app.cli.command('init-db')
def init_db():
    """Initialize the database tables."""
    db.create_all()
    print('Database initialized at', DB_PATH)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)