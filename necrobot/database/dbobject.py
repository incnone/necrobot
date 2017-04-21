"""
Base class for objects represented in the database.
"""


class DBObject(object):
    def checkout(self, *args, **kwargs):
        pass

    def commit(self):
        pass