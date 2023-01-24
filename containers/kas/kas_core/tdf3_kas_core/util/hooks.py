import functools

##### Hook decorator #########

def stub_pre(function_name, *args, **kwargs):
    # STUB
    pass

def stub_post(function_name, value, *args, **kwargs):
    # STUB
    pass

def stub_err(function_name, err, *args, **kwargs):
    # STUB
    pass

def post_rewrap_v2_hook_default(function_name, value, *args, **kwargs):
    res, _, _ = value
    return res

def hook_into(pre=stub_pre, post=stub_post, err=stub_err):
    def hooks_decorator(func):
        @functools.wraps(func)
        def hooks_wrapper(*args, **kwargs):
            # Do something before
            pre(func.__name__, *args, **kwargs)
            # try to execute function
            try:
                value = func(*args, **kwargs)
                # Do something after
                post_value = post(func.__name__, value, *args, **kwargs)
                # return the result
                if post_value:
                    return post_value
                return value
            # in case of errors
            except Exception as e:
                # run the error hooks
                err(func.__name__, e, *args, **kwargs)
                raise e
        return hooks_wrapper
    return hooks_decorator
