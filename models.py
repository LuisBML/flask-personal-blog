from app import db
from flask_login import UserMixin
from sqlalchemy.orm import relationship


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
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)
    name = db.Column(db.String(250), nullable=False)
    # These will act like a List of BlogPost and Comment objects
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="author",
                            cascade="all, delete", passive_deletes=True)

    def __str__(self) -> str:
        return self.name
