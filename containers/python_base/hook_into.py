import functools

##### Hook decorator #########

def hook_into(http_method, pre_hook, post_hook, err_hook):
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
