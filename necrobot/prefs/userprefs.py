class UserPrefs(object):
    def __init__(self):
        self.daily_alert = None
        self.race_alert = None

    # A list of strings describing preferences set by this object
    @property
    def pref_strings(self):
        pref_str = []
        if self.daily_alert:
            pref_str.append('Get seeds (via PM) when new dailies open.')
        else:
            pref_str.append('No daily PMs.')

        if self.race_alert:
            pref_str.append('Alert (via PM) when a race begins.')
        else:
            pref_str.append('No race alert PMs.')

        return pref_str

    # Overwrite prefs in this object with any non-None prefs in the passed object
    def merge_prefs(self, rhs):
        if rhs.daily_alert is not None:
            self.daily_alert = rhs.daily_alert
        if rhs.race_alert is not None:
            self.race_alert = rhs.race_alert
