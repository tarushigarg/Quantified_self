import os
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import matplotlib.pyplot as plt


cur_path = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, static_url_path='/static')
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.sqlite3"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False    
app.config['SECRET_KEY'] = "key"
db = SQLAlchemy(session_options={"autoflush": False})
db.init_app(app)
app.app_context().push()

def to_date(string):
    d_t = (string.split('-'))

#MODELS
class Users(db.Model):
    _tablename_ = 'users'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    username = db.Column(db.String, nullable = False, unique = True)
    password = db.Column(db.String, nullable = False)
    def __init__(self, username, password):
        self.username = username
        self.password = password

class Trackers(db.Model):
    _tablename_ = 'trackers'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable = False)
    name = db.Column(db.String, nullable = False, unique = True)
    input_type = db.Column(db.String)
    settings = db.Column(db.String)
    def __init__(self, user_id, name, input_type, settings='None'):
        self.user_id = user_id
        self.name = name
        self.input_type = input_type
        self.settings = settings

class Logs(db.Model):
    _tablename_ = 'logs'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    tracker_id = db.Column(db.Integer, db.ForeignKey('trackers.id'), nullable = False)
    date = db.Column(db.String, nullable = False)
    value = db.Column(db.String, nullable = False)
    details = db.Column(db.String)
    def __init__(self, tracker_id, date, value, details):
        self.tracker_id = tracker_id
        self.value = value
        self.details = details
        self.date = date
#TO CHECK IF THE USER ALREADY LOGGED IN
def is_logged_in():
    if 'logged_in' in session:
        return True
    else:
        return False


#HOME PAGE
@app.route("/")
@app.route('/home')
def home():
    if not is_logged_in():
        return redirect(url_for('login'))
    trackers = Trackers.query.filter_by(user_id = session['id']).all()
    return render_template('home.html', session = session, trackers = trackers)
    
#LOGIN PAGE
@app.route("/login", methods = ['POST', 'GET'])
def login():
    if request.method == 'POST':
        form = request.form
        user = Users.query.filter_by(username = form.get('username'), password = form.get('password')).all()
        if user != []:
            session['logged_in'] = True
            session['id'] = user[0].id
            session['username'] = form.get('username')
            return redirect(url_for('home'))
        else:
            flash('Incorrect username or password')

    return render_template('login.html', session = session)

#TO REGISTER
@app.route("/register", methods = ['POST', 'GET'])
def register():
    if request.method == 'POST':
        form = request.form
        if form.get('password') == form.get('password2'):
            new_user = Users(form['username'], form['password'])
            db.session.add(new_user)
            db.session.commit()
        else:
            flash("password and repeat password don't match")
            return redirect(url_for('register'))
    return render_template('register.html', session = session)

#TO ADD A NEW TRACKER
@app.route("/trackers/add", methods=['GET', 'POST'])
def add_trackers():
    if not 'logged_in' in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        form = request.form
        if form.get('settings') != "":
            new_tracker = Trackers(session['id'], form.get('name'), form.get('options'), str(form.get('settings').split(',')))
        else:
            new_tracker = Trackers(session['id'], form.get('name'), form.get('options'))
        db.session.add(new_tracker)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('add_trackers.html')

#TO EDIT A TRACKER
@app.route("/trackers/<tracker_id>/edit", methods = ['GET', 'POST'])
def edit_tracker(tracker_id):
    tracker = Trackers.query.filter_by(id = tracker_id).first()
    if not 'logged_in' in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        form  =request.form
        cur_tracker = Trackers.query.filter_by(id = tracker_id).first()
        cur_tracker.name = form.get('name')
        cur_tracker.input_type = form.get('type')
        cur_tracker.settings = form.get('settings')
        logs_in_tracker = Logs.query.filter_by(tracker_id=tracker_id).all()
        for log in logs_in_tracker:
            db.session.delete(log)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit_trackers.html', tracker=tracker)

#TO DELETE A TRACKER
@app.route("/trackers/<tracker_id>/delete")
def remove_tracker(tracker_id):
    if not 'logged_in' in session:
        return redirect(url_for('login'))
    to_be_removed = Trackers.query.filter_by(id = tracker_id).first()
    db.session.delete(to_be_removed)
    log_in_tracker = Logs.query.filter_by(tracker_id=tracker_id).all()
    for log in log_in_tracker:
        db.session.delete(log_in_tracker)
    db.session.commit()
    return redirect(url_for('home'))

#TO ADD A NEW LOG TO THE GIVEN TRACKER
@app.route("/trackers/<tracker_id>/records/add", methods = ['POST', 'GET'])
def add_record(tracker_id):
    if not 'logged_in' in session:
        return redirect(url_for('login'))
    tracker = Trackers.query.filter_by(id = tracker_id).first()
    options = None
    if tracker.input_type == "Multiple Choice":
        options = tracker.settings.split(',')
    if request.method == 'POST':
        form = request.form
        value = None
        if tracker.input_type == "Numerical":
            value = int(form.get('value'))
            new_log = Logs(tracker_id, datetime.today().strftime('%Y-%m-%d'),value, form.get('details'))
        if tracker.input_type == "Multiple Choice":
            value = form.get('value')
            new_log = Logs(tracker_id, datetime.today().strftime('%Y-%m-%d'),value, form.get('details'))
        if tracker.input_type == "Timestamp":
            value = form.get('value')
            new_log = Logs(tracker_id, datetime.today().strftime('%Y-%m-%d at %H-%M-%S'), value, form.get('details'))

        db.session.add(new_log)
        db.session.commit()
        return redirect(f'/trackers/{tracker_id}/view')


    return render_template('add_record.html', tracker = tracker, options = options)

#TO VIEW THE LOGS IN A TRACKER
@app.route("/trackers/<tracker_id>/view")
def view_trackers(tracker_id):
    if not 'logged_in' in session:
        return redirect(url_for('login'))
    tracker = Trackers.query.filter_by(id = tracker_id).first()
    logs = Logs.query.filter_by(tracker_id = str(tracker_id)).all()
    if logs!=[]:
        if tracker.input_type == "Numerical":
            min_date = date(int(logs[0].date.split('-')[0]), int(logs[0].date.split('-')[1]), int(logs[0].date.split('-')[2]))
            Y = [(date(int(log.date.split('-')[0]), int(log.date.split('-')[1]), int(log.date.split('-')[2]))-min_date) .days for log in logs]
            X = [int(log.value) for log in logs]
            file = open('./static/images/'+tracker_id+".png", "w+")
            file.close()
            plt.plot(list(Y), list(X))
            plt.savefig('./static/images/'+tracker_id+'.png')
            plt.clf() #Used to clear the pyplot buffer
        elif tracker.input_type == "Multiple Choice":
            log_data = {}
            options = tracker.settings.split(',')
            for log in logs:
                value = None
                for i in range(len(options)):
                    if options[i] == log.value:
                        value = i
                        break
                if options[value] not in log_data:
                    log_data[log.value] = 1
                else:
                    log_data[log.value] = log_data[log.value]+1
            values = log_data.values()
            file = open('./static/images/'+tracker_id+".png", "w+")
            file.close()
            plt.bar(log_data.keys(), values, color ='maroon', width = 0.4)
            plt.savefig('./static/images/'+tracker_id+'.png')
            plt.clf()
    return render_template('view_trackers.html', tracker_id = tracker_id, logs = logs, tracker=tracker)

#TO EDIT A LOGS DATA
@app.route("/tracker/<tracker_id>/logs/<log_id>", methods = ['GET', 'POST'])
def edit_logs(tracker_id, log_id):
    tracker = Trackers.query.filter_by(id = tracker_id).first()
    log = Logs.query.filter_by(id = log_id).first()
    options = tracker.settings.split(',')
    if request.method == "POST":
        form = request.form
        if form.get('submit') == "Delete":
            db.session.delete(log)
            db.session.commit()
            return redirect(f'/trackers/{tracker_id}/view')
        if form.get('submit') == "Edit":
            if tracker.input_type == "Numerical":
                log.tracker_id = tracker_id
                log.date = form.get('date')
                log.value = form.get('value')
                log.details = form.get('details')
            elif tracker.input_type == "Multiple Choice":
                log.tracker_id = tracker_id
                log.value = form.get('value')
                log.details = form.get('details')
            else:
                log.tracker_id = tracker_id
                log.value = form.get('value')
                log.details = form.get('details')
            db.session.commit()
            return redirect(f'/trackers/{tracker_id}/view')

    return render_template('edit_logs.html', tracker = tracker, log = log ,options = options)
#TO LOGOUT
@app.route("/logout")
def logout():
    session.pop('logged_in')
    return redirect(url_for('login'))


#RUNNING THE APP
if __name__ == "__main__":
    app.run(debug=True)