import asyncio


def async_test(f):
    def func_wrapper(*args, **kwargs):
        coro = asyncio.coroutine(f)
        future = coro(*args, **kwargs)
        asyncio.get_event_loop().run_until_complete(future)
    return func_wrapper
