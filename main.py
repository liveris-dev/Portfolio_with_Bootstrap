from flask import Flask, render_template, request
import requests
import smtplib
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text


my_email = "tapiagasantonakis@gmail.com"
my_password = os.environ.get('EMAIL_KEY')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')

#CREATE DATABASE
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///projects.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

#CONFIGURE TABLE
class Project(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)


with app.app_context():
    db.create_all()


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


@app.route("/")
def home():
    return render_template("index.html")

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