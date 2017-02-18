from .userprefs import UserPrefs
from ..necrodb import NecroDB


class PrefsManager(object):
    def __init__(self, necrobot):
        self.necrobot = necrobot

    def close(self):
        pass

    def set_prefs(self, user_prefs, user):
        prefs = self.get_prefs(user)
        prefs.merge_prefs(user_prefs)

        params = (int(user.id), False, 2 if prefs.daily_alert else 0, 1 if prefs.race_alert else 0,)
        print(params)
        NecroDB().set_prefs(params)

    @staticmethod
    def get_prefs(user):
        user_prefs = UserPrefs()
        params = (int(user.id),)
        for row in NecroDB().get_prefs(params):
            user_prefs.daily_alert = (row[2] != 0)
            user_prefs.race_alert = (row[3] != 0)
        return user_prefs

    # get all user id's matching the given user prefs
    def get_all_matching(self, user_prefs):
        users_matching_dailyalert = []
        users_matching_racealert = []
        lists_to_use = []

        if user_prefs.daily_alert is not None:
            lists_to_use.append(users_matching_dailyalert)
            params = (2,) if user_prefs.daily_alert else (0,)

            for row in NecroDB().get_all_matching_prefs("dailyalert", params):
                userid = row[0]
                for member in self.necrobot.server.members:
                    if int(member.id) == int(userid):
                        users_matching_dailyalert.append(member)

        if user_prefs.race_alert is not None:
            lists_to_use.append(users_matching_racealert)
            params = (1,) if user_prefs.race_alert else (0,)

            for row in NecroDB().get_all_matching_prefs("racealert", params):
                userid = row[0]
                for member in self.necrobot.server.members:
                    if int(member.id) == int(userid):
                        users_matching_racealert.append(member)

        users_matching = []
        if lists_to_use:
            for member in lists_to_use[0]:
                in_intersection = True
                for l in lists_to_use:
                    if member not in l:
                        in_intersection = False
                if in_intersection:
                    users_matching.append(member)

        return users_matching
