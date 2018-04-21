import requests
import json
from practice_api import api_key 
from flask import Flask, render_template, session, redirect, request, url_for, flash
from flask_script import Manager, Shell
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField, PasswordField, BooleanField, SelectMultipleField, ValidationError
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_required, logout_user, login_user, UserMixin, current_user
import os
import re
from flask.ext.uploads import UploadSet, configure_uploads, IMAGES, patch_request_class #from stackoverflow by chirag maliwal

####### Applicaiton configs #######
app = Flask(__name__)
app.debug = True
app.use_reloader = True
app.config['SECRET_KEY'] = 'thisoneishardtoguess'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or "postgresql://localhost/SI364finalprojecthhsurk"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False
app.config['HEROKU_ON'] = os.environ.get('HEROKU')
app.config['UPLOADED_PHOTOS_DEST'] = os.getcwd()

photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)
patch_request_class(app) 
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
	col = db.relationship('PersonalYodaFavorites',backref='User')

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
	plot = db.Column(db.String(10000))
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
	#rating = db.Column(db.Integer)

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
	base_url = "http://www.omdbapi.com/?"
	parameters = {'apikey':api_key,'t':search_string, 'plot':'full'}
	r = requests.get(base_url,parameters)
	rt = json.loads(r.text)
	plot = rt['Plot']
	title = rt['Title']
	movie_tupl = (title, plot)
	return movie_tupl

def get_yoda_translation(movie_plot):
	yoda_list = []
	base_url = "http://api.funtranslations.com/translate/yoda.json?"
	parameters = {'text':movie_plot}
	r = requests.get(base_url,parameters)
	rt = json.loads(r.text)
	translation = rt['contents']['translated']
	return(translation)

def get_or_create_movie(title, current_user):
	mov = Movie.query.filter_by(title=title).first()
	if mov:
		return mov
	else:
		movie_tupl = get_movie_data(title)
		title1 = movie_tupl[0]
		plot = movie_tupl[1]
		mov = Movie(title=title1, plot=plot, user_id=current_user.id)
		db.session.add(mov)
		db.session.commit()
		return mov

def get_or_create_yoda(plot, current_user, movie_id):
	yod = Yoda.query.filter_by(movie_id=movie_id).first()
	if yod:
		return yod
	else:
		yoda_trans = get_yoda_translation(plot) 
		yod = Yoda(yoda_trans=yoda_trans, user_id =current_user.id,movie_id=movie_id)
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

def get_trans(id):
	y = Yoda.query.filter_by(id=id).first()
	return y
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
	password = PasswordField('Enter Password:', validators=[Required(),EqualTo('passwordComf',message="Passwords must be the same.")])
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
	name = StringField('Favorite list name',validators=[Required()])
	trans_picks = SelectMultipleField('Yoda translations to include')
	submit = SubmitField('Create Favorites List')

	def validate_list_name(self, field):
		if PersonalYodaFavorites.query.filter_by(name=name).first():
			raise ValidationError('Favorite List name already exists. Please enter another.')

class TranslateForm(FlaskForm):
	#from HW5 update field 
	submit = SubmitField('Translated')

class UpdateButton(FlaskForm):
	submit = SubmitField('Update')

class UpdateForm(FlaskForm):
	new_trans = SelectMultipleField('Which translation do you want to add to an exisiting list?',validators=[Required()])
	submit = SubmitField('Update')

class ButtonTranslate(FlaskForm):
	#from HW5
	submit = SubmitField('Translate')

class DeleteForm(FlaskForm):
	#from HW5
	submit = SubmitField('Delete')

class UploadForm(FlaskForm):
	#for the movie poster if they wish to upload it
	photo = FileField(validators=[FileAllowed(photos, 'Image only!'), FileRequired('File was empty!')])
	submit = SubmitField('Submit')

class UploadFormButton(FlaskForm):
	submit = SubmitField('Upload Movie Poster')





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
			login_user(user, form.remember.data)
			return redirect(request.args.get('next') or url_for('index'))
		flash('Invalid username or password. Again please try.')
	return render_template('login.html',form=form)
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
	form = MovieSearchForm()
	if form.validate_on_submit():
		get_or_create_movie(title=form.movie.data,current_user=current_user)
		flash("Movie Successfully Found!")
		return redirect(url_for('movie_results'))
	return render_template('index.html',form=form)
	

@app.route('/movie_found')
def movie_results():
	#here you will see the movie results from the search entered on the previous page
	#a button will appear asking if you want to translate the plot to yodish
	#another button will appear here for the delete button
	#render template for that button and results
	#redirect url to page with yodish translation
	movies = Movie.query.all()
	for elem in movies:
		poster = MoviePoster.query.filter_by(movie_id=elem.id).first()
		if poster:
			filename=poster.poster
			file_url = photos.url(filename)
		else:
			file_url=None
	return render_template('movie_results.html',movie=movies,file_url=file_url)

@app.route('/movie_view/<movid>',methods=['POST','GET'])
def movie_view(movid):
	form = ButtonTranslate()
	form1 = UploadFormButton()
	mov1 = Movie.query.filter_by(id=movid).first()
	title = mov1.title
	plot = mov1.plot
	mov_id = mov1.id
	poster = MoviePoster.query.filter_by(movie_id=mov_id).first()
	if poster:
		filename=poster.poster
		file_url = photos.url(filename)
	else:
		file_url=None
	
	return render_template('movie_view.html',title=title,plot=plot,mov_id=mov_id,form=form,form1=form1, file_url=file_url)

@app.route('/all_movies',methods=["GET","POST"])
def see_all_movies():
	# queries the Yoda table 
	# update button form to a button to update the rating of the movie
	# takes movie id from Yoda Table and queries movie title 
	# renders template to displat movie names with yodish plots
	# list of movies tuples will be passed into the template
	yoda_list = []
	movie = Movie.query.all()

	for elem in movie:
		mov_id = elem.id
		yoda = Yoda.query.filter_by(movie_id=mov_id).first()
		if yoda:
			yoda_list.append((elem.title,yoda.yoda_trans))
		else:
			yoda_list.append((elem.title,elem.plot))
			flash('Not all plots Translated to Yoda. Please Translate this Statement')
		#return redirect(url_for('delete',movie=elem.title))
	return render_template('all_movies.html',all_movies=yoda_list)


@app.route('/create_favorites',methods=['GET','POST'])
@login_required
def create_favorites():
	#set up form
	#create the list of choices to choose from using the Yoda table
	#use the input data to pass into get_or_create_favorites to save the favorite collection
	#redirect the url to display collections
	#render template for the create favorites.html
	form = FavoriteForm()
	yod = Yoda.query.all()
	options = [(y.id,y.yoda_trans) for y in yod]
	form.trans_picks.choices = options
	if request.method == 'POST':
		name = form.name.data
		picks = form.trans_picks.data
		trans_obj = [get_trans(int(id)) for id in picks]
		get_or_create_favorite(current_user=current_user,name=name,yoda_list=trans_obj)
		return redirect(url_for('favorites'))
	return render_template('make_favorites.html',form=form)

@app.route('/translate_yodish/<mov_id>',methods=['GET','POST'])
def translate(mov_id):
	# set up translate form
	# get new rating
	# requery yoda table
	# save new rating to the yoda table instance
	# save to new table
	# redirect to see_all_movies
	# render template for the update item html file
	movie = Movie.query.filter_by(id=mov_id).first()
	plot = movie.plot
	form = TranslateForm()
	trans_obj = get_or_create_yoda(plot=plot,current_user=current_user,movie_id=mov_id)
	trans_text=trans_obj.yoda_trans
	flash("Created New Yoda Translated Plot")
	
	return render_template('yoda.html',translated_plot=trans_text,form=form)
	

@app.route('/delete/<collections>',methods=['GET','POST'])
def delete(collections):
	# query movie table instance to dele
	# delete from the table
	# redirect url for see_all_movies
	# movie = Movie.query.filter_by(title=movie).first()
	# movie_id = movie.id
	deleter = PersonalYodaFavorites.query.filter_by(id=collections).first()
	print(deleter)
	db.session.delete(deleter)
	db.session.commit()
	flash('Deleted Favorite List '+deleter.name)
	return redirect(url_for('see_all_movies'))


@app.route('/update/<collection>',methods=['GET','POST'])
def update(collection):
	#add items to collections
	form = UpdateForm()
	updater = PersonalYodaFavorites.query.filter_by(id=collection).first()
	yod = Yoda.query.all()
	options = [(y.id,y.yoda_trans) for y in yod]
	form.new_trans.choices = options
	if request.method == 'POST':
		picks = form.new_trans.data
		trans_obj = [get_trans(int(id)) for id in picks]
		for elem in trans_obj:
			updater.coll.append(elem)
			return redirect(url_for('favorites'))
		
		flash('New Translated Plot Addedd Successfully.  Please Click to any screen you want')
		db.session.add(updater)
		db.session.commit()
	return render_template('update.html',form=form)

@app.route('/favorites',methods=['GET','POST'])
@login_required
def favorites():
	# query the favorites table to show all the collections made by this user using current_user
	# render template for the favorites html file

	user_favs = PersonalYodaFavorites.query.filter_by(user_id=current_user.id).all()
	return render_template('favorites.html',favorites=user_favs)

@app.route('/favorite/<id>',methods=['GET','POST'])
def favorite(id):
	diction = {}
	form = DeleteForm()
	form1 = UpdateButton()
	fav_id = int(id)
	fav = PersonalYodaFavorites.query.filter_by(id=fav_id).first()
	favs = fav.coll.all()
	return render_template('favorite.html',favorites=fav, favs=favs, form=form,form1=form1)


@app.route('/upload/<mov_id>', methods=['GET', 'POST']) #github user greyli
def upload_file(mov_id):
    form = UploadForm()
    if form.validate_on_submit():
        filename = photos.save(form.photo.data)
        file_url = photos.url(filename)
        movie = Movie.query.filter_by(id=mov_id).first()
        poster = MoviePoster.query.filter_by(movie_id=movie.id).first()
        if poster:
        	pass
        else:
        	post = MoviePoster(movie_id=movie.id,poster=filename)
        	db.session.add(post)
        	db.session.commit()
        flash('Successfully Added Photo, Clink on Movies link again to see it.')
        return redirect(url_for('movie_results'))
    else:
        file_url = None
    return render_template('poster.html', form=form, file_url=file_url)

if __name__ == '__main__':
	db.create_all()
	manager.run()









