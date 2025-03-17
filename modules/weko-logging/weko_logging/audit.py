import logging
from os.path import dirname, exists

from weko_logging.handler import AuditLogHandler

from .ext import WekoLoggingBase


class WekoLoggingAudit(WekoLoggingBase):
    """WEKO-Logging extension. Filesystem handler."""

    def init_app(self, app):
        """
        Flask application initialization.

        :param app: The flask application.
        """
        self.install_handler(app)
        app.extensions["weko-logging-fs"] = self

    def install_handler(self, app):
        """
        Install log handler on Flask application.

        :param app: The flask application.
        """
        basedir = dirname(app.config["WEKO_LOGGING_FS_LOGFILE"])
        if not exists(basedir):
            raise ValueError("Log directory {0} does not exist.".format(basedir))

        handler = AuditLogHandler()

        handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] - %(levelname)s - %(filename)s - %(name)s - %(funcName)s - %(message)s "
                "[in %(pathname)s:%(lineno)d]"
            )
        )
        # Add handler to application logger
        app.logger.addHandler(handler)
