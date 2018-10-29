import logging
from flask import Flask, jsonify, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_login import current_user, login_user, logout_user, login_required
from flask_mail import Mail
from forms import LoginForm
from config import Config

from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import InputRequired, Email, Length, AnyOf, DataRequired, EqualTo

app = Flask(__name__)
bootstrap = Bootstrap(app)
mail = Mail(app)
app.config.from_object(Config)

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
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        #user = User.query.filter_by(username=username.data).first()
        user = 'Kathir'
        if user is not None:
            raise ValidationError(_('Please use a different username.'))

    def validate_email(self, email):
        #user = User.query.filter_by(email=email.data).first()
        user='kathir@gmail.com'
        if user is not None:
            raise ValidationError(_('Please use a different email address.'))


class ResetPasswordRequestForm(Form):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(Form):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(),EqualTo('password')])
    submit = SubmitField('Request Password Reset')


@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        return "Login Successfull"
    return render_template('login.html', title='Sign In', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = form.username.data
        email = form.email.data
        print user
        print email
        password = form.password.data
        print password
        flash('Congrats, new user created!!!')
        return redirect(url_for('login'))
    return render_template('register.html', title='SignUp', form=form)

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
