from flask import Flask, render_template, request, url_for, redirect, json, jsonify, flash, session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from sqlalchemy import func
from imdb_setup import Base, Movie, Person, Roles, User, MoviesWatched
from config import Auth
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from imdbpie import Imdb
from requests_oauthlib import OAuth2Session
import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

imdb = Imdb()
imdb = Imdb(anonymize=True) # to proxy requests

# Creating an instance with caching enabled
# Note that the cached responses expire every 2 hours or so.
# The API response itself dictates the expiry time)
imdb = Imdb(cache=True)

app = Flask(__name__)
#app.config.from_object(config['dev'])
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.session_protection = "strong"

#Create session and connect to the database
engine = create_engine('sqlite:///imdb_recognition.db')
Base.metadata.bind = engine
DBsession = sessionmaker(bind = engine)
SQLsession = DBsession()

#fakeuser
# user = User(name='Anna')
# SQLsession.add(user)
# SQLsession.commit()
#fakeuser end

#Helper functions
def get_google_auth(state=None, token=None):
    if token:
        return OAuth2Session(Auth.CLIENT_ID, token=token)
    if state:
        return OAuth2Session(
            Auth.CLIENT_ID,
            state=state,
            redirect_uri=Auth.REDIRECT_URI)
    oauth = OAuth2Session(
        Auth.CLIENT_ID,
        redirect_uri=Auth.REDIRECT_URI,
        scope=Auth.SCOPE)
    return oauth

@login_manager.user_loader
def load_user(id):
    user = SQLsession.query(User).filter_by(id=id).one_or_none()
    return user

@login_manager.request_loader
def request_loader(request):
    # email = request.form.get('email')
    # if email not in users:
    #     return
    #
    # user = User()
    # user.id = email

    # DO NOT ever store passwords in plaintext and always compare password
    # hashes using constant-time comparison!
    #$user.is_authenticated = request.form['pw'] == users[email]['pw']
    #print "i come here"
    return #user

#Routes

@app.route('/')
def landing_page():
    if current_user.is_authenticated:
        return redirect(url_for("showHomePage"))
    else:
        return render_template("welcomePage.html")

@app.route('/home/', methods=['GET', 'POST'])
@login_required
def showHomePage():
    if request.method == 'POST':
        search_for = request.form['title']
        return redirect(url_for('showSearchResults', search_for = search_for))
    else:
        cur_email = SQLsession.query(User).filter_by(id=current_user.id).one()
        return render_template('homepage.html', user_email=cur_email.email)

@app.route('/add/', methods= ['POST'])
@login_required
def addMoviesWatched():
    movie_ids_watched = request.form.getlist('watched')
    for imdb_id in movie_ids_watched:
        title = imdb.get_title_by_id(imdb_id)

        movie = SQLsession.query(Movie).filter_by(imdb_id=imdb_id).one_or_none()
        if not movie:
            #print "movie not in the database"
            movie = Movie(imdb_id=imdb_id, title = title.title, poster_url=title.poster_url)
            SQLsession.add(movie)

            for actor in title.credits:
              if actor.roles:
                  person = Person(name=actor.name, imdb_id=actor.imdb_id)
                  SQLsession.add(person)
                  roles = Roles(movie_id=imdb_id, person_id=actor.imdb_id, character_name=" / ".join(actor.roles))
                  SQLsession.add(roles)

        added_flag = SQLsession.query(MoviesWatched).filter_by(movie_id=imdb_id, user_id=1).one_or_none()
        if not added_flag:
            #print "movie not watched yet"
            movies_watched = MoviesWatched(user_id=current_user.id, movie_id=imdb_id)
            SQLsession.add(movies_watched)

        SQLsession.commit()

    return redirect(url_for('showHomePage'))

@app.route('/home/mywatchedlist/', methods=['GET'])
@login_required
def showMoviesWatched():
    cur_user = SQLsession.query(User).filter_by(id=current_user.id).one()
    movies_watched = SQLsession.query(Movie).join(MoviesWatched).filter(MoviesWatched.user_id == current_user.id).all()
    image_urls = {}
    for m in movies_watched:
        print m.imdb_id, m
        image_urls[m.imdb_id] = m.poster_url
        print m.imdb_id, "image URL:", image_urls[m.imdb_id]

    ### Network visualization
    #commonactors = SQLsession.query(Person).join(Movie).filter(MoviesWatched.user_id)

    subq = SQLsession.query(Roles.person_id).join(MoviesWatched, MoviesWatched.movie_id == Roles.movie_id).group_by(Roles.person_id).having(func.count(Roles.person_id) > 1).subquery()
    repeated_actors = SQLsession.query(MoviesWatched, Roles).join(Roles, MoviesWatched.movie_id == Roles.movie_id).filter(Roles.person_id.in_(subq)).all()
    #print "This is repeated_actors:", repeated_actors

    #Nodes - unique Movies and Actors
    #Edges - links between unique actors and multiple movies

    nodes = []
    unique_nodes_check = {}
    node_count = 0
    edges = []

    for movie, actor in repeated_actors:
        #print movie.movie_id, actor.person_id
        #add to nodes
        if movie.movie_id not in unique_nodes_check.keys():
            unique_nodes_check[movie.movie_id] = 1
            node = {}
            node['id'] = node_count
            node_count += 1
            node['group'] = 'movie'
            node['imdb_id'] = movie.movie_id
            nodes.append(node)
        if actor.person_id not in unique_nodes_check.keys():
            unique_nodes_check[actor.person_id] = 1
            node = {}
            node['id'] = node_count
            node_count += 1
            node['group'] = 'actor'
            node['imdb_id'] = actor.person_id
            nodes.append(node)
        #add edge
        #loop though nodes to find a dictionary with the imdb id, get node id
        #add to, from ids
        edge = {}
        for node in nodes:
            if node['imdb_id'] == actor.person_id:
                edge['from'] = node['id']
            if node['imdb_id'] == movie.movie_id:
                edge['to'] = node['id']
        edges.append(edge)



    print nodes
    print edges




    ###SQL Equivalent:
    # cmd = '''SELECT *
    #         from movies_watched
    #         join roles on movies_watched.movie_id == roles.movie_id
    #         where roles.person_id in
    #         (SELECT roles.person_id
    #         from movies_watched
    #         join roles on movies_watched.movie_id == roles.movie_id
    #         group by roles.person_id
    #         having count(roles.person_id) > 1
    #         )'''
    # query = SQLsession.execute(text(cmd))

    #edges
    ### Network visualization ends

    return render_template("movieswatched.html", user_email=cur_user.email, results=movies_watched, image_urls=image_urls)
#
# @app.route('/home/mywatchedlist/commonactors/', methods=['GET'])
# @login_required
# def showCommonActors():
#     movies_watched = SQLsession.query(Movie).join(MoviesWatched).filter(MoviesWatched.user_id == current_user.id).all()

@app.route('/search/<string:search_for>/')
@login_required
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

@app.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('showHomePage'))
    google = get_google_auth()
    auth_url, state = google.authorization_url(
        Auth.AUTH_URI, access_type='offline')
    session['oauth_state'] = state
    # return render_template('login.html', auth_url=auth_url)
    return redirect(auth_url)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('landing_page'))

@app.route('/gCallback')
def callback():
    # Redirect user to home page if already logged in.
    if current_user is not None and current_user.is_authenticated:
        return redirect(url_for('showHomePage'))
    if 'error' in request.args:
        if request.args.get('error') == 'access_denied':
            return 'You denied access.'
        return 'Error encountered.'
    if 'code' not in request.args and 'state' not in request.args:
        return redirect(url_for('login'))
    else:
        # Execution reaches here when user has
        # successfully authenticated our app.
        google = get_google_auth(state=session['oauth_state'])
        #try:
        token = google.fetch_token(
            Auth.TOKEN_URI,
            client_secret=Auth.CLIENT_SECRET,
            authorization_response=request.url)
        #except HTTPError:
            #return 'HTTPError occurred.'
        google = get_google_auth(token=token)
        resp = google.get(Auth.USER_INFO)
        if resp.status_code == 200:
            user_data = resp.json()
            email = user_data['email']
            #user = User.query.filter_by(email=email).first()
            user = SQLsession.query(User).filter_by(email=email).one_or_none()
            if user is None:
                user = User(email=email)
                #user.email = email
            user.name = user_data['name']
            print(token)
            user.tokens = json.dumps(token)
            user.avatar = user_data['picture']
            SQLsession.add(user)
            SQLsession.commit()
            login_user(user)
            return redirect(url_for('showHomePage'))
        return 'Could not fetch your information.'

if __name__ == '__main__':
    app.secret_key = "super_secret_key"
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
