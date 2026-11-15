from flask import Flask
from flask_cors import CORS

from server import auth, payouts

app = Flask(__name__)
CORS(app, origins="*")
app.register_blueprint(auth.bp)
app.register_blueprint(payouts.bp)
