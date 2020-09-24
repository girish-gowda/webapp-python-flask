from flask import Flask,  render_template, flash, redirect, url_for, session, logging, request
#from data import Articles
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import pymysql

app = Flask(__name__)
app.debug=True


#initialize pymysql
connection = pymysql.connect("localhost","girish","123456","myflaskapp")

#Articles = Articles()

@app.route("/")
def index():
    return render_template('home.html')

@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/articles")
def articles():
    cur = connection.cursor(pymysql.cursors.DictCursor)
    result = cur.execute("SELECT * from articles")

    articles  = cur.fetchall()

    if result > 0:
        return  render_template('articles.html', articles=articles)
    else:
        msg = "No Articles Found"
        return render_template('articles.html', msg = msg)
    #close connection
    cur.close()

@app.route("/article/<string:id>/")
def article(id):
    cur = connection.cursor(pymysql.cursors.DictCursor)
    result = cur.execute("SELECT * from articles WHERE id=%s", [id])

    article = cur.fetchone()
    return render_template('article.html', article=article)

#Register Form Class
class RegisterForm(Form):
    name = StringField('Name',[validators.Length(min=1, max=50)])
    username = StringField('Username',[validators.Length(min=4, max=25)])
    email = StringField('Email',[validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

#User Register
@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        cur = connection.cursor();
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s,%s,%s,%s)", (name,email,username,password))

        connection.commit();
        cur.close();

        flash("You are now registered and can log-in", 'success')
        redirect(url_for('login'))
    return render_template('register.html', form=form)

#User Login
@app.route('/login',methods=['POST','GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']

        cur = connection.cursor(pymysql.cursors.DictCursor)
        result = cur.execute("SELECT *  from users WHERE username = %s",[username])

        if result > 0:
            data = cur.fetchone()
            password = data['password']

            #compare passwords
            if sha256_crypt.verify(password_candidate,password):
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = "Invalid Login"
                return render_template('login.html', error=error)
            #cursor close
            cur.close()
        else:
            error = "Username not found"
            return render_template('login.html', error=error)

    return render_template('login.html')

#Check if user logged in
def is_loggedIn(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

#dashboard
@app.route('/dashboard')
@is_loggedIn
def dashboard():
    cur = connection.cursor(pymysql.cursors.DictCursor)
    result = cur.execute("SELECT * from articles")

    articles  = cur.fetchall()

    if result > 0:
        return  render_template('dashboard.html', articles=articles)
    else:
        msg = "No Articles Found"
        return render_template('dashboard.html', msg = msg)
    #close connection
    cur.close()


#Article Form Class
class ArticleForm(Form):
    title = StringField('Title',[validators.Length(min=1, max=200)])
    body = TextAreaField('Body',[validators.Length(min=30)])

#add article
@app.route('/add_article', methods=('GET','POST'))
@is_loggedIn
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        cur = connection.cursor()
        cur.execute("Insert INTO articles(title, body, author) VALUES(%s,%s,%s)",(title,body, session['username']))
        connection.commit()
        cur.close()
        flash('Article Created', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html',form=form)


#Edit article
@app.route('/edit_article/<string:id>', methods=('GET','POST'))
@is_loggedIn
def edit_article(id):
    cur = connection.cursor(pymysql.cursors.DictCursor)
    result = cur.execute("SELECT * from articles WHERE id = %s", [id])
    article = cur.fetchone()
    form = ArticleForm(request.form)
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']
        cur = connection.cursor()
        cur.execute("UPDATE articles SET title = %s, body = %s WHERE id = %s", (title,body,id))
        connection.commit()
        cur.close()
        flash('Article Updated', 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_article.html',form=form)


#logout
@app.route('/logout')
@is_loggedIn
def logout():
    session.clear()
    flash("You are logged out", 'success')
    return redirect(url_for('login'))



#delete article
@app.route('/delete_article/<string:id>',methods=['POST'])
@is_loggedIn
def delete_article(id):
    cur = connection.cursor()
    cur.execute("DELETE from articles WHERE id = %s", [id])
    connection.commit()
    cur.close()
    flash('Article Deleted','success')
    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    app.secret_key="secret123"
    app.run()

