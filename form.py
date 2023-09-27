# Setting Up Flask_WTF Forms
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField, SelectField
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
    condition = SelectField("Condition",
                            choices=["New", "Like New", "Very Good", "Good", "Acceptable", "Bad"],
                            validators=[DataRequired()]
                            )
    loc = StringField("Available for pickup at", validators=[DataRequired()])
    submit = SubmitField("Add My Book!")


class EditForm(FlaskForm):
    condition = StringField("Condition", validators=[DataRequired()])
    loc = StringField("Available for pickup at", validators=[DataRequired()])
    submit = SubmitField("Edit!")
