from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import os
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap5(app)
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # Redirect here if not logged in

    
class Upyogkarta(UserMixin):
    def __init__(self, username):
        self.username = username

    def get_id(self):
        return self.username


class BlogPost(db.Model):
    __tablename__ = 'blog_post'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    subtitle = db.Column(db.String(200))

    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    url = db.Column(db.Text, nullable=False)    
    
    # Relationship to User (foreign key)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', back_populates='posts')

    def __repr__(self):
        return f"<BlogPost {self.id} - {self.title[:20]}>"

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    date_signed_up = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to BlogPosts (one-to-many)
    posts = db.relationship('BlogPost', back_populates='author', lazy=True)

    def __repr__(self):
        return f"<User {self.id} - {self.email}>"

# Initialize database once (typically in your app factory)
with app.app_context():
    db.create_all()
def get_data(what_need):
    users = User.query.all()

    blogs = BlogPost.query.all()

    if what_need == "blogs":
        return blogs
    elif what_need == "users":
        return users


@login_manager.user_loader
def load_user(username):
    data = User.query.all()
    users = [i.email for i in data]
    if username in users:
        return Upyogkarta(username)
    return None

@app.route('/')
def home():

    return redirect(url_for('home_page'))
@app.route('/home')
def home_page():
    try:

        total_users = [i.email for i in get_data("users")]
        no_of_users = len(total_users)
        bloggs = BlogPost.query.all()
        blogs = [{
            "image_url": i.url,
            "username": i.author.name,
            "title": i.title,
            "id": i.id,
            "content": i.content,
            "subtitle": i.subtitle,
            "date_posted": i.date_posted
        } for i in bloggs]
        if len(blogs) > 0:
            blog_content = True
        else:
            blog_content = False
        no_of_blogs = len(blogs)
        ids = [i.id for i in bloggs]
        return render_template('base.html', active_users=no_of_users, no_of_blogs=no_of_blogs, blogs=blogs, blog_content=blog_content, ids=ids, zip=zip)
    except Exception:
        no_of_blogs = 0
        no_of_users = 0
    
    return render_template('base.html', active_users=no_of_users, no_of_blogs=no_of_blogs)

@app.route('/post')
@login_required
def post():
    return render_template('base.html', post_content=True)

@app.route('/submit', methods=['POST', 'GET'])
def submit():
    title = request.form.get('title')
    subtitle = request.form.get('subtitle')
    content = request.form.get('content')
    image_url = request.form.get('image_url')

    person = User.query.filter_by(email=current_user.username).first()
    user_id = person.id
    new_blog = BlogPost(
        title = title,
        subtitle = subtitle,
        content = content,
        url = image_url,
        user_id = user_id        
    )
    db.session.add(new_blog)
    db.session.commit()
    return redirect('post')

@app.route('/login')

def login():
    return render_template('login.html')


@app.route('/login_submit', methods=['POST'])
def login_submit():
    exist_data = User.query.all()
    if exist_data:
        exist_emials = [packet.email for packet in exist_data]

        email = request.form.get('email')

        

        if email in exist_emials:
            person = User.query.filter_by(email=email).first()
            if person:

                password = person.password
                if check_password_hash(password, request.form.get('password')):


                    user = load_user(email)
                    if user:
                        login_user(user)
                        return redirect(url_for('home'))
                else:
                    return render_template('login.html', prefill_email=email)
            else:
                return render_template('login.html')
                    
        else:
            return render_template('login.html')
        

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register_submit', methods=['POST'])
def register_submit():
    email = request.form.get('email')
    password = request.form.get('password')
    name = request.form.get('name')
    hashed_password = generate_password_hash(password)
    new_user = User(
        name = name,
        email = email,
        password = hashed_password
        
    )
    if new_user:
            
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    else:
        return redirect(url_for('register'))

@app.route('/my-posts')
@login_required
def my_posts():
    person = User.query.filter_by(email=current_user.username).first()
    user = User.query.get(person.id)
    user_posts = user.posts
    all_posts = [packet.id for packet in user_posts]
    blogs = [{

        "image_url": i.url,
        "username": i.author.name,
        "title": i.title,
        "id": i.id,
        "content": i.content
    } for i in user_posts]
    ids = [i.id for i in user_posts]
    return render_template('base.html', blog_content=True, blogs=blogs, edit=True, zip=zip, ids=ids)


@app.route('/delete/<int:id>')
@login_required
def delete(id):

    changable_post = BlogPost.query.get(id)

    if changable_post:
        db.session.delete(changable_post)
        db.session.commit()
        return redirect(url_for('my_posts'))        
    else:
        return redirect(url_for('my_posts'))
    

@app.route('/edit_post/<int:id>')
@login_required
def edit_post(id):
    changable_post = BlogPost.query.get(id)

    if changable_post:
        title = changable_post.title
        subtitle = changable_post.subtitle
        content = changable_post.content
        url = changable_post.url
        return render_template('base.html', post_content=True, title=title, subtitle=subtitle, content=content, url=url, update=True, id=id)

@app.route('/submit_update<int:id>', methods=['POST'])
def submit_update(id):
    changable_post = BlogPost.query.get(id)
    if changable_post:
        person = User.query.filter_by(email=current_user.username).first()
        user_id = person.id
        changable_post.title = request.form.get('title')
        changable_post.subtitle = request.form.get('subtitle')
        changable_post.content = request.form.get('content')
        changable_post.url = request.form.get('image_url')
        changable_post.user_id = user_id  

        db.session.commit()
        return redirect(url_for('my_posts'))        



@app.route('/about_me')
def aboutme():
    return render_template('aboutme.html')


@app.route('/send_image/<path:name>')
def send_image(name):
    directory = 'statics/files'
    
    try:
        # Attempt to send the file from the directory
        return send_from_directory(directory, name)
    except FileNotFoundError:
        # If the file is not found, handle the error gracefully
        return "File not found", 404


@app.route('/contact')
def contact():
    return render_template('form.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)