import asyncio


def async_test(loop):
    def real_decorator(f):
        def func_wrapper(*args, **kwargs):
            coro = asyncio.coroutine(f)
            future = coro(*args, **kwargs)
            loop.run_until_complete(future)
        return func_wrapper
    return real_decorator
