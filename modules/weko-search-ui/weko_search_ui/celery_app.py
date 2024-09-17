import sys
import os
from flask import Flask
from celery import Celery

# sys.path に /code/modules を追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../weko-search-ui/weko_search_ui')))

def create_flask_app():
    app = Flask(__name__)
    app.config.from_object('config')
    return app

def create_celery_app(flask_app=None):
    if flask_app is None:
        flask_app = create_flask_app()

    celery_app = Celery(
        flask_app.import_name,
        broker=flask_app.config['CELERY_BROKER_URL'],
        backend=flask_app.config['CELERY_RESULT_BACKEND']
    )
    celery_app.conf.update(flask_app.config)

    class ContextTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = ContextTask

    # デバッグ用に control 属性の確認
    if hasattr(celery_app, 'control'):
        print("Celery app initialized with control")
    else:
        print("Celery app does not have control")

    return celery_app

celery_app = create_celery_app()
