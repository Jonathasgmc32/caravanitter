from Caravanitter import db, login_manager
from datetime import datetime
from flask_login import UserMixin


followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('users.id'))
)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    card = db.Column(db.Text, default='Olá')
    dark_mode = db.Column(db.Boolean, default=False)
    pic = db.Column(db.String(60), nullable=False, default='perfil.png')
    posts = db.relationship('Post', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='comment_author', lazy=True)
    liked = db.relationship('PostLike', foreign_keys='PostLike.user_id', backref='user', lazy='dynamic')
    liked_comment = db.relationship('CommentLike', foreign_keys='CommentLike.user_id', backref='user', lazy='dynamic')
    causer = db.relationship('Notify', backref='causer_author', lazy=True)
    shared = db.relationship('SharePost', foreign_keys='SharePost.user_id', backref='user', lazy='dynamic')
    followed = db.relationship('User', secondary=followers, primaryjoin=(followers.c.follower_id == id), secondaryjoin=(followers.c.followed_id == id), backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def like_post(self, post):
        if not self.has_liked_post(post):
            like = PostLike(user_id=self.id, post_id=post.id)
            db.session.add(like)


    def unlike_post(self, post):
        if self.has_liked_post(post):
            PostLike.query.filter_by(
                user_id=self.id,
                post_id=post.id).delete()

    def has_liked_post(self, post):
        return PostLike.query.filter(
            PostLike.user_id == self.id,
            PostLike.post_id == post.id).count() > 0
            
    def like_comment(self, comment):
        if not self.has_liked_comment(comment):
            like = CommentLike(user_id=self.id, comment_id=comment.id)
            db.session.add(like)

    def unlike_comment(self, comment):
        if self.has_liked_comment(comment):
            CommentLike.query.filter_by(
                user_id=self.id,
                comment_id=comment.id).delete()

    def has_liked_comment(self, comment):
        return CommentLike.query.filter(
            CommentLike.user_id == self.id,
            CommentLike.comment_id == comment.id).count() > 0

    def share_post(self, post):
        if not self.has_shared_post(post):
            share = SharePost(user_id=self.id, post_id=post.id)
            db.session.add(share)


    def unshare_post(self, post):
        if self.has_shared_post(post):
            SharePost.query.filter_by(
                user_id=self.id,
                post_id=post.id).delete()

    def has_shared_post(self, post):
        return SharePost.query.filter(
            SharePost.user_id == self.id,
            SharePost.post_id == post.id).count() > 0

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def notification(self):
        return Notify.query.filter_by(rec_id=self.id).count()

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.pic}')"

class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    edit = db.Column(db.Boolean, default=False)
    pic = db.Column(db.String(60), nullable=False)
    comments = db.relationship('Comment', backref='comment', lazy='dynamic')
    likes = db.relationship('PostLike', backref='likepost', lazy='dynamic')
    shares = db.relationship('SharePost', backref='sharepost', lazy='dynamic')


    def __repr__(self):
        return f"Post('{self.title}', '{self.date}')"

class Comment(db.Model):

    __tablename__ = "comments"

    id = db.Column(db.Integer,unique=True, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    posts = db.relationship('Post', backref=db.backref('post', cascade="all, delete-orphan", lazy=True))
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    edit = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    pic = db.Column(db.String(60), nullable=False, default=False)
    likes = db.relationship('CommentLike', backref='likepost', lazy='dynamic')

    def __repr__(self):
        return f"Comment('{self.post_id}', '{self.date}')"


class PostLike(db.Model):
    __tablename__ = 'post_like'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    posts = db.relationship('Post', backref=db.backref('likepost', cascade="all, delete-orphan", lazy=True))

class CommentLike(db.Model):
    __tablename__ = 'comment_like'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'))
    posts = db.relationship('Comment', backref=db.backref('post', cascade="all, delete-orphan", lazy=True))

class Notify(db.Model):
    __tablename__ = 'notify'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    rec_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    action = db.Column(db.String, nullable=False)
    content = db.Column(db.Text, nullable=False)
    posts = db.relationship('Post', backref=db.backref('notifypost', cascade="all, delete-orphan", lazy=True))

class SharePost(db.Model):
    __tablename__ = 'share_post'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    posts = db.relationship('Post', backref=db.backref('sharepost', cascade="all, delete-orphan", lazy=True))