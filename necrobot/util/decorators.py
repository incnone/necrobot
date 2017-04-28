import asyncio


def commits(func):
    def func_wrapper(self, *args, **kwargs):
        func(self, *args, **kwargs)

        if 'commit' not in kwargs or kwargs['commit']:
            asyncio.ensure_future(self.commit())

    return func_wrapper
