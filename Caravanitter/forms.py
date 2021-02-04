from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from Caravanitter.models import User

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Senha", validators=[DataRequired()])
    remember = BooleanField("Lembrar Usuário")
    submit = SubmitField('Entrar')

class RegisterForm(FlaskForm):
    username = StringField("Usuário", validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField("Senha", validators=[DataRequired()])
    confirm_password = PasswordField("Confirmar Senha", validators=[DataRequired(), EqualTo('password')])
    name = StringField("Nome", validators=[DataRequired(), Length(min=2, max=40)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField('Cadastre-se')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Esse usuário já existe. Por favor, escolha um nome diferente')

    def validate_email(self, email):
        email = User.query.filter_by(email=email.data).first()
        if email:
            raise ValidationError('Esse email já está cadastrado.')        

class PostForm(FlaskForm):
    title = StringField("Título:", validators=[DataRequired()])
    content = TextAreaField("Conteúdo:", validators=[DataRequired()])
    picture = FileField("Deseja adicionar/mudar uma foto?", validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Postar')


class UpdateAccountForm(FlaskForm):
    username = StringField("Novo Usuário:", validators=[DataRequired(), Length(min=2, max=20)])
    name = StringField("Novo Nome:", validators=[DataRequired()])
    card = TextAreaField("Novo Card:")
    picture = FileField("Mudar foto de Perfil", validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Atualizar')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Esse usuário já existe. Por favor, escolha um nome diferente')

class CommentForm(FlaskForm):
    content = TextAreaField("Escreva um comentário:", validators=[DataRequired()])
    picture = FileField("Deseja adicionar/mudar uma foto?", validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Enviar')

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')