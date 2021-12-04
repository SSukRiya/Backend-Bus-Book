import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from Redbus import app, db, bcrypt, mail, admin, posts
from Redbus.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                              RequestResetForm, ResetPasswordForm, BusForm, BookingForm)
from Redbus.models import User, Bus, BusBook
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from sqlalchemy import exc


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='sukriyakalpana@gmail.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}
If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/admin', methods=['GET','POST'])
@login_required
def admin():
    if not current_user.role == 'ROLE_ADMIN':
        flash('You do not have access to view this page.')
        return redirect(url_for('admin'))

@app.route("/home", methods=['GET', 'POST'])
@app.route('/')
def home():
    buses=BusBook.query.all()
    return render_template('home.html', buses=buses)

@app.route("/book/tickets", methods=['GET', 'POST'])
@login_required
def book():
    form=BookingForm()
    if form.validate_on_submit():
        buses=BusBook(busname=form.busname.data,startingpoint=form.startingpoint.data,destination=form.destination.data,dateoftravel=form.dateoftravel.data)#, person=current_user)
        try:
            db.session.add(buses)
            db.session.commit()
        except exc.IntegrityError:
            db.session.rollback()

        flash('Your Ticket Booked','success')
        return redirect(url_for('home'))
    return render_template('book.html',title='Book ticket',form=form)#,buses=buses)

@app.route("/about")
def about():
    buss=Bus.query.all()
    return render_template('about.html', title='About',buss=buss)

@app.route("/bus/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form=BusForm()
    if form.validate_on_submit():
        bus = Bus(busname=form.busname.data, startingpoint=form.startingpoint.data, destination=form.destination.data,traveltime=form.traveltime.data,routedistance=form.routedistance.data,person=current_user)#, admitter=current_user)
        try:
            db.session.add(bus)
            db.session.commit()
        except exc.IntegrityError:
            db.session.rollback()

        flash('Bus Added','success')
        return redirect(url_for('about'))
    return render_template('create_post.html', title='Bus Info', form=form, legend='Bus Info')#,buss=buss)

@app.route("/bus/<int:post_id>")
def post(post_id):
    buss = BusBook.query.get_or_404(post_id)
    return render_template('post.html', busname=post.busname,buss=buss)

@app.route("/bus/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    buss = Bus.query.get_or_404(post_id)
    if buss.person != current_user:
        abort(403)
    db.session.delete(buss)
    db.session.commit()
    flash('Slot has been deleted!', 'success')
    return redirect(url_for('about'))
