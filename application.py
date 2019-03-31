import logging
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, Response, session
from flask_bootstrap import Bootstrap
from flask_login import current_user, login_user, logout_user, login_required
from flask_mail import Mail
from forms import LoginForm
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import InputRequired, Email, Length, AnyOf, DataRequired, EqualTo 
from lib import s3client 
from lib import rds_client as rds
import os

application = Flask(__name__)
bootstrap = Bootstrap(application)
mail = Mail(application)
application.config.from_object(Config)
s3obj = s3client.S3Client()
login_manager=LoginManager()
login_manager.init_app(application)
login_manager.login_view = 'login'
db = rds.RDSPostgresDb()
db_session = db.get_session()
db_engine = db.engine
userdetails = {}
user_id = []
filedata =[]

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

class ResetPasswordRequestForm(Form):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(Form):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(),EqualTo('password')])
    submit = SubmitField('Request Password Reset')

class Objectstore(Form):
    filename = StringField('Filename', validators=[InputRequired(), Length(min=1, max=80)])
    description = StringField('Description', validators=[InputRequired(), Length(min=1, max=80)])

class downloadForm(Form):
    filename = StringField('Filename', validators=[InputRequired(), Length(min=1, max=80)])


#prevent cached responses
@application.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers["Cache-Control"] = 'Public, max-age=0'
    return r

@application.route('/', methods=['GET', 'POST'])
@application.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        result = db_session.execute(rds.model.UserInfo.__table__.select().where(rds.model.UserInfo.email==form.username.data))
        if result:
            userdata = result.fetchall()
            if(check_password_hash(userdata[0][3], form.password.data)):
                return redirect(url_for('upload', userid= userdata[0][0]))
    return render_template('login.html', title='Sign In', form=form)

@application.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hash_passwd = generate_password_hash(form.password.data, method='sha256')
        uniqueId = str(uuid.uuid4())
        user_record = dict(uuid=uniqueId,
                        firstname=form.firstname.data,
                        lastname=form.lastname.data,
                        password=hash_passwd,
                        email=form.email.data,
                        created_date=datetime.now())
        rds.upsert(db_session, rds.model.UserInfo, user_record)
        filereq = form.firstname.data+"_"+uniqueId[:8]
        filename= os.getcwd()+"/file.txt" 
        print filereq
        print filename
        s3obj.upload_data(filename, 'viswa0531', filereq+"/file.txt")
        flash('Congrats, new user created!!!')
        return redirect(url_for('login'))
    return render_template('register.html', title='SignUp', form=form)

@application.route('/upload/<userid>', methods=['GET', 'POST'])
def upload(userid):
    form = Objectstore()
    userList = []
    fileList=[]
    result = db_session.execute(rds.model.UserInfo.__table__.select().where(rds.model.UserInfo.uuid==userid))
    userinfo = result.fetchall()
    userfile =userinfo[0]
    userset = {'fn': userfile[1], 'ln': userfile[2], 'email': userfile[4]}
    userList.append(userset)
    user_id.append(userid)
    filereq=userfile[1].strip()+"_"+userid[:8]+"/"
    try:
	if(userfile[4] == "vsingh0412@gmail.com"):
	    filedata = filelist_admin()
        else:
            filedata = filelist(userid)
    except:
        print "user List Empty"

    if 'Choose File' in request.files and form.validate_on_submit():
        startTime = datetime.now()
        file = request.files['Choose File']
        s3obj.upload_file(file, 'viswa0531', filereq+form.filename.data)
        flash("filename " + form.filename.data +" is created in S3 bucket")
        filerecord = dict(uuid=str(uuid.uuid4()), filename = filereq+form.filename.data, uploaded_time = startTime, updated_time=startTime, description=form.description.data, owner=userid) 
        rds.upsert(db_session, rds.model.FileInfo, filerecord)
	if(userfile[4] == "vsingh0412@gmail.com"):
	    filedata = filelist_admin()
        else:
            filedata = filelist(userid)
    return render_template("upload.html", name=userid, userdata=userList, files=filedata, title="upload", form=form)


def fileRecord(filename, description):
    dictrecord = {}
    data =[]
    fileresult = db_session.execute(rds.model.FileInfo.__table__.select().where(rds.model.FileInfo.filename==filename))
    filedata = fileresult.fetchall()
    print filedata[0]
    dictrecord['Key'] = filedata[0][1]
    dictrecord['description'] = filedata[0][4]
    dictrecord['uploadedTime']=filedata[0][2]
    dictrecord['LastModified']=filedata[0][3]
    data.applicationend(dictrecord)
    return data

def filelist(uuid):
    dictrecord = {}
    data =[]
    fileresult = db_session.execute(rds.model.FileInfo.__table__.select().where(rds.model.FileInfo.owner==uuid))
    filecontent = fileresult.fetchall()
    return filecontent 

def filelist_admin():
    dbinfo = db_session.execute(rds.model.FileInfo.__table__.select())
    dblist = dbinfo.fetchall()
    return dblist

@application.route('/download', methods=['GET'])
def download():
    downloadFile = request.args.get('downloadFile')
    attachment="attachment;filename="+downloadFile
    res = s3obj.get_object(bucket='viswa0531', filename=downloadFile)
    return Response(res['Body'].read(), mimetype='text/plain', headers={"Content-Disposition":attachment})

@application.route('/delete', methods=['POST'])
def delete():
    deleteFile = request.form['deleteFile']
    s3obj.delete_object('viswa0531', deleteFile)
    db_session.execute(rds.model.FileInfo.__table__.delete().where(rds.model.FileInfo.filename==deleteFile))
    db_session.commit()
    return redirect(url_for('upload', userid=user_id[0])) 

@application.route('/logout')
def logout():
    session['logged_in'] = False
    return redirect(url_for('login'))

@application.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html', title='Reset Password', form=form)

if __name__ == "__main__":
    gunicorn_logger = logging.getLogger('gunicorn.error')
    application.logger.handlers = gunicorn_logger.handlers
    application.logger.setLevel(gunicorn_logger.level)
    application.run(host='0.0.0.0', port=5001, debug=True)
    #application.debug=True
    #application.run()
    #application.run(debug=True)
