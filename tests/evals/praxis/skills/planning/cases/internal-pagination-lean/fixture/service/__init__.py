from flask import Flask


def create_app():
    from service.orders import bp

    app = Flask(__name__)
    app.register_blueprint(bp)
    return app
