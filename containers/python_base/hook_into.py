import functools
from enum import Enum

##### Hook decorator #########

class HttpMethod(Enum):
    GET = 4
    POST = 5
    PUT = 6
    PATCH = 7
    DELETE = 8

def stub_pre(http_method, function_name, *args, **kwargs):
    # STUB
    pass

def stub_post(http_method, function_name, *args, **kwargs):
    # STUB
    pass

def stub_err(http_method, function_name, *args, **kwargs):
    # STUB
    pass

def hook_into(context=None, *, pre=stub_pre, post=stub_post, err=stub_err):
    def hooks_decorator(func):
        @functools.wraps(func)
        async def hooks_wrapper(*args, **kwargs):
            # Do something before
            pre(context, func.__name__, *args, **kwargs)
            # try to execute function
            try:
                value = await func(*args, **kwargs)
                # Do something after
                post(context, func.__name__, *args, **kwargs)
                # return the result
                return value
            # in case of errors
            except Exception as e:
                # run the error hooks
                err(context, func.__name__, e, *args, **kwargs)
                raise e
        return hooks_wrapper
    return hooks_decorator
