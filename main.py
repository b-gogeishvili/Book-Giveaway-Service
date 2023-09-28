# External Imports
from flask import Flask, render_template, flash, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager, login_user, UserMixin, current_user, logout_user
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import datetime as dt
import smtplib
# Local Imports
from form import RegisterForm, LoginForm, BookForm, EditForm

# Initial Config
API_KEY = "AIzaSyBDHmv_vq36DeMkCrvmPTY89uaqtUXlEMA"
app = Flask(__name__)
app.config["SECRET_KEY"] = "ds321WQdas124AS;CokweqwSA"
Bootstrap5(app)

# GMAIL TEST ACCOUNT
GMAIL_ACCOUNT = "testforpython999@gmail.com"
GMAIL_PASSWORD = "fger kqni xcrc csko "
# SMTP SERVER INFO
GMAIL_SMTP_SERVER = "smtp.gmail.com"
PORT = 587

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


# <--- Start of Database Entries --->

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))

    posts = relationship("BookPost", back_populates="author")
    wishes = relationship("UserWish", back_populates="user_wish")


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


class UserWish(db.Model):
    __tablename__ = "user_wish"
    id = db.Column(db.String, unique=True, primary_key=True)
    time = db.Column(db.String(30), nullable=False)

    user_wish_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user_wish = relationship("User", back_populates="wishes")

    book_wish_id = db.Column(db.Integer, db.ForeignKey("book_posts.id"))
    book_wish = relationship("BookPost", back_populates="wishes")

    send_wish_to = db.Column(db.Integer, unique=False)


with app.app_context():
    db.create_all()


# <--- End of Database Entries --->


# <--- Home --->
@app.route("/")
def home():
    all_books = BookPost.query.order_by(BookPost.title).all()
    return render_template("index.html", all_books=all_books)


# <--- Search, Filter and Sort --->
@app.route("/sort")
def sort():
    sort_by = request.args.get("sort_by")
    if sort_by == "time":
        all_books = BookPost.query.order_by(BookPost.id.desc()).all()
    else:
        all_books = all_books = BookPost.query.order_by(BookPost.rating.desc()).all()

    return render_template("index.html", all_books=all_books)


@app.route("/filter-by")
def filter():
    filterBy = request.args.get("filter_by")
    all_books = BookPost.query.filter_by(condition=filterBy).all()

    return render_template("index.html", all_books=all_books)


@app.route("/search", methods=["POST"])
def search():
    title = request.form["title"]
    all_books = BookPost.query.filter_by(title=title).all()

    return render_template("index.html", all_books=all_books)

# <--- NavBar Routes --->
@app.route("/my-books")
def my_books():
    all_books = BookPost.query.filter_by(author_id=current_user.id).all()
    return render_template("user_books.html", all_books=all_books)


@app.route("/wishlist")
def wishlist():
    wishes = db.session.execute(db.Select(UserWish)).scalars().all()
    return render_template("wishlist.html", books_to_display=wishes)


@app.route("/requests")
def reqs():
    all_reqs = db.session.execute(db.Select(UserWish)).scalars().all()
    return render_template("requests.html", books_to_display=all_reqs)


@app.route("/delete-req", methods=["POST", "GET"])
def delete_req():
    req_id = request.args.get("req_id")
    req_to_delete = db.get_or_404(UserWish, req_id)
    db.session.delete(req_to_delete)
    db.session.commit()

    return redirect(url_for('reqs'))


@app.route("/accept-req", methods=["POST", "GET"])
def accept_req():
    user_email = request.args.get("user_email")
    book_title = request.args.get("book_title")
    book_loc = request.args.get("book_loc")
    book_owner_email = request.args.get("book_owner_email")
    book_id = request.args.get("book_id")

    # Send Mail To Accepted User
    with smtplib.SMTP(GMAIL_SMTP_SERVER, PORT) as server:
        server.starttls()
        server.login(GMAIL_ACCOUNT, GMAIL_PASSWORD)
        server.sendmail(
            from_addr=GMAIL_ACCOUNT,
            to_addrs=user_email,
            msg=f"Subject:{book_title} is available for pick-up\n\n"
                f"Your requested book - {book_title} is available for pickup at "
                f"{book_loc} from 9:00 am to 18:00 pm. You can contact book owner at - "
                f"{book_owner_email}"
                f"\n\nThanks for using our service!"
        )

    # Delete Both Book And Request
    reqs_to_delete = UserWish.query.filter_by(book_wish_id=book_id).all()
    for req in reqs_to_delete:
        db.session.delete(req)
    db.session.commit()

    book_to_delete = db.get_or_404(BookPost, book_id)
    db.session.delete(book_to_delete)
    db.session.commit()

    return redirect(url_for('reqs'))


# <--- Adding Books --->
@app.route("/add-book", methods=["POST", "GET"])
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

    # Google Books API
    url = (f"https://www.googleapis.com/books/v1/volumes?q={title}+inauthor:{book_author}&orderBy=relevance"
           f"&langRestrict=en&key={API_KEY}")
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


# <--- Managing Books --->
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
    already_added = False

    book_wish_id = request.args.get("book_id")
    user_wish_id = request.args.get("current_user_id")
    send_wish_to = request.args.get("user_id")
    wish_id = str(user_wish_id) + str(book_wish_id)

    result = db.session.execute(db.select(UserWish).where(UserWish.id == wish_id)).scalar()
    if not result:
        NOW = dt.datetime.now().strftime("%m/%d/%Y - %H:%M")
        new_wish = UserWish(
            id=wish_id,
            time=NOW,
            user_wish_id=user_wish_id,
            book_wish_id=book_wish_id,
            send_wish_to=send_wish_to
        )
        db.session.add(new_wish)
        db.session.commit()
    else:
        # If its already added, wishlist page should output that message
        book = result.book_wish.title
        already_added = True
        return redirect(url_for("wishlist", added=already_added, book=book))

    return redirect(url_for("wishlist"))


# <--- Authentication --->
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
