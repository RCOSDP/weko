import os
from flask import Blueprint, current_app, flash, render_template, \
    render_template_string
from flask_plugins import Plugin, connect_event

__plugin__ = "HelloPlugin"
__version__ = "1.0.0"


def hello_world():
    flash("Hello Plugin from {} Plugin".format(__plugin__), "success")


def hello_world2():
    flash("Hello Plugin 2 from {} Plugin".format(__plugin__), "success")


def inject_hello_world():
    return "<h1>Hello Plugin Injected</h1>"


def inject_hello_world2():
    return "<h1>Hello Plugin 2 Injected</h1>"


def inject_navigation_link():
    return render_template_string(
        """
            <li><a href="{{ url_for('helloplugin.index') }}">HelloPlugin</a></li>
        """)


hello = Blueprint("helloplugin", __name__, template_folder="templates")


@hello.route("/")
def index():
    return render_template("hello.html", plugin_name='hello_plugin')


class HelloPlugin(Plugin):

    def setup(self):
        self.register_blueprint(hello, url_prefix="/plugin/hello")

        connect_event("after_navigation", hello_world)
        connect_event("after_navigation", hello_world2)

        connect_event("tmpl_before_content", inject_hello_world)
        connect_event("tmpl_before_content", inject_hello_world2)

        connect_event("tmpl_navigation_last", inject_navigation_link)

    def register_blueprint(self, blueprint, **kwargs):
        """Registers a blueprint."""
        current_app.register_blueprint(blueprint, **kwargs)

    def delete(self):
        """Delete plugin.

        The app usually has to be restarted after this action because
        plugins _can_ register blueprints and in order to "unregister" them,
        the application object has to be destroyed.
        This is a limitation of Flask and if you want to know more about this
        visit this link: http://flask.pocoo.org/docs/1.0/blueprints/
        """
        disabled_file = os.path.join(self.path, "DELETED")
        try:
            open(disabled_file, "a").close()
            self.enabled = False
        except:
            raise
        return self.enabled
