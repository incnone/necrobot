def commits(func):
    def func_wrapper(self, *args, commit: bool = True, **kwargs):
        func(*args, **kwargs)
        if commit:
            self.commit()

    return func_wrapper
