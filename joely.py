'''A bitly clone'''
import joely_utils, datetime
from flask import Flask, request, session, redirect, url_for, render_template, flash 
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.restless import APIManager
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask('joeLy')

app.config.from_pyfile('settings.cfg')
db = SQLAlchemy(app)

manager = APIManager(app, flask_sqlalchemy_db=db)

num_per_page = 10 
min_pw_len, min_email_len = 7, 7


class URL(db.Model):
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    key = db.Column(db.Text)
    original_url = db.Column(db.Text)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'))
    created = db.Column(db.DateTime,default=datetime.datetime.utcnow)

    @property
    def formatted_date(self):
        return '{0}-{1}-{2}'.format(self.created.month,self.created.day,self.created.year)        

    @property
    def shortened(self):
        return '/j/{0}'.format(self.key)

class User(db.Model):
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    email = db.Column(db.Text)
    password = db.Column(db.Text)
    URLs = db.relationship('URL',backref='user',lazy='dynamic')
    
    def set_password(self,password):
        self.password = generate_password_hash(password)

    def check_password(self,password):
        return check_password_hash(self.password,password)


class RedirectInstance(db.Model):
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    done_gone = db.Column(db.DateTime,default=datetime.datetime.utcnow)
    url_id = db.Column(db.Integer, db.ForeignKey('URL.id'))

    @property
    def formatted_date(self):
        return '{0}-{1}-{2}'.format(self.done_gone.month,self.done_gone.day,self.done_gone.year)        

def is_valid_url(url):
    return joely_utils.url_regex.search(url)

def suitable_password(pw):
    return len(pw) >= min_pw_len 

def suitable_email(email):
    return len(email) >= min_email_len

@app.route('/',methods=['POST','GET'])
@app.route('/<int:page>',methods = ['POST','GET'])
def front_page(page=1):
    if 'email' not in session:
        flash('You have to be logged in to view this page.')
        return redirect(url_for('login'))

    da_url = None
    if request.method == 'POST':
        if is_valid_url(request.form['url']):
            new_url = joely_utils.shorten_dat(request.form['url']) 

            while len(URL.query.filter(URL.key==new_url).all()) > 0:
                new_url = joely_utils.shorten_dat(request.form['url'])

            da_url = URL(original_url=request.form['url'],
                          key=new_url,
                            user_id=session['user_id'])

            db.session.add(da_url)
            db.session.commit()
        else:
            flash('That ain\'t no valid url.')

    urls = URL.query.filter(URL.user_id==session['user_id']).order_by(URL.created.desc()).paginate(page,num_per_page)
    return render_template('home.html',urls=urls,da_url=da_url)

@app.route('/login',methods = ['POST','GET'])
def login():
    if 'email' in session:
        return redirect(url_for('front_page'))

    if request.method == 'POST':
        email = request.form['email'].lower()
        user = User.query.filter(User.email==email).first() 
        if user and user.check_password(request.form['password']):
            session['email'] = email
            session['user_id'] = user.id
            return redirect(url_for('front_page'))
        return render_template('login.html',error=True) 

    return render_template('login.html')

@app.route('/new_user',methods = ['POST','GET'])
def new_user():
    if 'email' in session:
        return redirect(url_for('front_page'))

    if request.method == 'POST':
        errors = set()
        email, pw = request.form['email'], request.form['password']
        if not suitable_password(pw):
            errors.add('password')
        if not suitable_email(email):
            errors.add('email')
        if errors: 
            return render_template('new_user.html',errors=errors)

        user = User()
        user.email = email
        user.set_password(pw)
        db.session.add(user)
        db.session.commit()
        
        session['email'] = email
        session['user_id'] = user.id
        return redirect(url_for('front_page'))
    
    return render_template('new_user.html')

@app.route('/logout',methods=['POST','GET'])
def log_out():
    for k in ('email','user_id'):
        if k in session:
            del session[k]
    return redirect(url_for('front_page'))

@app.route('/j/<shortened>',methods=['POST','GET'])
def the_whole_point(shortened): 
    url = URL.query.filter(URL.key==shortened).first_or_404()
    db.session.add(RedirectInstance(url_id=url.id))
    db.session.commit()
    return redirect(url.original_url)

@app.route('/jInfo/<shortened>',methods=['POST','GET'])
@app.route('/jInfo/<shortened>/<int:page>',methods=['POST','GET'])
def view_redirect_info(shortened,page=1):
    if 'email' not in session:
        return redirect(url_for('login'))
    
    # verify this is the right cat
    url = URL.query.filter(URL.key==shortened).first_or_404()
    if url.user_id != session['user_id']:
        flash('You do not have permission to view this page.')
        return redirect(url_for('front_page'))
    
    redirections = RedirectInstance.query.filter(RedirectInstance.url_id==url.id).order_by(RedirectInstance.done_gone.desc()).paginate(page,num_per_page)

    return render_template('redirect_info.html',url=url,rs=redirections)

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT' 
