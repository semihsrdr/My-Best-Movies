from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField,FloatField,URLField
from wtforms.validators import DataRequired
import requests


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

api_key="84bc20f65328a210ea788f7fcd266869"
api_token="eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI4NGJjMjBmNjUzMjhhMjEwZWE3ODhmN2ZjZDI2Njg2OSIsInN1YiI6IjY2MmY5YWUwMDI4ZjE0MDEyNTY5NTRhYSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.yj9vGc7oBGwKw_b6qhgtbzcMRXNZnetX-muuZJ2ObaI"

# CREATE DB
class Base(DeclarativeBase):
    pass

app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///my-movie-library.db"
db=SQLAlchemy(model_class=Base)
db.init_app(app)

# CREATE TABLE
class Movie(db.Model):
    id:Mapped[int]=mapped_column(Integer,nullable=False,primary_key=True)
    title:Mapped[str]=mapped_column(String,nullable=False,unique=True)
    year:Mapped[int]=mapped_column(Integer,nullable=False)
    description:Mapped[str]=mapped_column(String,nullable=False)
    rating:Mapped[float]=mapped_column(Float,nullable=False)
    review:Mapped[str]=mapped_column(String,nullable=False)
    img_url:Mapped[str]=mapped_column(String,nullable=False)

    def __repr__(self):
        return f'<Movie {self.title}>'

# Create Form
class MovieForm(FlaskForm):
    title=StringField('Title',validators=[DataRequired()],render_kw={"placeholder": "eg. Harry Potter"})
    submit=SubmitField("Add")


class RateMovieForm(FlaskForm):
    rating=FloatField("Your Rating Out of 10 e.g. 7.5",validators=[DataRequired()],render_kw={"placeholder":"Rating"})
    review = StringField("Your Review",validators=[DataRequired()],render_kw={"placeholder":"Review"})
    submit=SubmitField("Submit")
with app.app_context():
    db.create_all()


@app.route("/")
def home():
    all_movies=Movie.query.order_by(Movie.rating.asc()).all()
    return render_template("index.html",movies=all_movies)

@app.route("/edit/<int:id>",methods=["POST","GET"])
def edit(id):
    selected_movie=db.session.execute(db.select(Movie).where(Movie.id==id)).scalar()
    form=RateMovieForm()
    if form.validate_on_submit():
        selected_movie.rating=form.rating.data
        selected_movie.review=form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html",form=form,selected_movie=selected_movie)

@app.route("/add_review/<int:id>",methods=["POST","GET"])
def add_review(id):
    form = RateMovieForm()
    if form.validate_on_submit():
        base_url = "https://image.tmdb.org/t/p/original/"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {api_token}"
        }
        response=requests.get(url=f"https://api.themoviedb.org/3/movie/{id}",headers=headers)
        data=response.json()
        full_url = base_url + data["poster_path"]
        new_movie=Movie(title=data["original_title"],year=data["release_date"],img_url=full_url,description=data["overview"],
                        rating=form.rating.data,
                        review=form.review.data,
                        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("add_review.html",form=form)


@app.route("/select/<path:title>",methods=["POST","GET"])
def select(title):
    url = "https://api.themoviedb.org/3/search/movie?"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_token}",
    }
    params={
        "query":title.lower()
    }
    response = requests.get(url, headers=headers,params=params)
    data=response.json()["results"]

    return render_template("select.html",movies=data)

@app.route("/delete/<int:id>")
def delete(id):
    selected_movie=db.session.execute(db.select(Movie).where(Movie.id==id)).scalar()
    db.session.delete(selected_movie)
    db.session.commit()
    return redirect(url_for('home'))

@app.route("/add",methods=["POST","GET"])
def add():
    form=MovieForm()

    if request.method=="POST":
        if form.validate_on_submit():
            title=form.title.data
            return redirect(url_for("select",title=title))
    return render_template("add.html",form=form)


if __name__ == '__main__':
    app.run(debug=True,host="localhost",port=7000)
