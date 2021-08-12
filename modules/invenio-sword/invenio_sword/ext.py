from . import config
from . import views


class InvenioSword(object):
    def __init__(self, app=None):
        if app:
            self.init_config(app)
            self.init_app(app)

    def init_config(self, app):
        for k in dir(config):
            if k.startswith("SWORD_"):
                app.config.setdefault(k, getattr(config, k))

    def init_app(self, app):
        app.register_blueprint(views.create_blueprint(app.config))
