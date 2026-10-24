from celery import Celery, Task
from flask import Flask


def init_celery(app: Flask) -> Celery:
    """Create Celery and make every task run inside the Flask app context."""

    class FlaskTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_config = dict(app.config["CELERY"])
    if app.testing:
        celery_config.update(task_always_eager=True, task_eager_propagates=True)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(celery_config)
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app
