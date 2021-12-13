from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from sqlalchemy.orm import defaultload
from Redbus import db, login, app, admin
from flask_login import UserMixin, login_user, current_user, logout_user, login_required
from flask_admin.contrib.sqla import ModelView
from datetime import datetime
from flask import request

@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    is_admin = db.Column(db.Boolean, default=False)
    booking = db.relationship('Bus', backref='person', lazy=True, primaryjoin="User.id == Bus.user_id")
    #updating = db.relationship('BusBook', backref='admitter', lazy=True, primaryjoin="User.id == BusBook.book_id")
    
    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')
    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"


class Bus(db.Model,UserMixin):
    id = db.Column(db.Integer,primary_key=True)
    busname = db.Column(db.String(100), nullable=False)
    #date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    startingpoint = db.Column(db.Text, nullable=False)
    destination = db.Column(db.Text, nullable=False)
    routedistance=db.Column(db.String(100))
    traveltime=db.Column(db.String(10))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    
    #posts = db.relationship('Post', backref='administrator', lazy=True)
    def __repr__(self):
        return f"Post('{self.busname}', '{self.startingpoint}', '{self.destination}', '{self.routedistance}','{self.traveltime}')"

class BusBook(db.Model,UserMixin):
    id = db.Column(db.Integer,primary_key=True)
    busname = db.Column(db.String(100), nullable=False)
    dateoftravel = db.Column(db.DateTime)#strptime(request.form['data_apreensao'],'%Y-%m-%d'))
    startingpoint = db.Column(db.Text, nullable=False)
    destination = db.Column(db.Text, nullable=False)
    #book_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    def __repr__(self):
        return f"User('{self.busname}','{self.startingpoint}', '{self.destination}','{self.dateoftravel}')"

#updating = db.relationship('Bus', backref='person', lazy=True, primaryjoin="User.id == Bus.user_id")
#booking = db.relationship('Bus', backref='person', lazy=True, primaryjoin="User.id == BusBook.book_id")
    

admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Bus, db.session))
admin.add_view(ModelView(BusBook, db.session))
