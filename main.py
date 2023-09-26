from flask import Flask, render_template, abort, flash, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager, login_user, UserMixin, current_user, logout_user
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import requests

from form import RegisterForm, LoginForm, BookForm

key = "AIzaSyBDHmv_vq36DeMkCrvmPTY89uaqtUXlEMA"
app = Flask(__name__)
app.config["SECRET_KEY"] = "ds321WQdas124AS;CokweqwSA"
Bootstrap5(app)

# Configure Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
db = SQLAlchemy()
db.init_app(app)

# Configure authentication
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))

    posts = relationship("BookPost", back_populates="author")


class BookPost(UserMixin, db.Model):
    __tablename__ = "book_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    book_author = db.Column(db.String(250), nullable=False)
    genre = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(250), nullable=False)
    condition = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    all_books = db.session.execute(db.select(BookPost).order_by(BookPost.title)).scalars()
    return render_template("index.html", all_books=all_books)


@app.route("/add_book", methods=["POST", "GET"])
def add_book():
    form = BookForm()
    if form.validate_on_submit():
        return redirect(url_for("select", book_author=form.book_author.data, title=form.title.data))
    return render_template("add_book.html", form=form)


@app.route("/select", methods=["POST", "GET"])
def select():
    title = request.args.get("title")
    book_author = request.args.get("book_author")
    url = f"https://www.googleapis.com/books/v1/volumes?q={title}+inauthor:{book_author}&orderBy=relevance&langRestrict=en&key={key}"
    data = requests.get(url).json()["items"]
    print(data[0]["volumeInfo"]["imageLinks"])
    return render_template("select.html", books=data)


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function


@app.route("/register", methods=["POST", "GET"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        # Check if user email is already in the database.
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if user:
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        pwd = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=pwd,
        )
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)

        return redirect((url_for("home")))

    return render_template("register.html", form=form, user_authenticated=current_user.is_authenticated)


@app.route("/login", methods=["POST", "GET"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()

        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for("login"))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for("login"))
        else:
            login_user(user)
            return redirect((url_for("home")))

    return render_template("login.html", form=form, user_authenticated=current_user.is_authenticated)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
