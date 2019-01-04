#!/usr/bin/env python

from flask import Flask, render_template, request, redirect
from flask import jsonify, url_for, flash, send_from_directory
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Pokemon, Spotted
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from datetime import datetime

import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'svg'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

# Connect to Database and create database session
engine = create_engine('sqlite:///pokedexdb.db?check_same_thread=False')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


# Google connect
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/userinfo/v2/me"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['provider'] = 'google'
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h3>Welcome, '
    output += login_session['username']
    output += '!</h3>'
    flash("Welcome %s" % login_session['username'])
    print("Logged in!")
    return output


# Google disconnect
# Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print('Access Token is None')
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print('In gdisconnect access token is %s', access_token)
    print('User name is: ')
    print(login_session['username'])
    url = (
        'https://accounts.google.com/o/oauth2/revoke?token=%s'
        % login_session['access_token'])
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print('result is ')
    print(result)
    if result['status'] == '200':
        # del login_session['access_token']
        # del login_session['gplus_id']
        # del login_session['username']
        # del login_session['email']
        # del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['access_token']
            del login_session['gplus_id']
        if login_session['provider'] == 'facebook':
            # fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showPokemon'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showPokemon'))


# Helper Functions
def createUser(login_session):
    newUser = User(
                name=login_session['username'],
                email=login_session['email'],
                picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# JSON APIs
@app.route('/pokedex/JSON')
def pokedexJSON():
    pokemons = session.query(Pokemon).all()
    return jsonify(Pokedex=[p.serialize for p in pokemons])


@app.route('/pokedex/<int:pokemon_id>/JSON')
def pokemonJSON(pokemon_id):
    pokemon = session.query(Pokemon).filter_by(id=pokemon_id).one()
    spotted = session.query(Spotted).filter_by(
        pokemon_id=pokemon_id).all()
    return jsonify(Locations=[s.serialize for s in spotted])


# View all pokemon in pokedex
@app.route('/')
@app.route('/pokedex/')
def showPokemon():
    pokemons = session.query(Pokemon).order_by(asc(Pokemon.number))
    if 'username' not in login_session:
        return render_template('publicpokedex.html', pokemons=pokemons)
    else:
        return render_template('pokedex.html', pokemons=pokemons)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


# Add a new pokemon
@app.route('/pokedex/new/', methods=['GET', 'POST'])
def newPokemon():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        if 'file' not in request.files:
            filename = ''
            print('No file part')
        else:
            file = request.files['file']
            if file.filename == '':
                filename = ''
                print('No selected file')
            if file and allowed_file(file.filename):
                filename = str(datetime.now().strftime('%Y_%m_%d_%H_%M_%S')) + '_' + secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        newPokemon = Pokemon(
            name=request.form['name'],
            number=request.form['number'],
            picture=filename,
            type1=request.form['type1'],
            type2=request.form['type2'],
            description=request.form['description'],
            user_id=login_session['user_id']
        )
        session.add(newPokemon)
        session.commit()
        flash('New pokemon %s successfully created.' % newPokemon.name)
        return redirect(url_for('showPokemon'))
    else:
        return render_template('newpokemon.html')


# Edit a pokemon
@app.route('/pokedex/<int:pokemon_id>/edit/', methods=['GET', 'POST'])
def editPokemon(pokemon_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedPokemon = session.query(
        Pokemon).filter_by(id=pokemon_id).one()
    if editedPokemon.user_id != login_session['user_id']:
        return '''<script>function myFunction() {
            alert('You are not authorized to edit this pokemon.
            Please create your own pokemon in order to edit.');}
            </script><body onload='myFunction()'>'''
    if request.method == 'POST':
        if request.form['name']:
            editedPokemon.name = request.form['name']
        if request.form['number']:
            editedPokemon.number = request.form['number']
        if 'file' not in request.files:
            editedPokemon.picture = editedPokemon.picture
            print('No file part')
        else:
            file = request.files['file']
            if file.filename == '':
                editedPokemon.picture = editedPokemon.picture
                print("No change to picture")
            if file and allowed_file(file.filename):
                filename = str(datetime.now().strftime('%Y_%m_%d_%H_%M_%S')) + '_' + secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                editedPokemon.picture = filename
        if request.form['type1']:
            editedPokemon.type1 = request.form['type1']
        if request.form['type2']:
            editedPokemon.type2 = request.form['type2']
        if request.form['description']:
            editedPokemon.description = request.form['description']
        session.add(editedPokemon)
        session.commit()
        flash('%s successfully edited.' % editedPokemon.name)
        return redirect(url_for('showPokemon'))
    else:
        return render_template('editpokemon.html', pokemon=editedPokemon)


# Delete a pokemon
@app.route('/pokedex/<int:pokemon_id>/delete/', methods=['GET', 'POST'])
def deletePokemon(pokemon_id):
    if 'username' not in login_session:
        return redirect('/login')
    pokemonToDelete = session.query(
        Pokemon).filter_by(id=pokemon_id).one()
    if pokemonToDelete.user_id != login_session['user_id']:
        return '''<script>function myFunction() {
            alert('You are not authorized to delete this pokemon.
            Please create your own pokemon in order to delete.');}
            </script><body onload='myFunction()'>'''
    if request.method == 'POST':
        session.delete(pokemonToDelete)
        flash('%s successfully deleted.' % pokemonToDelete.name)
        session.commit()
        return redirect(url_for('showPokemon', pokemon_id=pokemon_id))
    else:
        return render_template('deletepokemon.html', pokemon=pokemonToDelete)


# View a single pokemon
@app.route('/pokedex/<int:pokemon_id>/')
def showSpotted(pokemon_id):
    pokemon = session.query(Pokemon).filter_by(id=pokemon_id).one()
    creator = getUserInfo(pokemon.user_id)
    spotted = session.query(Spotted).filter_by(
        pokemon_id=pokemon_id).all()
    if ('username' not in login_session or
            creator.id != login_session['user_id']):
        return render_template(
            'publicpokemon.html',
            spotted=spotted, pokemon=pokemon, creator=creator)
    else:
        return render_template(
            'pokemon.html',
            spotted=spotted, pokemon=pokemon, creator=creator)


# Add a new spotted location
@app.route('/pokedex/<int:pokemon_id>/location/new/', methods=['GET', 'POST'])
def newSpot(pokemon_id):
    if 'username' not in login_session:
        return redirect('/login')
    pokemon = session.query(Pokemon).filter_by(id=pokemon_id).one()
    if login_session['user_id'] != pokemon.user_id:
        return '''<script>function myFunction() {
            alert('You are not authorized to add spots for this pokemon.
            Please create your own pokemon in order to add spots.');}
            </script><body onload='myFunction()'>'''
    if request.method == 'POST':
        newSpot = Spotted(
            location=request.form['location'],
            date=request.form['date'],
            notes=request.form['notes'],
            pokemon_id=pokemon_id
        )
        session.add(newSpot)
        session.commit()
        flash('New location %s successfully created.' % (newSpot.location))
        return redirect(url_for('showSpotted', pokemon_id=pokemon_id))
    else:
        return render_template('newspot.html', pokemon_id=pokemon_id)


# Edit a spotted location
@app.route(
    '/pokedex/<int:pokemon_id>/location/<int:spotted_id>/edit',
    methods=['GET', 'POST'])
def editSpot(pokemon_id, spotted_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedSpot = session.query(Spotted).filter_by(id=spotted_id).one()
    pokemon = session.query(Pokemon).filter_by(id=pokemon_id).one()
    if login_session['user_id'] != pokemon.user_id:
        return '''<script>function myFunction() {
            alert('You are not authorized to edit spots for this pokemon.
            Please create your own pokemon in order to edit spots.');}
            </script><body onload='myFunction()'>'''
    if request.method == 'POST':
        if request.form['location']:
            editedSpot.location = request.form['location']
        if request.form['date']:
            editedSpot.date = request.form['date']
        if request.form['notes']:
            editedSpot.notes = request.form['notes']
        session.add(editedSpot)
        session.commit()
        flash('%s successfully edited.' % (editedSpot.location))
        return redirect(url_for('showSpotted', pokemon_id=pokemon_id))
    else:
        return render_template(
            'editspot.html',
            pokemon_id=pokemon_id, spotted_id=spotted_id, spot=editedSpot)


# Delete a spotted location
@app.route(
    '/pokedex/<int:pokemon_id>/location/<int:spotted_id>/delete',
    methods=['GET', 'POST'])
def deleteSpot(pokemon_id, spotted_id):
    if 'username' not in login_session:
        return redirect('/login')
    pokemon = session.query(Pokemon).filter_by(id=pokemon_id).one()
    spotToDelete = session.query(Spotted).filter_by(id=spotted_id).one()
    if login_session['user_id'] != pokemon.user_id:
        return '''<script>function myFunction() {
            alert('You are not authorized to delete spots for this pokemon.
            Please create your own pokemon in order to delete spots.');}
            </script><body onload='myFunction()'>'''
    if request.method == 'POST':
        session.delete(spotToDelete)
        session.commit()
        flash('%s successfully deleted.' % (spotToDelete.location))
        return redirect(url_for('showSpotted', pokemon_id=pokemon_id))
    else:
        return render_template(
            'deletespot.html',
            pokemon_id=pokemon_id, spotted_id=spotted_id, spot=spotToDelete)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
