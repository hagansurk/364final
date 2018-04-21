# 364 final By Hagan Surkamer

**Overview:**
For my application, I wanted to create a nice easy movie database application.  Using OMDB's api, I got plot and title information on users inputed movies.  I wanted to do more than that, so I added a little twist.  I then instructed users to press a translate button to get the plot translated to Yodish.  After that, they were able to create, update, and delete lists of thier favorite movies and plots as well as add images to their movie entries.  

**IMPORTANT TO NOTE: the yoda translator api only allows for 5 calls an hour so if it doesn't work after 5, you have to wait another hour.  Was a real headache when completing this project.**

**User Experience:**
When running the application, the user will be able to do a multitude of things.  From the get go, they are able to start searching for movies right away.  Also, they are able to login and register if they are a new user.  The site will never log them out, so no need to worry about forgetting your password.  Once they seach movie, they can see a list of hyper linked movie title for all the searches they have done.  By clicking on one, you can then translate the plot to Yodaish.  The text on the screen will then change and save to a database.  Clicking the same button again will take you to a list of movie titles and all their Yodaish translations.  Before moving on to the next set of tasks, users are also able to upload and save photos, such as movie posters, from the same screen that possesed the translate button.  These images will be permantly saved under these movie Titles and plots.  Now that plots have been translated, users may want to save their favorite ones a list.  I have given them the ability to select multiple plot translations and save them to a named list.  By clicking on the hyperlinked name of different lists, users are then able to update or delete lists as they so choose.  The only lists displayed will those that the user has saved personally, so that no one else can delete or change them.  Deleteing will result in the whole list dissapearing, while updating allows users to add more plots to their lists.  

**Other modules:**
I did install one other module with pip which was Flask-Uploads.  This was found on stackover flow by Chirag Maliwal and again by Github user greyli, who helped me with a little bit more of the image upload process.  This module was used to set up and configure the application for upload and let the app to expect images and where to save them after upload.  

**Routes and their templates:**

Errorhandler(404) --> '404.html'

Errorhandler(500) --> '500.html'

'/login' --> 'login.html'

'/logout' --> no template

'/secret' --> no template

'/register' --> 'register.html'

'/' --> 'index.html'

'/movie_view/<movid>' --> 'movie_view.html'

'/all_movies' --> 'all_movies.html'

'/create_favorites' (login required) --> 'make_favorites.html'

'/translate_yodish/<mov_id>' --> 'yoda.html'

'/delete/<collections>' --> no template

'/update/<collection>' --> 'update.html'

'/favorites' (login required) --> 'favorites.html'

'/favorite/<id>' --> 'favorite.html'

'/upload/<mov_id>' --> 'poster.html'


