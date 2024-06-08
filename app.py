# External Imports
from flask import Flask, render_template, flash, redirect, url_for, request, Blueprint
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_bootstrap import Bootstrap5
from flask_restx import Resource, Namespace, fields, Api
from flask_login import LoginManager, login_user, UserMixin, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import datetime as dt
import smtplib
# Local Imports
from form import RegisterForm, LoginForm, BookForm, EditForm

# May need
# Werkzeug==2.3.7

# Initial Config
API_KEY = "AIzaSyBDHmv_vq36DeMkCrvmPTY89uaqtUXlEMA"
app = Flask(__name__)
app.config["SECRET_KEY"] = "ds321WQdas124AS;CokweqwSA"
Bootstrap5(app)
blueprint = Blueprint("Book Library Api", __name__, url_prefix="/swagger")

# GMAIL TEST ACCOUNT
GMAIL_ACCOUNT = "testforpython999@gmail.com"
GMAIL_PASSWORD = "fger kqni xcrc csko "
# SMTP SERVER INFO
GMAIL_SMTP_SERVER = "smtp.gmail.com"
PORT = 587

# Configure API
api = Api(blueprint)
ns = Namespace("api")
app.register_blueprint(blueprint)
api.add_namespace(ns)

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

class User(db.Model, UserMixin):
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


# <--- SWAGGER API --->


# API Models

book_model = api.model("Books", {
    "id": fields.Integer,
    "title": fields.String,
    "book_author": fields.String,
    "description": fields.String,
    "loc": fields.String,
    "rating": fields.String,
    "condition": fields.String,
    "img_url": fields.String,
    "author_id": fields.Integer
})

book_input_model = api.model("BookInput", {
    "title": fields.String,
    "book_author": fields.String,
    "description": fields.String,
    "loc": fields.String,
    "rating": fields.String,
    "condition": fields.String,
    "img_url": fields.String,
})

book_patch_model = api.model("BookPatchInput", {
    "loc": fields.String,
    "condition": fields.String,
})

user_model = api.model("Users", {
    "id": fields.Integer,
    "email": fields.String,
    "name": fields.String,
})

user_posts_model = api.model("UserWithBooks", {
    "id": fields.Integer,
    "email": fields.String,
    "name": fields.String,
    "posts": fields.List(fields.Nested(book_model))
})


# API Routes and Methods

@ns.route("/users")
class UserListAPI(Resource):
    @ns.marshal_list_with(user_model)
    def get(self):
        return User.query.all()


@ns.route("/users_posts")
class UserAndPostsAPI(Resource):
    @ns.marshal_list_with(user_posts_model)
    def get(self):
        return User.query.all()


@ns.route("/books")
class BookListAPI(Resource):
    @ns.marshal_list_with(book_model)
    def get(self):
        return BookPost.query.all()

    @ns.expect(book_input_model)
    @ns.marshal_with(book_model)
    def post(self):
        book = BookPost(
            title=ns.payload["title"],
            book_author=ns.payload["book_author"],
            description=ns.payload["description"],
            loc=ns.payload["loc"],
            rating=ns.payload["rating"],
            condition=ns.payload["condition"],
            img_url=ns.payload["img_url"],
            author_id=current_user.id

        )
        db.session.add(book)
        db.session.commit()
        return book, 201


@ns.route("/books/<int:id>")
class BookIdAPI(Resource):
    @ns.marshal_list_with(book_model)
    def get(self, id):
        return BookPost.query.get(id)

    @ns.expect(book_patch_model)
    @ns.marshal_with(book_model)
    def patch(self, id):
        book = BookPost.query.get(id)
        book.loc = ns.payload["loc"]
        book.condition = ns.payload["condition"]
        db.session.commit()
        return book

    def delete(self, id):
        book = BookPost.query.get(id)
        db.session.delete(book)
        db.session.commit()
        return {}, 204


@ns.route("/books/filter_by_author/<string:book_author>")
class BookAuthorFilter(Resource):
    @ns.marshal_list_with(book_model)
    def get(self, book_author):
        book = BookPost.query.filter_by(book_author=book_author).all()
        print(book)
        return book


@ns.route("/books/filter_by_condition/<string:condition>")
class BookConditionFilter(Resource):
    @ns.marshal_list_with(book_model)
    def get(self, condition):
        book = BookPost.query.filter_by(condition=condition).all()
        print(book)
        return book


# <--- End of API DOC --->


# !!! <--- WEBSITE ---> !!!


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
        all_books = BookPost.query.order_by(BookPost.rating.desc()).all()

    return render_template("index.html", all_books=all_books)


@app.route("/filter-by")
def filter_query_by():
    filter_queries = request.args.get("filter_by")
    all_books = BookPost.query.filter_by(condition=filter_queries).all()

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
    book_wish_id = request.args.get("book_id")
    user_wish_id = request.args.get("current_user_id")
    send_wish_to = request.args.get("user_id")
    wish_id = str(user_wish_id) + str(book_wish_id)

    result = db.session.execute(db.select(UserWish).where(UserWish.id == wish_id)).scalar()
    if not result:
        now = dt.datetime.now().strftime("%m/%d/%Y - %H:%M")
        new_wish = UserWish(
            id=wish_id,
            time=now,
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


@app.route("/not_authenticated")
def not_authenticated():
    return render_template("not_authenticated.html")


if __name__ == "__main__":
    app.run()
