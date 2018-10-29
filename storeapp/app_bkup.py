import logging
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, Response
from flask_bootstrap import Bootstrap
from flask_login import current_user, login_user, logout_user, login_required
from flask_mail import Mail
from forms import LoginForm
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from datetime import datetime

from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import InputRequired, Email, Length, AnyOf, DataRequired, EqualTo 
from lib import s3client 
from lib import rds_client as rds

app = Flask(__name__)
bootstrap = Bootstrap(app)
mail = Mail(app)
app.config.from_object(Config)
s3obj = s3client.S3Client()

db = rds.RDSPostgresDb()
db_session = db.get_session()
db_engine = db.engine
userdetails = {}
global user_id 
'''
@app.route("/")
def hello():
    app.logger.debug('this is a DEBUG message')
    app.logger.info('this is an INFO message')
    app.logger.warning('this is a WARNING message')
    app.logger.error('this is an ERROR message')
    app.logger.critical('this is a CRITICAL message')
    return "<h1 style='color:blue'>Hello There!</h1>"
@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != 'admin' or request.form['password'] != 'admin':
            error = 'Invalid Credentials. Please try again.'
        else:
            return redirect(url_for('login'))
    return render_template('login.html', error=error)

'''

class LoginForm(Form):
    username = StringField('Username', validators=[InputRequired(), Length(min=5, max=30), Email(message='Email required')])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=30)])
    remember = BooleanField('remember me')

class RegisterForm(Form):
    firstname = StringField('Firstname', validators=[DataRequired()])
    lastname = StringField('Lastname', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=30)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    #submit = SubmitField('Register')

    """
    def validate_username(self, username):
        #user = User.query.filter_by(username=username.data).first()
        user = 'Kathir'
        if user is None:
            raise ValidationError(_('Please use a different username.'))

    def validate_email(self, email):
        #user = User.query.filter_by(email=email.data).first()
        user='kathir@gmail.com'
        if user is None:
            raise ValidationError(_('Please use a different email address.'))
    """

class ResetPasswordRequestForm(Form):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(Form):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(),EqualTo('password')])
    submit = SubmitField('Request Password Reset')

class Objectstore(Form):
    filename = StringField('Filename', validators=[InputRequired(), Length(min=1, max=80)])

class downloadForm(Form):
    filename = StringField('Filename', validators=[InputRequired(), Length(min=1, max=80)])

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        result = db_session.execute(rds.model.UserInfo.__table__.select().where(rds.model.UserInfo.email==form.username.data))
        if result:
            userdata = result.fetchall()
            user_id = userdata[0][0]
            print user_id
            if(check_password_hash(userdata[0][3], form.password.data)):
                return redirect(url_for('upload', userid= userdata[0][0]))
    return render_template('login.html', title='Sign In', form=form)


def user_details(userdata):
    userinfo = {'fn': userdata[1], 'ln': userdata[2], 'email': userdata[3]}
    return userinfo

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hash_passwd = generate_password_hash(form.password.data, method='sha256')
        user_record = dict(uuid=str(uuid.uuid4()),
                        firstname=form.firstname.data,
                        lastname=form.lastname.data,
                        password=hash_passwd,
                        email=form.email.data,
                        created_date=datetime.now())
        rds.upsert(db_session, rds.model.UserInfo, user_record)
        flash('Congrats, new user created!!!')
        return redirect(url_for('login'))
    return render_template('register.html', title='SignUp', form=form)

#@app.route('/upload', methods=['GET', 'POST'])
#def upload():
@app.route('/upload/<userid>', methods=['GET', 'POST'])
def upload(userid):
    form = Objectstore()
    userList = []
    fileList=[]
    result = db_session.execute(rds.model.UserInfo.__table__.select().where(rds.model.UserInfo.uuid==userid))
    userinfo = result.fetchall()
    userfile =userinfo[0]
    userset = {'fn': userfile[1], 'ln': userfile[2], 'email': userfile[4]}
    userList.append(userset)
    fileList = s3obj.list_all_objects('wpmedia123')

    if 'Choose File' in request.files and form.validate_on_submit():
        file = request.files['Choose File']
        s3obj.upload_file(file, 'wpmedia123', form.filename.data)
        flash("filename " + form.filename.data +"is created in S3 bucket")
    return render_template("upload.html", name=userid, userdata=userList, files=fileList, title="upload", form=form)

@app.route('/download', methods=['GET'])
def download():
    downloadFile = request.args.get('downloadFile')
    attachment="attachment;filename="+downloadFile
    res = s3obj.get_object(bucket='wpmedia123', filename=downloadFile)
    return Response(res['Body'].read(), mimetype='text/plain', headers={"Content-Disposition":attachment})

@app.route('/delete', methods=['POST'])
def delete():
    print user_id
    deleteFile = request.form['deleteFile']
    s3obj.delete_object('wpmedia123', deleteFile)
    return redirect(url_for('upload', userid=user_id)) 

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        #user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


if __name__ == "__main__":
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
    app.run(host='0.0.0.0', port=8080, debug=True)
    #app.run(debug=True)
