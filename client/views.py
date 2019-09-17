import requests
from flask import Blueprint, render_template, session, redirect
from flask_restplus import Api, Resource, reqparse
from functools import wraps
from server.auth import sessiondb as sdb
from server.esp8266conn import pulley


########
# UTIL #
########

destmap = {
    1: 'HIGH',
    0: 'LOW'
}


def gottasignin(f):
    ''' wrapper function to reroute unathenticated users '''
    @wraps(f)
    def decorated(*args, **kwargs):
        # if there is no/invalid sessionid in session, redirect to login
        if 'sid' not in session or not sdb().does_session_exist(session.get('sid')):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated


################
# CREATE VIEWS #
################

views_bp = Blueprint('views', __name__)


@views_bp.route('/')
@views_bp.route('/sendit')
@gottasignin
def sendit_choice():
    ''' present user with links to request that the
        pulley be moved up or down '''
    return render_template('select-dest.html')


@views_bp.route('/sendit/<int:reqdest>')
@views_bp.route('/sendit/<reqdest>')
@gottasignin
def sendit(reqdest):
    ''' where user's request to move the pulley hits
        reqdest: 0 --> up, 1 --> down '''
    # reqdest must be an int 0 or 1
    if not isinstance(reqdest, int) or reqdest not in [0, 1]:
        return {'error-message': 'requested destination must be either 0 or 1'}
    # before we tell the pulley to move, we should stop the pulley
    r = requests.get('http://127.0.0.1:5000/stopmovement').json()
    # we're safe, ping the api to request movement
    r = requests.post('http://127.0.0.1:5000/requestmovement',
                      params={'dest': reqdest}).json()
    # the pulley is moving
    if r['moving'] == 1:
        kw = {
            'title_txt': 'in progress...',
            'main_txt': f"Moving to {reqdest}!",
            'sub_txt': r['message'],
            'links': [
                ['/stop', 'Stop pulley'],
                [f"/sendit/{int(not reqdest)}", 'Send pulley back.']
            ]
        }
    # the pulley is not moving
    elif r['moving'] == 0:
        kw = {
            'title_txt': 'Done.',
            'main_txt': 'No action necessary.',
            'sub_txt': r['message']
        }
    return render_template('request-mvmt-result.html', **kw)


@views_bp.route('/stop')
@gottasignin
def stop():
    ''' when user wants to tell pulley to stop '''
    # attemp to stop pulley
    r = requests.get('http://127.0.0.1:5000/stopmovement').json()
    # success
    if r['stoppedmovement'] == 1:
        kw = {
            'title_txt': 'Done.',
            'main_txt': 'Successfully stopped pulley.',
            'sub_txt': r['message']
        }
    # failure
    else:
        kw = {
            'title_txt': 'Error.',
            'main_txt': 'Pulley not stopped',
            'sub_txt': r['message']
        }
    return render_template('request-mvmt-result.html', **kw)


##############
# CREATE API #
##############

api_bp = Blueprint('api', __name__)
api = Api(api_bp)
ply = pulley(
        **{'ip': '10.0.0.7',
         'port': 8181,
         'buf_size': 124}
    )


@api.route('/getcurrentloc')
class getcurrentloc(Resource):

    def get(self):
        print(ply.getcurrentloc())
        return 1


@api.route('/requestmovement')
class requestmovement(Resource):

    def post(self):
        # parse request args for destination
        rp = reqparse.RequestParser()
        rp.add_argument('dest', type=int)
        args = rp.parse_args()
        currloc = requests.get('http://127.0.0.1:5000/getcurrentloc').json()
        destloc = args.get('dest')
        if destloc is None:
            destloc = int(not currloc)
        # if pulley is at req loc, don't do anything
        if destloc == currloc:
            return {
                'moving': 0,
                'message': f"Pulley already at {destloc}"
            }
        else:
            ply.requestmovement(destloc)
            return {
                'moving': 1,
                'message': f"Pulley moving to {destloc}"
            }


@api.route('/stopmovement')
class stopmovement(Resource):

    def get(self):
        # TODO: stop pulley
        return {
            'stoppedmovement': 1,
            'message': 'Pulley movement stopped.'
        }
