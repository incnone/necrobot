import clparse

class UserPrefs(object): 
    def get_default():
        prefs = UserPrefs()
        prefs.hide_spoilerchat = False
        prefs.deliver_seed = False
        return prefs

    def __init__(self):
        self.hide_spoilerchat = None
        self.deliver_seed = None

    def modify_with(self, user_prefs):
        if user_prefs.hide_spoilerchat != None:
            self.hide_spoilerchat = user_prefs.hide_spoilerchat
        if user_prefs.deliver_seed != None:
            self.deliver_seed = user_prefs.deliver_seed

    @property
    def contains_info(self):
        return self.hide_spoilerchat != None or self.deliver_seed != None

    # A list of strings describing preferences set by this object
    @property
    def pref_strings(self):
        pref_str = []
        if self.hide_spoilerchat == False:
            pref_str.append('Show daily spoiler chat at all times.')
        elif self.hide_spoilerchat == True:
            pref_str.append('Hide daily spoiler chat until after submission.')

        if self.deliver_seed == False:
            pref_str.append('Do not deliver the daily seed via PM.')
        elif self.deliver_seed == True:
            pref_str.append('Deliver the daily seed via PM.')
        return pref_str

def _parse_show_spoilerchat(args, user_prefs):
    command_list = ['spoilerchat']
    if len(args) >= 2 and args[0] in command_list:
        if args[1] == 'hide':
            user_prefs.hide_spoilerchat = True
        elif args[1] == 'show':
            user_prefs.hide_spoilerchat = False         

def _parse_deliver_seed(args, user_prefs):
    command_list = ['deliverseed']
    if len(args) >= 2 and args[0] in command_list:
        if args[1] == 'true':
            user_prefs.deliver_seed = True
        elif args[1] == 'false':
            user_prefs.deliver_seed = False   

def parse_args(args):
    #user_prefs is a list of preferences we should change
    user_prefs = UserPrefs()

    while args:
        next_cmd_args = clparse.pop_command(args)
        if not next_cmd_args:
            next_cmd_args.append(args[0])
            args.pop(0)

        #Parse each possible command
        _parse_show_spoilerchat(next_cmd_args, user_prefs)
        _parse_deliver_seed(next_cmd_args, user_prefs)
    #end while

    return user_prefs

class UserPrefManager(object):
    def __init__(self, db_connection, server):
        self._db_conn = db_connection
        self._server = server

    def set_prefs(self, user_prefs, user):
        prefs = self.get_prefs(user)
        prefs.modify_with(user_prefs)

        db_cursor = self._db_conn.cursor()
        params = (user.id, prefs.hide_spoilerchat, prefs.deliver_seed,)
        db_cursor.execute("""INSERT INTO user_prefs VALUES (?,?,?)""", params)         
        self._db_conn.commit()

    def get_prefs(self, user):
        user_prefs = UserPrefs.get_default()
        db_cursor = self._db_conn.cursor()
        params = (user.id,)
        db_cursor.execute("""SELECT * FROM user_prefs WHERE playerid=?""", params)
        for row in db_cursor:
            user_prefs.hide_spoilerchat = row[1]
            user_prefs.deliver_seed = row[2]
        return user_prefs

    #get all user id's matching the given user prefs
    def get_all_matching(self, user_prefs):
        users_matching_spoilerchat = []
        users_matching_deliverseed = []
        lists_to_use = []
        db_cursor = self._db_conn.cursor()

        if user_prefs.hide_spoilerchat != None:
            lists_to_use.append(users_matching_spoilerchat)
            params = (user_prefs.hide_spoilerchat,)
            db_cursor.execute("""SELECT playerid FROM user_prefs WHERE hidespoilerchat=?""", params)
            for row in db_cursor:
                userid = row[0]
                for member in self._server.members:
                    if int(member.id) == int(userid):
                        users_matching_spoilerchat.append(member)

        if user_prefs.deliver_seed != None:
            lists_to_use.append(users_matching_deliverseed)
            params = (user_prefs.deliver_seed,)
            db_cursor.execute("""SELECT playerid FROM user_prefs WHERE deliverseed=?""", params)
            for row in db_cursor:
                userid = row[0]
                for member in self._server.members:
                    if int(member.id) == int(userid):
                        users_matching_deliverseed.append(member)

        users_matching = []
        if lists_to_use:
            for member in lists_to_use[0]:
                in_intersection = True
                for l in lists_to_use:
                    if not member in l:
                        in_interesection = False
                if in_intersection:
                    users_matching.append(member)
        return users_matching
