from flask import Flask, render_template, request, url_for, redirect, jsonify, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
from imdb_setup import Base, Movie, Person, Roles, User, MoviesWatched
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
    else:
        return render_template('homepage.html')

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
