class Singleton(type):
    def __call__(cls, *args, **kwargs):
        if '_instance_' not in cls.__dict__:
            cls._instance_ = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instance_
