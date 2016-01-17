## Holds permission data for a private race room

import discord
from raceprivateinfo import RacePrivateInfo

def get_permission_info(server, race_private_info):
    permission_info = PermissionInfo()
    for admin_name in race_private_info.admin_names:
        for role in server.roles:
            if role.name == admin_name:
                permission_info.admin_roles.append(role)
        for member in server.members:
            if member.name == admin_name:
                permission_info.admins.append(member)

    for racer_name in race_private_info.racer_names:
        for member in server.members:
            if member.name == racer_name:
                permission_info.racers.append(member)

    return permission_info
        
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
