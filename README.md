# Pokedex

This application allows the user to login via Google and view, create, update, and delete pokemon.
The user can also view, create, update, and delete spotted locations for each added pokemon.

## Getting Started

### Prerequisites

* Python interpreter
* Vagrant
* Flask (run command: *pip install flask*)
* Flask-HTTPAuth (run command: *pip install flask-httpauth*)
* Flask-SQLAlchemy (run command: *pip install flask-sqlalchemy*)
* SQLAlchemy (run command: *pip install sqlalchemy*)
* oauth2client (run command: *pip install oauth2client*)
* httplib2 (run command: *pip install httplib2*)
* requests (run command: *pip install requests*)
* Werkzeug (run command: *pip install werkzeug*)

### Installing

1. Verify all prerequisites are installed
2. Navigate to the *vagrant* folder and run command: *vagrant up*
3. Next, run command: *vagrant ssh*
4. Navigate to the *catalog* folder and run command: *python pokedex.py*
5. Go to http://localhost:5000/ in your browser
6. Login via Google to create, update, and delete pokemon and spotted locations

## Code Design

URLs:
* /login/ - Login via Google
* /pokedex/ - Lists all pokemon in pokedex
* /pokedex/1/ - Lists details + spotted locations of a single pokemon ID
* /pokedex/new/ - Add a new pokemon
* /pokedex/1/edit - Edit a pokemon
* /pokedex/1/delete - Delete a pokemon
* /pokedex/1/location/new/ - Add a new spotted location for a pokemon
* /pokedex/1/location/1/edit - Edit a spotted location for a pokemon
* /pokedex/1/location/1/delete - Delete a spotted location for a pokemon

JSON:
* /pokedex/JSON/ - All pokemon in pokedex in JSON format
* /pokedex/1/JSON/ - All spotted locations for a single pokemon ID in JSON format

## Built With

* [Python](https://www.python.org/downloads/) - Programming language
* [Flask](http://flask.pocoo.org/) - Python microframework
* [Vagrant](https://www.vagrantup.com/) - Virtual machine management
* [VirtualBox](https://www.virtualbox.org/wiki/Download_Old_Builds_5_1) - Runs virtual machine

## Authors

* **Sara Neel** - [sneelz](https://github.com/sneelz)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Thanks Udacity!
