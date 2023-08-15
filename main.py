from datetime import date
from flask import render_template, redirect, url_for, flash
from flask_login import login_user, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from functools import wraps
from models import User, Comment, BlogPost
from app import create_app, db, login_manager, bcrypt


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


app = create_app()

with app.app_context():
    db.create_all()


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
    app.run(debug=False)
