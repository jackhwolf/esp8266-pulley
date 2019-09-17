import boto3
from flask import Blueprint, session, render_template, redirect
from flask_restplus import Api, Resource, reqparse
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from functools import wraps
from boto3.dynamodb.conditions import Key, Attr, Not
import os
import time
from uuid import uuid4
import hashlib

# setup blueprint

auth_bp = Blueprint('auth', __name__)


##############
# LOGIN FORM #
##############

class LoginForm(FlaskForm):
    ''' require username & password, submit with button '''
    uname = StringField('Username: ', validators=[DataRequired()])
    pword = PasswordField('Password: ', validators=[DataRequired()])
    submit = SubmitField('Login!')


################
# LOGIN ROUTES #
################

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    ''' verify uname/pword combo,
        if user is auth, give them a token. else,
        reroute to login '''
    form = LoginForm()
    if form.validate_on_submit():
        uname, pword = form.uname.data, form.pword.data
        if uname == 'dean' and pword == 'dean':
            sid = sessiondb().create_active_session(uname)
            session['sid'] = sid
        return redirect('/')
    return render_template('login.html',
                           main_txt='Sign in!',
                           form=form)


@auth_bp.route('/logout')
def logout():
    ''' for user logout, clear token and ping api
        to delete session'''
    print('logging out', session.get('sid', -1))
    if session.get('sid', None) is not None:
        sessiondb().delete_active_session(session.get('sid'))
        del session['sid']
    form = LoginForm()
    return redirect('login')


###################
# USER DB CLASSES #
###################

########
# util #
########

def tokenize(x):
    ''' return hashed string of x '''
    return f"{hashlib.sha256(str(x).encode()).hexdigest()[::2]}==="

def create_session_id():
    return f"{uuid4().hex[::2]}{str(int(time.time()))[::2]}"


#################
# base db class #
#################

class db:
    ''' subclass to handle db conn - throws errors '''

    def __init__(self):
        ''' get a dynamodb resource '''
        self.res = boto3.resource(
                        'dynamodb',
                        aws_access_key_id=os.environ.get(
                                            'AWS_SKIPPYELVIS_STONESOUP_ACCESS'),
                        aws_secret_access_key=os.environ.get(
                                            'AWS_SKIPPYELVIS_STONESOUP_SECRET'),
                        region_name='us-west-1'
                    )

    def create_(self, tid, key_schema, attribute_defn, **kw):
        ''' create table '''
        self.res.create_table(
            TableName=tid,
            KeySchema=key_schema,
            AttributeDefinitions=attribute_defn,
            ProvisionedThroughput={
                "ReadCapacityUnits": kw.get('RCU', 2),
                "WriteCapacityUnits": kw.get('RCU', 2)
            }
        )

    def put_(self, tid, item):
        ''' put item(s) into table '''
        table = self.res.Table(tid)
        if not issubclass(type(item), list):
            item = [item]
        for i in item:
            table.put_item(Item=i)

    def delete_(self, tid, item):
        table = self.res.Table(tid)
        table.delete_item(
            Key=item
        )

    def query_(self, tid, keycondexpr):
        table = self.res.Table(tid)
        resp = table.query(KeyConditionExpression=keycondexpr)
        return resp


#####################
# class for db conn #
#####################

class conn(db):
    ''' class to handle connection to user db '''

    def __init__(self, tid, key_schema, attr_defn):
        db.__init__(self)
        self.tid = tid
        self.key_schema = key_schema
        self.attr_defn = attr_defn

    def create(self, **kw):
        try:
            self.create_(
                self.tid,
                self.key_schema,
                self.attr_defn, **kw
            )
            return True
        except Exception as e:
            print(e)
            return False

    def put(self, item, **kw):
        try:
            self.put_(
                self.tid,
                item
            )
            return True
        except Exception as e:
            print(e)
            return False

    def delete(self, item, **kw):
        try:
            self.delete_(
                self.tid,
                item
            )
            return True
        except Exception as e:
            print(e)
            return False

    def query(self, keycondexpr):
        try:
            resp = self.query_(self.tid, keycondexpr)
            return resp
        except Exception as e:
            print(e)
            return {'error': str(e)}


#############################################
# classes to handle specific db connections #
#############################################

class sessiondb(conn):
    ''' connect to user db '''

    class CustomExceptions:
        ''' all custom exceptions to be thrown '''

        class SessionAlreadyExists(Exception):
            ''' when existing session id is given out '''

            def __init__(self):
                Exception.__init__(self, "User already exists")

        class TokenDoesNotMatch(Exception):
            ''' when session id does not match given token'''

            def __init__(self):
                Exception.__init__(self, "Username and Password not in system")

        class SessionDoesNotExist(Exception):
            ''' when a given session id does not exist '''

            def __init__(self):
                Exception.__init__(self, "Username does not exist")

    def __init__(self):
        ''' define table name and schema, init connection '''

        self.tid = 'sessions-sendit'
        self.key_schema = [
                    {
                        'AttributeName': 'sessionid',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'token',
                        'KeyType': 'RANGE'
                    }
                ]
        self.attr_defn = [
                    {
                        'AttributeName': 'sessionid',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'token',
                        'AttributeType': 'S'
                    }
                ]
        conn.__init__(self, self.tid, self.key_schema, self.attr_defn)

    def format_session_entry(self, sessionid, token):
        ''' give each entry a common schema '''
        entry = {
            'sessionid': sessionid,
            'token': token
        }
        return entry

    def create_active_session(self, uname):
        ''' class to add new session to db '''
        sid = create_session_id()
        entry = self.format_session_entry(sid, tokenize(uname))
        self.put(entry)
        return sid

    def delete_active_session(self, sid):
        key = {'sessionid': sid}
        try:
            r = self.get_existing_session(sid)
            key['token'] = r.get('Items', [{}])[0].get('token', -1)
            self.delete(key)
            return True
        except Exception as e:
            print(e)
            return False

    def get_existing_session(self, sid):
        r = self.query(Key('sessionid').eq(sid))
        if r.get('Count', 0) <= 0:
            raise self.CustomExceptions.SessionDoesNotExist
        return r

    def does_session_exist(self, sid):
        r = self.query(Key('sessionid').eq(sid))
        if r.get('Count', 0) <= 0:
            return False
        return True
