from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from hashutils import make_pw_hash, check_pw_hash


app = Flask(__name__)
app.config['Debug'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogs:password@localhost:8889/blogs'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = '13579qwerty'


class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(500))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True)
    pw_hash = db.Column(db.String(200))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.pw_hash = make_pw_hash(password)
        


@app.before_request
def require_login():
    allowed_routes = ['login', 'signup', 'blog', 'index']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_pw_hash(password, user.pw_hash):
            session['username'] = username
            flash("Logged In")
            return redirect('/')
        else:
            flash('User password incorrect, or user does not exist', 'error')

    return render_template('login.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']

        #input validate user's data
        existing_user = User.query.filter_by(username=username).first()
        if not existing_user:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/')

        else:
            #resp that same that user exits
            return "<h1>Duplicate User</h1>"

    if request.method == 'GET':
        return render_template('signup.html')


@app.route('/', methods =['POST', 'GET'])
def index ():

    users = User.query.all()
    return render_template('index.html', users=users)



@app.route('/logout', methods=['POST'])
def logout():
    del session['username']
    return redirect('/')


@app.route('/newpost', methods =['POST', 'GET'])
def new ():

    title_error = ""
    post_error = ""
    owner = User.query.filter_by(username=session['username']).first()

    if request.method == 'POST':
        blog_post = request.form['blog']
        blog_title = request.form['title']

        if (blog_post == ""):
            post_error = "Please Enter a Blog"

        if (blog_title == ""):
            title_error = "Please Enter a Title"

        if post_error == "" and title_error == "":
            new_blog_post = Blog(blog_title, blog_post, owner)
            db.session.add(new_blog_post)
            db.session.commit()
            return redirect('/blog?id={}'.format(new_blog_post.id))
    
        return render_template('newpost.html', title_error=title_error, post_error=post_error)


    if request.method == 'GET':
        return render_template('newpost.html', title="Blogz")


@app.route('/blog', methods=['GET'])
def blog():
    blogs = Blog.query.all()
    blog_id = request.args.get('id')
    user_id = request.args.get('user')
    
    if user_id:
        user = User.query.get(user_id)
        blogs = Blog.query.filter_by(owner=user).all()
        return render_template('singleUser.html', blogs=blogs)
    if blog_id:
        blog = Blog.query.get(blog_id)
        return render_template('post.html', blog=blog )

    return render_template('blog.html', blogs=blogs)


if __name__ == '__main__':
    app.run()