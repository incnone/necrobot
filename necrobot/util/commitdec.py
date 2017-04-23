def commits(func):
    def func_wrapper(self, *args, **kwargs):
        func(self, *args, **kwargs)

        if 'commit' not in kwargs or kwargs['commit']:
            self.commit()

    return func_wrapper
