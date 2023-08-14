from datetime import date
from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from functools import wraps
from sqlalchemy.orm import relationship
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_KEY")
ckeditor = CKEditor(app)
Bootstrap5(app)

# TODO: Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
bcrypt = Bcrypt()
bcrypt.init_app(app)


def only_admin(func):
    @wraps(func)
    def wrapper_func(*args, **kwargs):
        if not current_user.is_authenticated or current_user.id != 1:
            return redirect(url_for("get_all_posts"))
        return func(*args, **kwargs)
    return wrapper_func


def is_admin():
    if current_user.is_authenticated and current_user.id == 1:
        return True
    return False

# load_user callback


@login_manager.user_loader
def load_user(user_id):
    user = db.session.get(User, user_id)
    return user if user else None


# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    "DB_URI", "sqlite:///blog.db")
db = SQLAlchemy()
db.init_app(app)


# CONFIGURE TABLES
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    # Create reference to the User object
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="parent_post",
                            cascade="all, delete", passive_deletes=True)


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    # Create reference to the User object
    author_id = db.Column(db.Integer, db.ForeignKey(
        "users.id", ondelete="CASCADE"))
    author = relationship("User", back_populates="comments")
    # Create reference to the BlogPost object
    post_id = db.Column(db.Integer, db.ForeignKey(
        "blog_posts.id", ondelete="CASCADE"))
    parent_post = relationship("BlogPost", back_populates="comments")


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(1000), nullable=False)
    # These will act like a List of BlogPost and Comment objects
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="author",
                            cascade="all, delete", passive_deletes=True)

    def __str__(self) -> str:
        return self.name


with app.app_context():
    db.create_all()


# TODO: Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register', methods=["POST", "GET"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("get_all_posts"))

    register_form = RegisterForm()
    if register_form.validate_on_submit():
        u_name = register_form.name.data
        u_email = register_form.email.data
        u_password = register_form.password.data

        user = db.session.execute(
            db.select(User).filter_by(email=u_email)).scalar()

        if user:
            flash("You've already registered with that Email.", "danger")
            return redirect(url_for("login"))

        new_user = User(name=u_name,
                        email=u_email,
                        password=bcrypt.generate_password_hash(u_password))

        db.session.add(new_user)
        db.session.commit()
        # Log in and authenticate user after adding details to database.
        login_user(new_user)
        return redirect(url_for("get_all_posts"))
    return render_template("register.html", form=register_form, authenticated=False)


# TODO: Retrieve a user from the database based on their email.
@app.route('/login', methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("get_all_posts"))

    login_form = LoginForm()
    if login_form.validate_on_submit():
        u_email = login_form.email.data
        u_password = login_form.password.data
        user = db.session.execute(
            db.select(User).filter_by(email=u_email)).scalar()
        if user and bcrypt.check_password_hash(user.password, u_password):
            login_user(user)
            return redirect(url_for("get_all_posts"))
        flash("Invalid Email or Password!", "danger")
    return render_template("login.html", form=login_form, authenticated=False)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts, authenticated=current_user.is_authenticated, user_admin=is_admin())


# TODO: Allow logged-in users to comment on posts
@app.route("/post/<int:post_id>", methods=["POST", "GET"])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    all_comments = requested_post.comments
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.", "danger")
            return redirect(url_for("login"))
        new_comment = Comment(
            content=comment_form.content.data,
            parent_post=requested_post,
            author=current_user,
        )
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for("show_post", post_id=requested_post.id))
    return render_template("post.html", post=requested_post, user_admin=is_admin(),
                           form=comment_form, comments=all_comments, authenticated=current_user.is_authenticated)


@app.route("/new-post", methods=["GET", "POST"])
@only_admin
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, authenticated=current_user.is_authenticated)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@only_admin
def edit_post(post_id):
    req_post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(obj=req_post)
    if edit_form.validate_on_submit():
        req_post.title = edit_form.title.data
        req_post.subtitle = edit_form.subtitle.data
        req_post.img_url = edit_form.img_url.data
        req_post.author = current_user
        req_post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=req_post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True, authenticated=current_user.is_authenticated)


@app.route("/delete/<int:post_id>")
@only_admin
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template("about.html", authenticated=current_user.is_authenticated)


# @app.route("/contact")
# def contact():
#     return render_template("contact.html", authenticated=current_user.is_authenticated)


if __name__ == "__main__":
    app.run(debug=True)
