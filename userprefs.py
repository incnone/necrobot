import clparse

class UserPrefs(object): 
    def get_default():
        prefs = UserPrefs()
        prefs.show_spoilerchat = True
        return prefs

    def __init__(self):
        self.show_spoilerchat = None

    def modify_with(self, user_prefs):
        if user_prefs.show_spoilerchat != None:
            self.show_spoilerchat = user_prefs.show_spoilerchat

    @property
    def contains_info(self):
        return self.show_spoilerchat != None

    # A list of strings describing preferences set by this object
    @property
    def pref_strings(self):
        pref_str = []
        if self.show_spoilerchat == True:
            pref_str.append('Show daily spoiler chat at all times.')
        elif self.show_spoilerchat == False:
            pref_str.append('Hide daily spoiler chat until after submission.')
        return pref_str

def _parse_show_spoilerchat(args, user_prefs):
    command_list = ['spoilerchat']
    if len(args) >= 2 and args[0] in command_list:
        if args[1] == 'hide':
            user_prefs.show_spoilerchat = False
        elif args[1] == 'show':
            user_prefs.show_spoilerchat = True         

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
    #end while

    return user_prefs

class UserPrefManager(object):
    def __init__(self, db_connection):
        self._db_conn = db_connection 

    def set_prefs(self, user_prefs, user):
        prefs = self.get_prefs(user)
        prefs.modify_with(user_prefs)

        db_cursor = self._db_conn.cursor()
        params = (user.id, prefs.show_spoilerchat,)
        db_cursor.execute("""INSERT INTO user_prefs VALUES (?,?)""", params)         
        self._db_conn.commit()

    def get_prefs(self, user):
        user_prefs = UserPrefs.get_default()
        db_cursor = self._db_conn.cursor()
        params = (user.id,)
        db_cursor.execute("""SELECT * FROM user_prefs WHERE playerid=?""", params)
        for row in db_cursor:
            user_prefs.show_spoilerchat = row[1]
        return user_prefs
