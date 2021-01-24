#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# connect to a local postgresql database
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref="venue", lazy=True)
    
    def __repr__(self):
      return f'<Venue ID: {self.id}, name: {self.name}, city: {self.city}, state: {self.state}, address: {self.address}, phone: {self.phone}, genres: {self.genres}>'

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref="artist", lazy=True)

    def __repr__(self):
      return f'<Artist ID: {self.id}, name: {self.name}, city: {self.city}, state: {self.state}, phone: {self.phone}, genres: {self.genres}>'

class Show(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
      return '<Show {}{}>'.format(self.artist_id, self.venue_id)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  venues = Venue.query.with_entities(Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
  data = []

  for venue in venues:
    venues_city = Venue.query.filter_by(city=venue.city).filter_by(state=venue.state).all()
    venues_area = []

    for venue_city in venues_city:
      upcoming = Show.query.filter_by(venue_id=venue_city.id).filter(Show.start_time > datetime.now())
      venues_area.append({
        "id": venue_city.id,
        "name": venue_city.name,
        "num_upcoming_shows": upcoming.count()
      })

    data.append({
      "city": venue.city,
      "state": venue.state,
      "venues": venues_area
    })

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%'))
  data = []

  if venues.count() > 0:
    for venue in venues:
      upcoming = Show.query.filter_by(venue_id=venue.id).filter(Show.start_time > datetime.now())
      data.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": upcoming.count(),
      })
    
    response = {
      "count": venues.count(),
      "data": data
    }
  else: 
    response = {
      "count": venues.count()
    }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)
  
  upcoming_shows_artists = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time>datetime.now()).all()
  past_shows_artists = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time<datetime.now()).all()
  
  upcoming_shows = []
  past_shows = []

  for show in past_shows_artists:
    past_shows.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
    })

  for show in upcoming_shows_artists:
    upcoming_shows.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
    })

  venue_data = {
      "id": venue.id,
      "name": venue.name,
      "genres": venue.genres[1:-1].split(','),
      "address": venue.address,
      "city": venue.city,
      "state": venue.state,
      "phone": venue.phone,
      "website": venue.website,
      "facebook_link": venue.facebook_link,
      "seeking_talent": venue.seeking_talent,
      "seeking_description": venue.seeking_description,
      "image_link": venue.image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows),
  }

  return render_template('pages/show_venue.html', venue=venue_data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error=False
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    image_link = request.form['image_link']
    facebook_link = request.form['facebook_link']
    website = request.form['website']
    seeking_talent = True if 'seeking_talent' in request.form else False
    seeking_description = request.form['seeking_description']

    venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres, facebook_link=facebook_link, image_link=image_link, website=website, seeking_talent=seeking_talent, seeking_description=seeking_description)
    db.session.add(venue)
    db.session.commit()

  except:
    error=True
    db.session.rollback()
    print(sys.exc_info())

  finally:
    db.session.close()
    
  if error:
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')

  if not error:
    flash('Venue ' + request.form['name'] + ' was successfully listed!.')

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  error = False

  try: 
    venue = Venue.query.get(venue_id)
    shows = Show.query.filter_by(venue_id=venue_id).all()
    for show in shows:
      db.session.delete(show)
    db.session.delete(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue could not be deleted.')
 
  # It doesn't redirect and I don't know why actutally
  return redirect(url_for('home'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = Artist.query.all()
  data = []

  for artist in artists:
    data.append({
      "id": artist.id,
      "name": artist.name,
    })

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')
  artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%'))
  data = []

  if artists.count() > 0:
    for artist in artists:
      upcoming = Show.query.filter_by(artist_id=artist.id).filter(Show.start_time > datetime.now())
      data.append({
        "id": artist.id,
        "name": artist.name,
        "num_upcoming_shows": upcoming.count(),
      })
    
    response = {
      "count": artists.count(),
      "data": data
    }
  else: 
    response = {
      "count": artists.count(),
      "data": []
    }
  
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)
  artist_data = []

  upcoming_shows_venues = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.now()).all()
  past_shows_venues = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time<datetime.now()).all()
  
  upcoming_shows = []
  past_shows = []

  for show in past_shows_venues:
    past_shows.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
    })

  for show in upcoming_shows_venues:
    upcoming_shows.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
    })

  artist_data = {
      "id": artist.id,
      "name": artist.name,
      "genres": artist.genres[1:-1].split(','),
      "city": artist.city,
      "state": artist.state,
      "phone": artist.phone,
      "facebook_link": artist.facebook_link,
      "seeking_venue": artist.seeking_venue,
      "seeking_description": artist.seeking_description,
      "image_link": artist.image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows),
  }

  return render_template('pages/show_artist.html', artist=artist_data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  
  form.id = artist.id
  form.name = artist.name
  form.city = artist.city
  form.state = artist.state
  form.phone = artist.phone
  form.genres = artist.genres
  form.facebook_link = artist.facebook_link
  form.image_link = artist.image_link
  form.seeking_venue = artist.seeking_venue
  form.seeking_description = artist.seeking_description

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  artist = Artist.query.get(artist_id)
  error = False
  try:
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.address = request.form['address']
    artist.phone = request.form['phone']
    artist.genres = request.form['genres']
    artist.image_link = request.form['image_link']
    artist.facebook_link = request.form['facebook_link']
    artist.seeking_description = request.form['seeking_description']
    artist.seeking_venue = request.form['seeking_venue']
    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
    
  finally:
    db.session.close()
    
  if error:
    flash('An error occurred. Artist ' + request.form['name']+ ' could not be changed.')

  if not error:
    flash('Artist ' + request.form['name'] + ' was successfully changed!.')

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  
  form.id = venue.id
  form.name = venue.name
  form.city = venue.city
  form.state = venue.state
  form.phone = venue.phone
  form.genres = venue.genres
  form.facebook_link = venue.facebook_link
  form.image_link = venue.image_link
  form.seeking_venue = venue.seeking_venue
  form.seeking_description = venue.seeking_description
  
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  venue = Venue.query.get(venue_id)
  error = False
  try:
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.genres = request.form['genres']
    venue.image_link = request.form['image_link']
    venue.facebook_link = request.form['facebook_link']
    venue.website = request.form['website']
    venue.seeking_description = request.form['seeking_description']
    venue.seeking_venue = request.form['seeking_venue']
    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
    
  finally:
    db.session.close()
    
  if error:
    flash('An error occurred. Venue ' + request.form['name']+ ' could not be changed.')

  if not error:
    flash('Venue ' + request.form['name'] + ' was successfully changed!.')

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error=False
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    image_link = request.form['image_link']
    seeking_venue = True if 'seeking_venue' in request.form else False
    seeking_description = request.form['seeking_description']

    artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=facebook_link, image_link=image_link, seeking_venue=seeking_venue, seeking_description=seeking_description)
    db.session.add(artist)
    db.session.commit()

  except:
    error=True
    db.session.rollback()
    print(sys.exc_info())

  finally:
    db.session.close()
    
  if error:
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')

  if not error:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')

  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows

  shows = db.session.query(Show).join(Artist).join(Venue).all()
  data = []

  for show in shows:
    data.append({
      "venue_id": show.venue.id,
      "venue_name": show.venue.name,
      "artist_id": show.artist.id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
    })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  try:
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']
    show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)

    db.session.add(show)
    db.session.commit()

  except:
    error=True
    db.session.rollback()
    print(sys.exc_info())

  finally:
    db.session.close()
    
  if error:
    flash('An error occurred. Show could not be listed.')

  if not error:
    flash('Show was successfully listed!')

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
