from flask import Flask
from uuid import uuid4
from client import views
from server import auth


# init app
app = Flask(__name__)
app.config['SECRET_KEY'] = uuid4().hex

# register blueprints
app.register_blueprint(views.views_bp)
app.register_blueprint(views.api_bp)
app.register_blueprint(auth.auth_bp)

if __name__ == '__main__':
    # startup
    app.run(debug=True)
