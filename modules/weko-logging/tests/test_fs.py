# -*- coding: utf-8 -*-

"""File system logging tests."""


import logging
import os
from logging.handlers import TimedRotatingFileHandler
from os.path import exists, join

import pytest
from flask import Flask

from weko_logging.config import WEKO_LOGGING_FS_LEVEL
from weko_logging.fs import WekoLoggingFS


def test_init(tmppath):
    """
    Test extension initialization.

    :param tmppath: Temp path object.
    """
    app = Flask("testapp")
    WekoLoggingFS(app)
    assert "weko-logging-fs" in app.extensions

    ext = WekoLoggingFS()
    app = Flask("testapp")
    assert "weko-logging-fs" not in app.extensions
    ext.init_app(app)
    assert "weko-logging-fs" in app.extensions

    logfile = join(tmppath, "test.log")
    app = Flask("testapp")
    app.config.update(dict(WEKO_LOGGING_FS_LOGFILE=logfile))
    WekoLoggingFS(app)
    assert "weko-logging-fs" in app.extensions
    assert app.config["WEKO_LOGGING_FS_LEVEL"] == WEKO_LOGGING_FS_LEVEL

    app = Flask("testapp")
    app.config.update(
        dict(WEKO_LOGGING_FS_PYWARNINGS=None, WEKO_LOGGING_FS_LOGFILE=logfile)
    )
    ext = WekoLoggingFS(app)
    assert "weko-logging-fs" in app.extensions
    logger = logging.getLogger("py.warnings")
    assert TimedRotatingFileHandler not in [x.__class__ for x in logger.handlers]

    app = Flask("testapp")
    app.config.update(
        dict(WEKO_LOGGING_FS_PYWARNINGS=True, WEKO_LOGGING_FS_LOGFILE=logfile)
    )
    ext = WekoLoggingFS(app)
    assert "weko-logging-fs" in app.extensions
    logger = logging.getLogger("py.warnings")
    assert TimedRotatingFileHandler in [x.__class__ for x in logger.handlers]

    app = Flask("testapp")
    app.config.update(dict(WEKO_LOGGING_FS_LOGFILE=None))
    WekoLoggingFS(app)
    assert "weko-logging-fs" not in app.extensions
    assert app.config["WEKO_LOGGING_FS_LEVEL"] == WEKO_LOGGING_FS_LEVEL

    app = Flask("testapp")
    os.environ["LOGGING_FS_LOGFILE"] = logfile
    WekoLoggingFS(app)
    assert "weko-logging-fs" in app.extensions
    assert app.config["WEKO_LOGGING_FS_LEVEL"] == WEKO_LOGGING_FS_LEVEL
    assert app.config["WEKO_LOGGING_FS_LOGFILE"] == logfile
    os.environ.pop("LOGGING_FS_LOGFILE")


def test_filepath_formatting(tmppath):
    """
    Test extension initialization.

    :param tmppath: Temp path object.
    """
    app = Flask("testapp", instance_path=tmppath)
    filepath = tmppath + "/testapp.log"
    app.config.update(dict(DEBUG=True, WEKO_LOGGING_FS_LOGFILE=filepath))
    WekoLoggingFS(app)
    assert app.config["WEKO_LOGGING_FS_LOGFILE"] == filepath
    assert app.config["WEKO_LOGGING_FS_LEVEL"] == "DEBUG"


def test_missing_dir(tmppath):
    """
    Test missing dir.

    :param tmppath: Temp path object.
    """
    app = Flask("testapp")
    filepath = join(tmppath, "invaliddir/test.log")
    app.config.update(dict(WEKO_LOGGING_FS_LOGFILE=filepath))
    assert pytest.raises(ValueError, WekoLoggingFS, app)


def test_warnings(tmppath, pywarnlogger):
    """
    Test extension initialization.

    :param tmppath: Temp path object.
    :param pywarnlogger: Py warn logger object.
    """
    app = Flask("testapp", instance_path=tmppath)
    app.config.update(
        dict(
            WEKO_LOGGING_FS_LOGFILE=tmppath + "/testapp.log",
            WEKO_LOGGING_FS_PYWARNINGS=True,
            WEKO_LOGGING_FS_LEVEL="WARNING",
        )
    )
    WekoLoggingFS(app)
    assert TimedRotatingFileHandler in [x.__class__ for x in pywarnlogger.handlers]


def test_logging(tmppath):
    """
    Test extension initialization.

    :param tmppath: Temp path object.
    """
    filepath = join(tmppath, "test.log")
    app = Flask("testapp")
    app.config.update(
        dict(WEKO_LOGGING_FS_LOGFILE=filepath, WEKO_LOGGING_FS_LEVEL="WARNING")
    )
    WekoLoggingFS(app)
    # Test delay opening of file
    app.logger.warning("My warning")

    assert exists(filepath)
    app.logger.info("My info")
    # Test log level
    with open(filepath) as fp:
        content = fp.read()
    assert "My warning" in content
    assert "My info" not in content
