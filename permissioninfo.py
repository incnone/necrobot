## Holds permission data for a private race room

class PermissionInfo(object):
    admins = []
    admin_roles = []
    racers = []

    def is_admin(self, member):
        for role in member.roles:
            if role in self.admin_roles:
                return True
        if member in admins:
            return True

        return False
