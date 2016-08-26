from flask import Flask, render_template, request, url_for, redirect, jsonify, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
from imdb_setup import Base, Movie, Person, Roles, User, MoviesWatched
from imdbpie import Imdb

imdb = Imdb()
imdb = Imdb(anonymize=True) # to proxy requests

# Creating an instance with caching enabled
# Note that the cached responses expire every 2 hours or so.
# The API response itself dictates the expiry time)
imdb = Imdb(cache=True)

app = Flask(__name__)

#Create session and connect to the database
engine = create_engine('sqlite:///imdb_recognition.db')
Base.metadata.bind = engine
DBsession = sessionmaker(bind = engine)
session = DBsession()

#fakeuser
user = User(name='Anna')
session.add(user)
session.commit()
#fakeuser end

@app.route('/')
@app.route('/home/', methods=['GET', 'POST'])
def showHomePage():
    if request.method == 'POST':
        search_for = request.form['title']
        return redirect(url_for('showSearchResults', search_for = search_for))
    else:
        return render_template('homepage.html')

@app.route('/search/<string:search_for>/')
def showSearchResults(search_for):
    results = imdb.search_for_title(search_for)
    image_urls = {}
    for r in results:
        image_url = imdb.get_title_by_id(r['imdb_id'])
        if not image_url.poster_url:
            image_urls[r['imdb_id']] = "http://ia.media-imdb.com/images/G/01/imdb/images/nopicture/32x44/film-3119741174._CB282925985_.png"
        else:
            image_urls[r['imdb_id']] = image_url.poster_url
    return render_template('search_results.html', results=results, image_urls=image_urls)

@app.route('/add/', methods= ['POST'])
def addMoviesWatched():
    movie_ids_watched = request.form.getlist('watched')
    for imdb_id in movie_ids_watched:
        title = imdb.get_title_by_id(imdb_id)

        movie = session.query(Movie).filter_by(imdb_id=imdb_id).one_or_none()
        if not movie:
            print "movie not in the database"
            movie = Movie(imdb_id=imdb_id, title = title.title, poster_url=title.poster_url)
            session.add(movie)

            for actor in title.credits:
              if actor.roles:
                  person = Person(name=actor.name, imdb_id=actor.imdb_id)
                  session.add(person)
                  roles = Roles(movie_id=imdb_id, person_id=actor.imdb_id, character_name=" / ".join(actor.roles))
                  session.add(roles)

        added_flag = session.query(MoviesWatched).filter_by(movie_id=imdb_id, user_id=1).one_or_none()
        if not added_flag:
            print "movie not watched yet"
            movies_watched = MoviesWatched(user_id=1, movie_id=imdb_id)
            session.add(movies_watched)

        session.commit()

    return redirect(url_for('showHomePage'))



if __name__ == '__main__':
    #app.secret_key = "super_secret_key"
    app.debug = True

    ## Cryptic stuff to make templates reload
    # import os
    # extra_dirs = ['.',]
    # extra_files = extra_dirs[:]
    # for extra_dir in extra_dirs:
    #     for dirname, dirs, files in os.walk(extra_dir):
    #         for filename in files:
    #             filename = os.path.join(dirname, filename)
    #             if os.path.isfile(filename):
    #                 extra_files.append(filename)
    # app.run(host = '0.0.0.0', port = 5000, extra_files=extra_files)
    ## END Cryptic stuff to make templates reload
    ## No cryptic stuff
    app.run(host = '0.0.0.0', port = 5000)
    ## END No cryptic stuff
