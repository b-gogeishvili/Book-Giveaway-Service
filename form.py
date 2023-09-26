from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email
import email_validator


class RegisterForm(FlaskForm):
    name = StringField("Enter Your Userame", validators=[DataRequired()])
    email = EmailField("Enter Your Email", validators=[DataRequired(), Email()])
    password = PasswordField("Create Password", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!")


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let Me In!")


class BookForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    book_author = StringField("Author", validators=[DataRequired()])
    submit = SubmitField("Add My Book!")
