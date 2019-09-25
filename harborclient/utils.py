
import os
import six


def env(*args, **kwargs):
    """Returns the first environment variable set.

    If all are empty, defaults to '' or keyword arg `default`.
    """
    for arg in args:
        value = os.environ.get(arg)
        if value:
            return value
    return kwargs.get('default', '')


def arg(*args, **kwargs):
    """Decorator for CLI args.

    Example:

    >>> @arg("name", help="Name of the new entity")
    ... def entity_create(args):
    ...     pass
    """

    def _decorator(func):
        add_arg(func, *args, **kwargs)
        return func

    return _decorator


def add_arg(func, *args, **kwargs):
    """Bind CLI arguments to a shell.py `do_foo` function."""

    if not hasattr(func, 'arguments'):
        func.arguments = []

    # NOTE(sirp): avoid dups that can occur when the module is shared across
    # tests.
    if (args, kwargs) not in func.arguments:
        # Because of the semantics of decorator composition if we just append
        # to the options list positional options will appear to be backwards.
        func.arguments.insert(0, (args, kwargs))



def get_function_name(func):
    if six.PY2:
        if hasattr(func, "im_class"):
            return "%s.%s" % (func.im_class, func.__name__)
        else:
            return "%s.%s" % (func.__module__, func.__name__)
    else:
        return "%s.%s" % (func.__module__, func.__qualname__)
