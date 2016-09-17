from functools import wraps
from flask.ext.login import current_user
from flask import abort
from .models import Permission


def permission_required(permission):
    def decorator(func):
        @wraps(func)
        def decorator_func(*args, **kw):
            if not current_user.can(permission):
                abort(403)
            return func(*args, **kw)
        return decorator_func
    return decorator


def admin_required(f):
    return permission_required(Permission.ADMINISTER)(f)
