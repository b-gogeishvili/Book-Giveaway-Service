from flask import Flask, render_template, flash, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager, login_user, UserMixin, current_user, logout_user
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
import requests

from form import RegisterForm, LoginForm, BookForm, EditForm

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
    wishes = relationship("UserWish", back_populates="user_wish")
    # reqs = relationship("UserReq", back_populates="user_req")


class BookPost(db.Model):
    __tablename__ = "book_posts"
    id = db.Column(db.Integer, unique=True, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    book_author = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(250), nullable=False)
    loc = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.String(250), nullable=False)
    condition = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")

    wishes = relationship("UserWish", back_populates="book_wish")
    reqs = relationship("UserReq", back_populates="book_req")


class UserWish(db.Model):
    __tablename__ = "user_wish"
    id = db.Column(db.String, unique=True, primary_key=True)

    user_wish_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user_wish = relationship("User", back_populates="wishes")

    book_wish_id = db.Column(db.Integer, db.ForeignKey("book_posts.id"))
    book_wish = relationship("BookPost", back_populates="wishes")


class UserReq(db.Model):
    __tablename__ = "user_req"
    id = db.Column(db.String, unique=True, primary_key=True)
    req_from = db.Column(db.String)
    req_from_email = db.Column(db.String)

    # user_req_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # user_req = relationship("User", back_populates="reqs")

    book_req_id = db.Column(db.Integer, db.ForeignKey("book_posts.id"))
    book_req = relationship("BookPost", back_populates="reqs")


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
        return redirect(url_for("select",
                                book_author=form.book_author.data,
                                title=form.title.data,
                                condition=form.condition.data, loc=form.loc.data))
    return render_template("add_book.html", form=form)


@app.route("/select", methods=["POST", "GET"])
def select():
    title = request.args.get("title")
    book_author = request.args.get("book_author")
    condition = request.args.get("condition")
    loc = request.args.get("loc")
    url = (f"https://www.googleapis.com/books/v1/volumes?q={title}+inauthor:{book_author}&orderBy=relevance"
           f"&langRestrict=en&key={key}")
    data = requests.get(url).json()["items"]
    return render_template("select.html", books=data, condition=condition, loc=loc)


@app.route("/adding", methods=["POST", "GET"])
def adding():
    new_book = BookPost(
        title=request.args.get("title"),
        book_author=request.args.get("book_author"),
        description=request.args.get("description"),
        rating=request.args.get("rating"),
        loc=request.args.get("loc"),
        condition=request.args.get("condition"),
        img_url=request.args.get("img_url"),
        author=current_user
    )
    db.session.add(new_book)
    db.session.commit()

    return redirect(url_for("home"))


@app.route("/edit/<int:book_id>", methods=["POST", "GET"])
def edit(book_id):
    form = EditForm()

    if form.validate_on_submit():
        book_to_update = db.get_or_404(BookPost, book_id)
        book_to_update.condition = form.condition.data
        book_to_update.loc = form.loc.data
        db.session.commit()

        return redirect(url_for('home'))

    return render_template("edit.html", form=form)


@app.route("/delete", methods=["POST", "GET"])
def delete():
    book_id = request.args.get("book_id")
    book_to_delete = db.get_or_404(BookPost, book_id)
    db.session.delete(book_to_delete)
    db.session.commit()

    return redirect(url_for('home'))


@app.route("/want", methods=["POST", "GET"])
def want():
    book_wish_id = request.args.get("book_id")
    user_wish_id = request.args.get("current_user_id")
    wish_id = str(user_wish_id) + str(book_wish_id)

    result = db.session.execute(db.select(UserWish).where(UserWish.id == wish_id)).scalar()
    if not result:
        new_wish = UserWish(
            id=wish_id,
            user_wish_id=user_wish_id,
            book_wish_id=book_wish_id
        )
        db.session.add(new_wish)
        db.session.commit()
    else:
        flash("Already in your wishlist!")  # fix
        return redirect(url_for("home"))

    book_req_id = book_wish_id
    user_req_id = request.args.get("user_id")
    req_id = str(user_req_id) + str(book_req_id)

    new_req = UserReq(
        id=req_id,
        req_from=current_user.name,
        req_from_email=current_user.email,
        user_req_id=user_req_id,
        book_req_id=book_req_id
    )
    db.session.add(new_req)
    db.session.commit()
    return redirect(url_for("wishlist"))


@app.route("/wishlist")
def wishlist():
    wishes = db.session.execute(db.Select(UserWish)).scalars().all()
    return render_template("wishlist.html", books_to_display=wishes)


@app.route("/requests")
def reqs():
    all_reqs = db.session.execute(db.Select(UserReq)).scalars().all()
    return render_template("requests.html", books_to_display=all_reqs)


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
