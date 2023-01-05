import functools

##### Hook decorator #########

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
            pre_hook(http_method, func.__name__, *args, **kwargs)
            # try to execute function
            try:
                value = await func(*args, **kwargs)
                # Do something after
                post_hook(http_method, func.__name__, *args, **kwargs)
                # return the result
                return value
            # in case of errors
            except Exception as e:
                # run the error hooks
                err_hook(http_method, func.__name__, e, *args, **kwargs)
                raise e
        return hooks_wrapper
    return hooks_decorator
