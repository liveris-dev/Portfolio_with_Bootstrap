from flask import Flask, render_template, redirect, url_for, request, abort, flash
import smtplib
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, SubmitField, SelectField, PasswordField
from wtforms.validators import DataRequired, URL, Email
from flask_ckeditor import CKEditor, CKEditorField
from flask_bootstrap import Bootstrap5
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from functools import wraps

my_email = os.environ.get('EMAIL_ADDRESS')
my_password = os.environ.get('EMAIL_KEY')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
Bootstrap5(app)
ckeditor = CKEditor(app)

#CREATE DATABASE
class Base(DeclarativeBase):
    pass
#Add env variable to db uri to use with postgresql on render
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URI', 'sqlite:///projects.db')
db = SQLAlchemy(model_class=Base)
db.init_app(app)

#CONFIGURE FLASK LOGIN MANAGER
login_manager = LoginManager()
login_manager.init_app(app)

#CREATE USER LOADER CALLBACK
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

#CONFIGURE TABLES
class Project(db.Model):
    __tablename__= "projects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Create a foreign key, "users.id" the users refers to the tablename of User.
    author_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"))
    # Create reference to the User object. The "projects" refers to the projects property in the User class.
    author = relationship("User", back_populates="projects")
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(250), nullable=False)
    github: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    # This will act as a list of Project objects attached to each User.The "author" refers to the author property of th Project class.
    projects = relationship("Project", back_populates="author")

with app.app_context():
    db.create_all()

#CREATE WTFORMS
class ProjectForm(FlaskForm):
    title=StringField(label='Project Title', validators=[DataRequired()])
    subtitle=StringField(label='Project Subtitle', validators=[DataRequired()])
    body=CKEditorField(label='Project Body', validators=[DataRequired()])
    category=SelectField(label='Project Category', choices=['App','Game','Website'])
    project_url=StringField(label='Github Link', validators=[DataRequired(), URL()])
    img_url=StringField(label='Image URL', validators=[DataRequired(), URL()])
    submit=SubmitField(label='Submit Project')

class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let Me In!")


#CREATE SEND EMAIL FUNCTION FOR CONTACT
def send_email(name, email, phone, message):
    email_message = f"Subject:Blogspot contact message!\n\nName:{name}\nEmail:{email}\nPhone number:{phone}\nMessage:{message}"
    with smtplib.SMTP("smtp.gmail.com") as connection:
        connection.starttls()
        connection.login(user=my_email, password=my_password)
        connection.sendmail(
            from_addr=my_email,
            to_addrs="lpapagiannidis@hotmail.com",
            msg=email_message
        )

#CREATE ADMIN REQUIRED DECORATOR
def admin_only(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if current_user.is_anonymous or current_user.id != 1:
            return abort(403)
        return f(*args,**kwargs)
    return decorated_function

@app.route("/register", methods=["GET","POST"])
def register_user():
    form = RegisterForm()
    if form.validate_on_submit():
        registered_user = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        if registered_user:
            return redirect(url_for("login"))
        hashed_salted_password = generate_password_hash(password=form.password.data, method="pbkdf2", salt_length=8)
        new_user = User(
            email=form.email.data,
            name = form.name.data,
            password = hashed_salted_password
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("home"))
    return render_template("register.html", form=form)

@app.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        registered_user = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        if registered_user:
            if check_password_hash(pwhash=registered_user.password, password=form.password.data):
                login_user(registered_user)
                return redirect(url_for("home"))
            else:
                flash("The password is incorrect. Please try again.", category="error")
                return redirect(url_for("login"))
        else:
            flash("The email you entered is not registered. Please sign up first.", category="error")
            return redirect(url_for('register_user'))
    return render_template("login.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/")
def home():
    projects = db.session.execute(db.select(Project)).scalars().all()
    return render_template("index.html", all_projects=projects)

@app.route("/all_projects")
def show_all_projects():
    projects = db.session.execute(db.select(Project)).scalars().all()
    return render_template("projects.html", all_projects=projects)

@app.route("/project/<project_id>")
def show_project(project_id):
    requested_project = db.get_or_404(Project, project_id)
    return render_template("project.html", project=requested_project)

#ADD A NEW PROJECT
@app.route("/new_project", methods=["GET","POST"])
@admin_only
def new_project():
    form = ProjectForm()
    if form.validate_on_submit():
        new_project_to_add=Project(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            type=form.category.data,
            github=form.project_url.data,
            img_url=form.img_url.data,
            author_id=current_user.id
        )
        db.session.add(new_project_to_add)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("add-project.html", form=form)

@app.route("/terminate/<project_id>")
@admin_only
def terminate_project(project_id):
    requested_project = db.get_or_404(Project, project_id)
    db.session.delete(requested_project)
    db.session.commit()
    return redirect(url_for('show_all_projects'))

@app.route("/contact", methods=["GET","POST"])
def contact():
    if request.method == "POST":
        data = request.form
        send_email(data["name"], data["email"], data["phone"], data["message"])
        return render_template("contact.html", msg_sent=True)
    else:
        return render_template("contact.html", msg_sent=False)

@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == "__main__":
    app.run(debug=False)