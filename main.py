from enum import unique

from flask import Flask, render_template, redirect, url_for, request
import smtplib
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditor, CKEditorField
from flask_bootstrap import Bootstrap5

my_email = os.environ.get('EMAIL_ADDRESS')
my_password = os.environ.get('EMAIL_KEY')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
Bootstrap5(app)
ckeditor = CKEditor(app)

#CREATE DATABASE
class Base(DeclarativeBase):
    pass
#ADD ENV VARIABLE TO DB URI TO USE WITH POSTGRESQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URI', 'sqlite:///projects.db')
db = SQLAlchemy(model_class=Base)
db.init_app(app)

#CONFIGURE TABLES
class Project(db.Model):
    __tablename__= "projects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Create a foreign key, "users.id" the users refers to the tablename of User.
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    # Create reference to the User object. The "projects" refers to the projects property in the User class.
    author = relationship("User", back_populates="projects")
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(250), nullable=False)
    github: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

class User(db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    # This will act as a list of Project objects attached to each User.The "author" refers to the author property of th Project class.
    projects = relationship("Project", back_populates="author")

with app.app_context():
    db.create_all()

#CREATE WTFORM FOR NEW PROJECT
class ProjectForm(FlaskForm):
    title=StringField(label='Project Title', validators=[DataRequired()])
    subtitle=StringField(label='Project Subtitle', validators=[DataRequired()])
    body=CKEditorField(label='Project Body', validators=[DataRequired()])
    category=SelectField(label='Project Category', choices=['App','Game','Website'])
    project_url=StringField(label='Github Link', validators=[DataRequired(), URL()])
    img_url=StringField(label='Image URL', validators=[DataRequired(), URL()])
    submit=SubmitField(label='Submit Project')

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

#ADD A NEW PROJECT
@app.route("/new_project", methods=["GET","POST"])
def new_project():
    form = ProjectForm()
    if form.validate_on_submit():
        new_project_to_add=Project(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            type=form.category.data,
            github=form.project_url.data,
            img_url=form.img_url.data
        )
        db.session.add(new_project_to_add)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("add-project.html", form=form)



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

@app.route("/terminate/<project_id>")
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
    app.run(debug=True)