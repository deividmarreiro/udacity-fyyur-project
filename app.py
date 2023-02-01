# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import logging
from logging import FileHandler, Formatter

import babel
import dateutil.parser
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ARRAY

from forms import ArtistForm, ShowForm, VenueForm

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object("config")
db: SQLAlchemy = SQLAlchemy(app)
migrate = Migrate(app, db)

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = "venues"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    genres = db.Column(ARRAY(db.String), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String(120), nullable=False)
    seeking_talent = db.Column(db.Boolean, default=False, nullable=False)
    seeking_description = db.Column(db.String(500), nullable=False)
    image_link = db.Column(db.String(500), nullable=False)
    facebook_link = db.Column(db.String(120), nullable=False)
    shows = db.relationship("Show", backref="venue", lazy=True)

    def __repr__(self) -> str:
        return f"<Venue id: {self.id} name: {self.name}>"


class Artist(db.Model):
    __tablename__ = "artists"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    genres = db.Column(ARRAY(db.String), nullable=False)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120), nullable=False)
    seeking_venue = db.Column(db.Boolean, default=False, nullable=False)
    seeking_description = db.Column(db.String(500), nullable=False)
    shows = db.relationship("Show", backref="artist", lazy=True)


class Show(db.Model):
    __tablename__ = "shows"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey("artists.id"), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey("venues.id"), nullable=False)


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format="medium"):
    date = dateutil.parser.parse(value)
    if format == "full":
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == "medium":
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale="en")


app.jinja_env.filters["datetime"] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route("/")
def index():
    return render_template("pages/home.html")


#  Venues
#  ----------------------------------------------------------------


@app.route("/venues")
def venues():
    # TODO: Upcoming Shows.
    #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    venue_areas: list[Venue] = Venue.query.distinct(Venue.city, Venue.state).all()
    areas = []
    for venue_area in venue_areas:
        venues_result = Venue.query.filter(Venue.state == venue_area.state).filter(Venue.city == venue_area.city).all()
        areas.append({"city": venue_area.city, "state": venue_area.state, "venues": [{"id": venue.id, "name": venue.name, "num_upcoming_shows": 0} for venue in venues_result]})
    return render_template("pages/venues.html", areas=areas)


@app.route("/venues/search", methods=["POST"])
def search_venues():
    # TODO: Upcoming Shows.
    search_term = request.form.get("search_term")
    results = Venue.query.filter(Venue.name.ilike(f"%{search_term}%")).all()
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    response = {"count": len(results), "data": [{"id": result.id, "name": result.name, "num_upcoming_shows": 0} for result in results]}
    return render_template(
        "pages/search_venues.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/venues/<int:venue_id>")
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: Upcoming Shows and Past Shows.
    venue: Venue = Venue.query.get_or_404(venue_id)
    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": [],
        "upcoming_shows": [],
        "past_shows_count": 0,
        "upcoming_shows_count": 0,
    }
    return render_template("pages/show_venue.html", venue=data)


#  Create Venue
#  ----------------------------------------------------------------


@app.route("/venues/create", methods=["GET"])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():
    error = False
    try:
        venue = Venue(
            name=request.form.get("name"),
            genres=request.form.getlist("genres"),
            address=request.form.get("address"),
            city=request.form.get("city"),
            state=request.form.get("state"),
            phone=request.form.get("phone"),
            website=request.form.get("website_link"),
            seeking_talent=True if request.form.get("seeking_talent") else False,
            seeking_description=request.form.get("seeking_description"),
            image_link=request.form.get("image_link"),
            facebook_link=request.form.get("facebook_link"),
        )
        db.session.add(venue)
        db.session.commit()
    except Exception as e:
        error = True
        db.session.rollback()
        flash(f"Venue {request.form.get('name')} was unsuccessfully listed! because {e}")
    finally:
        db.session.close()
    if not error:
        # on successful db insert, flash success
        flash("Venue " + request.form.get("name") + " was successfully listed!")
    return render_template("pages/home.html")


@app.route("/venues/<venue_id>", methods=["DELETE", "POST"])
def delete_venue(venue_id):
    error = False
    try:
        venue = Venue.query.get_or_404(venue_id)
        db.session.delete(venue)
        db.session.commit()
        print("Commited")
    except Exception as e:
        error = True
        db.session.rollback()
        flash(f"Venue {request.form.get('name')} was unsuccessfully deleted! because {e}")
    finally:
        db.session.close()
    if not error:
        flash("Venue " + venue.name + " was successfully deleted!")
    return render_template("pages/home.html"), 204


#  Artists
#  ----------------------------------------------------------------
@app.route("/artists")
def artists():
    artists = Artist.query.all()
    data = [{"id": artist.id, "name": artist.name} for artist in artists]
    return render_template("pages/artists.html", artists=data)


@app.route("/artists/search", methods=["POST"])
def search_artists():
    # TODO: Upcoming Shows.
    search_term = request.form.get("search_term")
    results = Artist.query.filter(Artist.name.ilike(f"%{search_term}%")).all()
    response = {"count": len(results), "data": [{"id": result.id, "name": result.name, "num_upcoming_shows": 0} for result in results]}
    return render_template(
        "pages/search_artists.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: Upcoming Shows.
    artist: Artist = Artist.query.get_or_404(artist_id)

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": [
            {
                "venue_id": 1,
                "venue_name": "The Musical Hop",
                "venue_image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
                "start_time": "2019-05-21T21:30:00.000Z",
            }
        ],
        "upcoming_shows": [],
        "past_shows_count": 1,
        "upcoming_shows_count": 0,
    }

    return render_template("pages/show_artist.html", artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    result: Artist = Artist.query.get_or_404(artist_id)
    form = ArtistForm(obj=result)
    artist = {
        "id": result.id,
        "name": result.name,
        "genres": result.genres,
        "city": result.city,
        "state": result.state,
        "phone": result.state,
        "website": result.website,
        "facebook_link": result.facebook_link,
        "seeking_venue": result.seeking_venue,
        "seeking_description": result.seeking_description,
        "image_link": result.image_link,
    }
    return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    error = False
    try:
        artist: Artist = Artist.query.get_or_404(artist_id)
        artist.name = request.form.get("name")
        artist.city = request.form.get("city")
        artist.state = request.form.get("state")
        artist.address = request.form.get("address")
        artist.phone = request.form.get("phone")
        artist.genres = request.form.getlist("genres")
        artist.facebook_link = request.form.get("facebook_link")
        artist.image_link = request.form.get("image_link")
        artist.website = request.form.get("website_link")
        artist.seeking_talent = True if request.form.get("seeking_talent", None) else False
        artist.seeking_description = request.form.get("seeking_description")
        db.session.add(artist)
        db.session.commit()
    except Exception as e:
        error = True
        db.session.rollback()
        flash(f"Artist {request.form.get('name')} was unsuccessfully edited! because {e}")
    finally:
        db.session.close()
    if not error:
        flash("Artist " + request.form.get("name") + " was successfully edited!")
    return redirect(url_for("show_artist", artist_id=artist_id))


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    result: Venue = Venue.query.get_or_404(venue_id)
    form = VenueForm(obj=result)
    venue = {
        "id": result.id,
        "name": result.name,
        "genres": result.genres,
        "address": result.address,
        "city": result.city,
        "state": result.state,
        "phone": result.phone,
        "website": result.website,
        "facebook_link": result.facebook_link,
        "seeking_talent": result.seeking_talent,
        "seeking_description": result.seeking_description,
        "image_link": result.image_link,
    }
    return render_template("forms/edit_venue.html", form=form, venue=venue)


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    error = False
    try:
        venue: Venue = Venue.query.get_or_404(venue_id)
        venue.name = request.form.get("name")
        venue.city = request.form.get("city")
        venue.state = request.form.get("state")
        venue.address = request.form.get("address")
        venue.phone = request.form.get("phone")
        venue.genres = request.form.getlist("genres")
        venue.facebook_link = request.form.get("facebook_link")
        venue.image_link = request.form.get("image_link")
        venue.website = request.form.get("website_link")
        venue.seeking_talent = True if request.form.get("seeking_talent", None) else False
        venue.seeking_description = request.form.get("seeking_description")
        db.session.add(venue)
        db.session.commit()
    except Exception as e:
        error = True
        db.session.rollback()
        flash(f"Venue {request.form.get('name')} was unsuccessfully edited! because {e}")
    finally:
        db.session.close()
    if not error:
        # on successful db insert, flash success
        flash("Venue " + request.form.get("name") + " was successfully edited!")
    return redirect(url_for("show_venue", venue_id=venue_id))
    # venue record with ID <venue_id> using the new attributes


#  Create Artist
#  ----------------------------------------------------------------


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    error = False
    try:
        artist = Artist(
            name=request.form.get("name"),
            genres=request.form.getlist("genres"),
            city=request.form.get("city"),
            state=request.form.get("state"),
            phone=request.form.get("phone"),
            website=request.form.get("website_link"),
            image_link=request.form.get("image_link"),
            facebook_link=request.form.get("facebook_link"),
            seeking_venue=True if request.form.get("seeking_venue") else False,
            seeking_description=request.form.get("seeking_description"),
        )
        db.session.add(artist)
        db.session.commit()
    except Exception as e:
        error = True
        db.session.rollback()
        flash(f"Artist {request.form.get('name')} was unsuccessfully listed! because {e}")
    finally:
        db.session.close()
    if not error:
        # on successful db insert, flash success
        flash("Artist " + request.form.get("name") + " was successfully listed!")
    return render_template("pages/home.html")


#  Shows
#  ----------------------------------------------------------------


@app.route("/shows")
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    data = [
        {
            "venue_id": 1,
            "venue_name": "The Musical Hop",
            "artist_id": 4,
            "artist_name": "Guns N Petals",
            "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
            "start_time": "2019-05-21T21:30:00.000Z",
        },
        {
            "venue_id": 3,
            "venue_name": "Park Square Live Music & Coffee",
            "artist_id": 5,
            "artist_name": "Matt Quevedo",
            "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
            "start_time": "2019-06-15T23:00:00.000Z",
        },
        {
            "venue_id": 3,
            "venue_name": "Park Square Live Music & Coffee",
            "artist_id": 6,
            "artist_name": "The Wild Sax Band",
            "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
            "start_time": "2035-04-01T20:00:00.000Z",
        },
        {
            "venue_id": 3,
            "venue_name": "Park Square Live Music & Coffee",
            "artist_id": 6,
            "artist_name": "The Wild Sax Band",
            "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
            "start_time": "2035-04-08T20:00:00.000Z",
        },
        {
            "venue_id": 3,
            "venue_name": "Park Square Live Music & Coffee",
            "artist_id": 6,
            "artist_name": "The Wild Sax Band",
            "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
            "start_time": "2035-04-15T20:00:00.000Z",
        },
    ]
    return render_template("pages/shows.html", shows=data)


@app.route("/shows/create")
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead

    # on successful db insert, flash success
    flash("Show was successfully listed!")
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template("pages/home.html")


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500


if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == "__main__":
    app.run()

# Or specify port manually:
"""
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
"""
