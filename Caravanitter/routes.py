import os
import secrets
from PIL import Image
from flask import render_template, flash, redirect, url_for, request, abort
from Caravanitter import app, db, bcrypt
from Caravanitter.forms import LoginForm, RegisterForm, PostForm, UpdateAccountForm, CommentForm, EmptyForm
from Caravanitter.models import User, Post, Comment, PostLike, CommentLike, Notify, SharePost
from flask_login import login_user, logout_user, current_user, login_required




def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/img', picture_fn)
    form_picture.save(picture_path)

    return picture_fn

@app.errorhandler(404)
def error_404(error):
    return render_template('error_404.html', title="Página não encontrada")

@app.errorhandler(403)
def error_403(error):
    return render_template('error_403.html', title="Acesso negado")

@app.errorhandler(500)
def error_500(error):
    return render_template('error_500.html', title="Erro inesperado")

@app.route("/index")
@app.route("/")
def index():
    if current_user.is_authenticated == True:
        return redirect(url_for("feed"))
    else:
        return render_template('index.html')

@app.route("/feed", methods=["GET", "POST"])
@login_required
def feed():
    posts = Post.query.order_by(Post.date.desc())
    followed = current_user.followed.all()
    return render_template('feed.html', posts=posts, title="Feed", followed=followed)

@app.route("/create_post", methods=["GET", "POST"])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            image = picture_file
        else:
            image = False
        post = Post(title=form.title.data, content=form.content.data, author=current_user, pic=image)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for("feed"))
    return render_template('criar_post.html', form=form, title="Criar uma Postagem", legend="Criar uma Postagem")

@app.route("/register", methods=["GET","POST"])
def register():
    if current_user.is_authenticated == True:
        return redirect (url_for("feed"))
    else: 
        form = RegisterForm()
        if form.validate_on_submit():
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user = User(username=form.username.data, password=hashed_password, name=form.name.data, email=form.email.data)
            db.session.add(user)
            db.session.commit()
            flash('Conta cadastrada com sucesso!', 'success')
            return redirect(url_for("login"))
        return render_template('register.html', form=form, title="Cadastre-se")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated == True:
        return redirect (url_for("feed"))
    else:
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email = form.email.data).first()
            if user and bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for("feed"))
            else:
                flash("Email ou senha incorretos", 'danger')
        return render_template('login.html', form=form , title="Login")

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/perfil")
@login_required
def perfil():
    posts = Post.query.filter_by(author=current_user).order_by(Post.date.desc())
    image_file = url_for('static', filename='img/' + current_user.pic)
    like = PostLike.query.filter_by(user_id=current_user.id)
    share = SharePost.query.filter_by(user_id=current_user.id)
    return render_template('perfil.html', title='Perfil', image_file=image_file, posts=posts, like=like, share=share)

@app.route("/atualizar_perfil", methods=["GET","POST"])
@login_required
def atualizar_perfil():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.pic = picture_file
        current_user.username = form.username.data
        current_user.name = form.name.data
        current_user.card = form.card.data
        db.session.commit()
        flash('Perfil atualizado com sucesso', 'success')
        return redirect(url_for('perfil'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.name.data = current_user.name
        form.card.data = current_user.card
    return render_template('atualizar_perfil.html', title='Atualizar Perfil', form=form)    


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
@login_required
def post(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.date.desc())
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            image = picture_file
        else:
            image = False
        comment = Comment(content=form.content.data, post_id=post.id, comment_author=current_user, pic=image)
        db.session.add(comment)
        if current_user.id != post.author.id:
            notify = Notify(post_id=post.id, causer_author=current_user, rec_id=post.author.id, action="comentou em sua publicação:", content=form.content.data)
            db.session.add(notify)
        db.session.commit()
        return redirect(url_for('post', post_id=post.id))
    return render_template('post.html', title=post.title, post=post, form=form, comments=comments)

@app.route("/post/<int:post_id>/update", methods=["GET","POST"])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            post.pic = picture_file
        post.title = form.title.data
        post.content = form.content.data
        post.edit = 1
        db.session.commit()
        flash('Postagem atualizada com sucesso!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('update_post.html', form=form, post=post, title="Editar uma Postagem", legend="Editar uma Postagem")

@app.route("/post/<int:post_id>/like/<action>", methods=["GET", "POST"])
@login_required
def like_post(post_id, action):
    post = Post.query.filter_by(id=post_id).first_or_404()
    if action == 'like':
        current_user.like_post(post)
        if current_user.id != post.author.id:
            notify = Notify(post_id=post.id, causer_author=current_user, rec_id=post.author.id, action="curtiu sua publicação", content=post.title)
            db.session.add(notify)
        db.session.commit()
    if action == 'unlike':
        current_user.unlike_post(post)
        notify = Notify.query.filter_by(post_id=post.id, causer_author=current_user, rec_id=post.author.id).first()
        if notify != None:
            db.session.delete(notify)
        db.session.commit()
    if action == 'None':
        return render_template('error_500.html', title="Erro inesperado")
    return redirect(request.referrer)

@app.route("/post/<int:post_id>/share/<action>", methods=["GET", "POST"])
@login_required
def share_post(post_id, action):
    post = Post.query.filter_by(id=post_id).first_or_404()
    if action == 'share':
        current_user.share_post(post)
        if current_user.id != post.author.id:
            notify = Notify(post_id=post.id, causer_author=current_user, rec_id=post.author.id, action="compartilhou sua publicação", content=post.title)
            db.session.add(notify)
        db.session.commit()
    if action == 'unshare':
        current_user.unshare_post(post)
        notify = Notify.query.filter_by(post_id=post.id, causer_author=current_user, rec_id=post.author.id).first()
        if notify != None:
            db.session.delete(notify)
        db.session.commit()
    if action == 'None':
        return render_template('error_500.html', title="Erro inesperado")
    return redirect(request.referrer)


@app.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    if post.pic != "0":
        os.unlink(os.path.join(app.root_path, 'static/img/' + post.pic))
        db.session.delete(post)
    else:
        db.session.delete(post)
    db.session.commit()
    flash('Postagem excluída com sucesso!', 'success')
    return redirect(url_for('feed'))
    
@app.route("/user/<string:username>")
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    if current_user == user:
        return redirect(url_for("perfil"))
    else:
        image_file = url_for('static', filename='img/' + user.pic)
        posts = Post.query.filter_by(author=user).order_by(Post.date.desc())
        like = PostLike.query.filter_by(user_id=user.id)
        share = SharePost.query.filter_by(user_id=user.id)
        form = EmptyForm()
        return render_template('user.html', posts=posts, user=user, like=like, share=share, image_file=image_file, form=form)

@app.route("/comment/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    post = Post.query.filter_by(id=comment.post_id).first()
    if comment.comment_author != current_user:
        abort(403)
    if comment.pic != "0":
        os.unlink(os.path.join(app.root_path, 'static/img/' + comment.pic))
        db.session.delete(comment)
        notify = Notify.query.filter_by(post_id=comment.post_id, causer_author=current_user, rec_id=post.author.id).first()
        if notify != None:
            db.session.delete(notify)
    else:
        db.session.delete(comment)
        notify = Notify.query.filter_by(post_id=comment.post_id, causer_author=current_user, rec_id=post.author.id).first()
        if notify != None:
            db.session.delete(notify)
    db.session.commit()
    flash('Comentário excluído com sucesso!', 'success')
    return redirect(url_for('post', post_id=comment.post_id))


@app.route("/comment/<int:comment_id>/update", methods=["GET","POST"])
@login_required
def update_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.comment_author != current_user:
        abort(403)
    form = CommentForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            comment.pic = picture_file
        comment.content = form.content.data
        comment.edit = 1
        db.session.commit()
        flash('Comentário atualizado com sucesso!', 'success')
        return redirect(url_for('post', post_id=comment.post_id))
    elif request.method == 'GET':
        form.content.data = comment.content
    return render_template('editar_comentário.html', form=form, comment=comment, title="Editar um Comentário")


@app.route("/comment/<int:comment_id>/like/<action>", methods=["GET", "POST"])
@login_required
def like_comment(comment_id, action):
    comment = Comment.query.filter_by(id=comment_id).first_or_404()
    if action == 'like':
        current_user.like_comment(comment)
        db.session.commit()
        if current_user.id != comment.comment_author.id:
            notify = Notify(post_id=comment.post_id, causer_author=current_user, rec_id=comment.comment_author.id, action="curtiu seu comentário", content=comment.content)
            db.session.add(notify)
        db.session.commit()
    if action == 'unlike':
        current_user.unlike_comment(comment)
        notify = Notify.query.filter_by(post_id=comment.post_id, causer_author=current_user, rec_id=comment.comment_author.id).first()
        if notify != None:
            db.session.delete(notify)
        db.session.commit()
    if action == 'None':
        return render_template('error_500.html', title="Erro inesperado")
    return redirect(request.referrer)


@app.route("/notifications")
@login_required
def notifications():
    notify = Notify.query.filter_by(rec_id=current_user.id).order_by(Notify.date.desc())
    return render_template('notifications.html', title="Notificações", notify=notify)

@app.route("/notifications/<int:notify_id>/delete")
@login_required
def delete_notifications(notify_id):
    notify = Notify.query.get_or_404(notify_id)
    user = notify.causer_author.username
    if notify.rec_id != current_user.id:
        abort(403)
    db.session.delete(notify)
    db.session.commit()
    if notify.post_id == None:
        return redirect(url_for('user', username=user))
    else:
        return redirect(url_for('post', post_id=notify.post_id))

@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    q = request.args.get('q')
    if q != "":
        user = User.query.filter(User.username.contains(q))
        post = Post.query.filter(Post.title.contains(q) | Post.content.contains(q))
        return render_template('search.html', title="Busca", user=user, post=post)
    else:
        return redirect(request.referrer) 


@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('Você não pode seguir a sí!', 'info')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        flash('Você está seguindo {}!'.format(username), 'success')
        notify = Notify(post_id=None, causer_author=current_user, rec_id=user.id, action="está seguindo você.", content="Quer seguir de volta?")
        db.session.add(notify)
        db.session.commit()
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))

@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('Você não pode deixar de seguir a sí!', 'info')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        notify = Notify.query.filter_by(causer_author=current_user, rec_id=user.id, action="está seguindo você.").first()
        if notify != None:
            db.session.delete(notify)
        db.session.commit()
        flash('Você deixou de seguir {}.'.format(username), 'danger')
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))

@app.route('/theme')
@login_required
def theme():
    if current_user.dark_mode == False:
        current_user.dark_mode = True
    else:
        current_user.dark_mode = False
    db.session.commit()
    return redirect(request.referrer)
