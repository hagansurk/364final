import requests
import json
from practice_api import api_key 
from flask import Flask, render_template, session, redirect, request, url_for, flash
from flask_script import Manager, Shell
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField, PasswordField, BooleanField, SelectMultipleField, ValidationError
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_required, logout_user, login_user, UserMixin, current_user
import os
import re
####### Applicaiton configs #######
app = Flask(__name__)
app.debug = True
app.use_reloader = True
app.config['SECRET_KEY'] = 'thisoneishardtoguess'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or "postgresql://localhost/SI364finalprojecthhsurk"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False
app.config['HEROKU_ON'] = os.environ.get('HEROKU')
####### app set up #######
manager = Manager(app)
db = SQLAlchemy(app)
migrate = Migrate(app,db)
manager.add_command('db',MigrateCommand)

####### Login configs #########
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'
login_manager.init_app(app)


###### association table model #######

user_collection = db.Table('user_collection',db.Column('user_id',db.Integer,db.ForeignKey('yoda.id')),db.Column('collection_id',db.Integer,db.ForeignKey('personalyodafavorites.id')))

####### database table models ########

class User(UserMixin, db.Model):
	__tablename__ = "users"
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(250), unique=True,index=True)
	email = db.Column(db.String(64), unique=True,index=True)
	password_hash = db.Column(db.String(128))
	mov = db.relationship('Movie',backref='User')
	yod = db.relationship('Yoda', backref='User')
	col = db.relationship('PersonalYodaCollection',backref='User')

	@property
	def password(self):
		raise AttributeError('password is not a reasonable attribute') #from HW4

	@password.setter
	def password(self,password):
		self.password_hash = generate_password_hash(password) #from HW4

	def verify_password(self,password):
		return check_password_hash(self.password_hash, password) #from HW4

##### login loader #####
@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

class Movie(db.Model):
	__tablename__ = 'movie'
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(64))
	plot = db.Column(db.String(500))
	user_id = db.Column(db.Integer,db.ForeignKey('users.id'))
	yoda = db.relationship('Yoda',backref='Movie')
	poster = db.relationship('MoviePoster',backref='Movie')
	def __repr__(self):
		return "{}, Plot: {}".format(self.title, self.plot)

class Yoda(db.Model):
	__tablename__ = 'yoda'
	id = db.Column(db.Integer, primary_key=True)
	yoda_trans = db.Column(db.String(500))
	user_id = db.Column(db.Integer,db.ForeignKey('users.id'))
	movie_id = db.Column(db.Integer,db.ForeignKey('movie.id'))
	rating = db.Column(db.Integer)

class PersonalYodaFavorites(db.Model):
	__tablename__ = 'personalyodafavorites'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(64))
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	coll = db.relationship('Yoda', secondary=user_collection,backref=db.backref('personalyodafavorites',lazy='dynamic'),lazy='dynamic')

class MoviePoster(db.Model):
	__tablename__='movieposter'
	id = db.Column(db.Integer, primary_key=True)
	movie_id = db.Column(db.Integer,db.ForeignKey('movie.id'))
	poster = db.Column(db.String(128))
	# need to figure out how to save a file or image object to db

##### Helper Functions ######

def get_movie_data(search_string):
	movie_list = []
	base_url = "http://www.omdbapi.com/?"
	parameters = {'apikey':api_key,'t':search_string}
	r = requests.get(base_url,parameters)
	rt = json.loads(r.text)
	pass

def get_yoda_translation(movie_plot):
	yoda_list = []
	base_url = "http://api.funtranslations.com/translate/yoda.json?"
	parameters = {'text':movie_plot}
	r = requests.get(base_url,parameters)
	rt = json.loads(r.text)
	pass

def get_or_create_movie(title, plot):
	mov = Movie.query.filter_by(title=title).first()
	if mov:
		return mov
	else:
		mov = Mov(title=title, plot=plot)
		db.session.add(mov)
		db.session.commit()
		return mov

def get_or_create_yoda(yoda_trans):
	yod = Yoda.query.filter_by(yoda_trans=yoda_trans).first()
	if yod:
		return yod
	else:
		yod = Yoda(yoda_trans=yoda_trans)
		db.session.add(yod)
		db.session.commit()
		return yod

def get_or_create_favorite(name,current_user,yoda_list=[]): #from HW4
	col = PersonalYodaFavorites.query.filter_by(name=name,user_id=current_user.id).first()
	if col:
		return col
	else:
		col = PersonalYodaFavorites(name=name,user_id=current_user.id,coll=[])
		for trans in yoda_list:
			col.coll.append(trans)
		db.session.add(col)
		db.session.commit()
		return col

##### Form Classes ####
def Nospace(form, field):
	match = re.match('^[A-Z|a-z][A-Za-z0-9_.\!\?\$\@\&]*$', field.data[0])
	if match:
		pass
	else:
		raise ValidationError('Username must only contain letters, numbers, and special characters (!, ?, _, $, &, .). No spaces allowed')
		
class RegistrationForm(FlaskForm): 
	#from HW4
	email = StringField('Enter Email:', validators=[Required(),Length(1,64),Email()]) 
	username = StringField('Enter Username:', validators=[Required(),Length(1,64),Nospace])
	password = PasswordField('Enter Password:', vaildators=[Required(),EqualTo('passwordComf',message="Passwords must be the same.")])
	passwordComf = PasswordField('Confirm Password:',validators=[Required()])
	submit = SubmitField('Register User')

	def validate_email(self, field):
		if User.query.filter_by(email=field.data).first():
			raise ValidationError('Email is already registered. Try a new one.')

	def validate_username(self, field):
		if User.query.filter_by(username=field.data).first():
			raise ValidationError('Username already taken. Enter a new username')

class LoginForm(FlaskForm):
	#from HW4
	email = StringField('Email',validators=[Required(),Length(1,64),Email()])
	password = PasswordField('Password',validators=[Required()])
	remember = BooleanField('Keep me logged in')
	submit = SubmitField('Log In')

class MovieSearchForm(FlaskForm):
	#create form to get movie data to search omdb by
	movie = StringField('Enter a Movie',validators=[Required()])
	submit = SubmitField('Submit')

class FavoriteForm(FlaskForm):
	#create form to make a collection of yoda translations
	col = StringField('Favorite list name',validators=[Required()])
	trans_picks = SelectMultipleField('Yoda translations to include')
	submit = SubmitField('Create Favorites List')

	def validate_list_name(self, field):
		if PersonalYodaFavorites.query.filter_by(name=col).first():
			raise ValidationError('Favorite List name already exists. Please enter another.')

class UpdateForm(FlaskForm):
	#from HW5 update field 
	new_rate = StringField('What is the new rating of this translation?',validators=[Required()])
	submit = SubmitField('Update')

class ButtonUpdate(FlaskForm):
	#from HW5
	submit = SubmitField('Update')

class DeleteForm(FlaskForm):
	#from HW5
	submit = SubmitField('Delete')

class UploadForm(FlaskForm):
	#for the movie poster if they wish to upload it
	file = FileField()




####### View Functions #######

# error handler
@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404
	#create template

@app.errorhandler(500)
def internal_server_error(e):
	return render_template('500.html'), 500
	#create template

@app.route('/login',methods=['GET','POST']) #From HW4
def login():
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user is not None and user.verify_password(form.password.data):
			login_user(user, form.remember_me.data)
			return redirect(request.args.get('next') or url_for('index'))
		flash('Invalid username or password. Again please try.')
	return render_template('login.hmtl',form=form)
	#create template

@app.route('/logout')
@login_required #from HW4
def logout():
	logout_user()
	flash('logged out you have been.')
	return redirect(url_for('index'))

@app.route('/register',methods=["GET","POST"]) #from HW4
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,username=form.username.data,password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Log in you can now!')
        return redirect(url_for('login'))
    return render_template('register.html',form=form)

@app.route('/secret') #from HW4
@login_required
def secret():
    return "Do this only authenticated users can! Try to log in or contact the site admin."


@app.route('/',methods=['GET','POST'])
def index():
	# this is where the movie search form will be rendered 
	#will take the form, validate it, and call get_or_create_movie
	#redirect to results page to see the yodaish translate
	#render template for index.html

	pass

@app.route('/movie_found')
def movie_results():
	#here you will see the movie results from the search entered on the previous page
	#a button will appear asking if you want to translate the plot to yodish
	#another button will appear here for the delete button
	#render template for that button and results
	#redirect url to page with yodish translation
	pass

@app.route('/all_movies')
def see_all_movies():
	# queries the Yoda table 
	# update button form to a button to update the rating of the movie
	# takes movie id from Yoda Table and queries movie title 
	# renders template to displat movie names with yodish plots
	# list of movies tuples will be passed into the template
	pass

@app.route('/create_favorites',methods=['GET','POST'])
@login_required
def create_favorites():
	#set up form
	#create the list of choices to choose from using the Yoda table
	#use the input data to pass into get_or_create_favorites to save the favorite collection
	#redirect the url to display collections
	#render template for the create favorites.html
	pass

@app.route('/update_yodish/<translation>',methods=['GET','POST'])
def update(translation):
	# set up update rating form
	# get new rating
	# requery yoda table
	# save new rating to the yoda table instance
	# save to new table
	# redirect to see_all_movies
	# render template for the update item html file
	pass

@app.route('/delete/<movie>',methods=['GET','POST'])
def delete(movie):
	# query movie table instance to dele
	# delete from the table
	# redirect url for see_all_movies
	pass


@app.route('/favorites',methods=['GET','POST'])
@login_required
def favorites():
	# query the favorites table to show all the collections made by this user using current_user
	# render template for the favorites html file
	pass

@app.route('/upload',methods=['GET','POST'])
def upload():
	# form is the upload form
	# get the file name out of the form
	# save the file name to a static file 
	# upload file route the database for movie posters
	# redirect url to see_all_movies
	# render form template here
	pass

@app.route('/ajax')
def search():
	# using ajax to search for all movies
	# not sure if will actually be used or not
	pass



if __name__ == '__main__':
	db.create_all()
	manager.run()









