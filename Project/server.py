import os
from io import BytesIO
import flask
import hashlib
from sqlalchemy import or_, desc
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta, datetime
from flask import Flask, flash, jsonify, redirect, url_for, render_template, send_from_directory, request, Response, session, send_file, abort
import time
from random import randint
import json
import flask_admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink
import random

filePath = os.path.realpath(__file__)
filePath = filePath.replace('\\server.py', '')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'KutyaFasz123'
app.config['UPLOAD_FOLDER'] = './static/uploads'
app.permanent_session_lifetime = timedelta(days=30)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{filePath}/haziorvos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
admin = flask_admin.Admin(app, name='Haziorvos')

#databases
class Beteg(db.Model):
    TAJ = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    nev = db.Column(db.String(30))
    lakcim = db.Column(db.String(255))
    szuletes = db.Column(db.Date)
    
    vizsgalatok = db.relationship("Vizsgalat", backref="beteg", order_by="desc(Vizsgalat.datum)")
    erzekenysegek = db.relationship("Erzekeny", backref="beteg")
    felirasok = db.relationship("Felir", backref="beteg")
    diagnosztizalasok = db.relationship("Diagnosztizal", backref="beteg")
    
    def __repr__(self):
        return f'{self.TAJ}; {self.nev}'

class Vizsgalat(db.Model):
    vkod = db.Column(db.Integer, primary_key=True)
    TAJ = db.Column(db.Integer, db.ForeignKey("beteg.TAJ"))
    datum = db.Column(db.DateTime)
    
    felirasok = db.relationship("Felir", backref="vizsgalat")
    diagnosztizalasok = db.relationship("Diagnosztizal", backref="vizsgalat")
    
    def __repr__(self):
        return f'{self.vkod}; {self.TAJ}; {self.datum}'

class Gyogyszer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gyogyszer_neve = db.Column(db.String)
    
    erzekenysegek = db.relationship("Erzekeny", backref="gyogyszer")
    felirasok = db.relationship("Felir", backref="gyogyszer")

    def __repr__(self):
        return f'{self.id}; {self.gyogyszer_neve}'

class Betegseg(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    betegseg_neve = db.Column(db.String)
    
    diagnosztizaciok = db.relationship("Diagnosztizal", backref="betegseg")

    def __repr__(self):
        return f'{self.id}; {self.betegseg_neve}'

class Erzekeny(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    TAJ = db.Column(db.Integer, db.ForeignKey("beteg.TAJ"))
    gyogyszer_id = db.Column(db.Integer, db.ForeignKey("gyogyszer.id"))

    def __repr__(self):
        return f'{self.id}; {self.TAJ}; {self.gyogyszer_id}'

class Felir(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    TAJ = db.Column(db.Integer, db.ForeignKey("beteg.TAJ"))
    gyogyszer_id = db.Column(db.Integer, db.ForeignKey("gyogyszer.id"))
    vkod = db.Column(db.Integer, db.ForeignKey("vizsgalat.vkod"))
    datum =  db.Column(db.DateTime)

    def __repr__(self):
        return f'{self.id}; {self.TAJ}; {self.gyogyszer_id}; {self.datum}'

class Diagnosztizal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    TAJ = db.Column(db.Integer, db.ForeignKey("beteg.TAJ"))
    betegseg_id = db.Column(db.Integer, db.ForeignKey("betegseg.id"))
    vkod = db.Column(db.Integer, db.ForeignKey("vizsgalat.vkod"))
    datum =  db.Column(db.DateTime)

    def __repr__(self):
        return f'{self.id}; {self.TAJ}; {self.betegseg_id}; {self.datum}'

with app.app_context():
    db.create_all()

#admin panel
#class BetegView(ModelView):
#    column_list = []
#    form_columns = []
#    column_display_pk = True
#    page_size = 100
#    can_set_page_size = True 
#    #column_default_sort = ('date', True)
#    column_searchable_list = []
#    column_filters = []
#
#admin.add_link(MenuLink(name='Site', url='/'))

class BetegView(ModelView):
    column_list = ["TAJ", "nev", "lakcim", "szuletes"]
    form_columns = ["vizsgalatok", "erzekenysegek", "felirasok", "diagnosztizalasok", "TAJ", "nev", "lakcim", "szuletes"]
    column_display_pk = True
    page_size = 100
    can_set_page_size = True

admin.add_view(BetegView(Beteg, db.session))
admin.add_view(ModelView(Vizsgalat, db.session))
admin.add_view(ModelView(Gyogyszer, db.session))
admin.add_view(ModelView(Betegseg, db.session))
admin.add_view(ModelView(Erzekeny, db.session))
admin.add_view(ModelView(Felir, db.session))
admin.add_view(ModelView(Diagnosztizal, db.session))

#ip functions
@app.before_request
def showIp():
    print(request.headers.get('X-FORWARDED-FOR'))

@app.before_request
def fixAdmin():
    if request.path == "/admin":
        return redirect(f"{request.url_root}admin/")

@app.route('/')
def index():
    betegek = Beteg.query.all()
    return render_template('index.html', betegek=betegek)

@app.route('/betegSearch')
def betegSearch():
    q = request.args['q']
    betegek = Beteg.query.filter(or_(Beteg.nev.contains(q), Beteg.TAJ.contains(q))).all()
    return render_template('index.html', betegek=betegek)

@app.route('/beteg/<taj>')
def beteg(taj):
    dtNow = time.time() 
    beteg = Beteg.query.filter(Beteg.TAJ == taj).first()
    vizsgalatokq = Vizsgalat.query.filter(Vizsgalat.TAJ == taj).order_by(desc(Vizsgalat.datum)).all()
    betegsegek = Betegseg.query.all()
    gyogyszerek = Gyogyszer.query.all()
    
    return render_template('beteg.html',dtNow=dtNow, beteg=beteg,gyogyszerek=gyogyszerek, betegsegek=betegsegek, vizsgalatokq=vizsgalatokq, Diagnosztizal=Diagnosztizal, Felir=Felir)

@app.route('/dev/vizsgalat_feltolt', methods=['get', 'post'])
def devVizsgalat_feltolt():
    taj = request.form['taj']
    datum = datetime.strptime(request.form['datum'].replace('T', ' '), '%Y-%m-%d %H:%M')
    db.session.add(Vizsgalat(TAJ=taj, datum=datum))
    db.session.commit()
    return redirect(f'/beteg/{taj}')

@app.context_processor
def handle_context():
    return dict(session=session, db=db, datetime=datetime, reversed=reversed)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)