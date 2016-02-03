import command

class CadenceSpeed(object):
    class __CadenceSpeed(object):
        def __init__(self):
            self.name = 'CadenceSpeed'
            self.id = 0

        def character(self, daily_number):
            return 'Cadence'

        def leaderboard_header(self, daily_number):
            return 'Cadence Speedrun Daily'            

    instance = None
    def __init__(self):
        if not CadenceSpeed.instance:
            CadenceSpeed.instance = CadenceSpeed.__CadenceSpeed()
    def __getattr__(self, name):
        return getattr(self.instance, name)
    def __eq__(self, other):
        return self.instance == other.instance
    
class RotatingSpeed(object):
    class __RotatingSpeed(object):
        def __init__(self):
            self.name = 'RotatingSpeed'
            self.id = 1
            self.rotating_chars = ['Eli', 'Bolt', 'Dove', 'Aria', 'Bard', 'Dorian', 'Coda', 'Melody', 'Monk']

        def character(self, daily_number):
            return self.rotating_chars[daily_number % 9]           

        def leaderboard_header(self, daily_number):
            return 'Rotating Speedrun Daily ({})'.format(self.character(daily_number))

        def days_until(self, char_name, today_number):
            for i,name in enumerate(self.rotating_chars):
                if name == char_name.capitalize():
                    return (i - today_number) % 9
            return None

    instance = None
    def __init__(self):
        if not RotatingSpeed.instance:
            RotatingSpeed.instance = RotatingSpeed.__RotatingSpeed()
    def __getattr__(self, name):
        return getattr(self.instance, name)
    def __eq__(self, other):
        return self.instance == other.instance
    
class CalledType(object):
    def __init__(self, daily_type, daily_number, explicit_char=True, for_previous=False):
        self.type = daily_type
        self.number = daily_number
        self.explicit_char = explicit_char
        self.for_previous = for_previous

    @property
    def character(self):
        return self.type.character(self.number)

#--------------------------------------

def _parse_dailytype_arg(arg):
    sarg = arg.lstrip('-').lower()
    if sarg == 'cadence':
        return 'cadence'
    elif sarg == 'rot' or sarg == 'rotating':
        return 'rotating'
    else:
        return None

def parse_out_type(command, daily_number):
    arg_to_cull = None
    parsed_args = []
    for i,arg in enumerate(command.args):
        parg = _parse_dailytype_arg(arg)
        if parg:
            arg_to_cull = i
            parsed_args.append(parg)

    if not parsed_args:
        return CalledType(CadenceSpeed(), daily_number, explicit_char=False)
    elif len(parsed_args) == 1:
        del command.args[arg_to_cull]
        parg = parsed_args[0]
        if parg == 'cadence':
            return CalledType(CadenceSpeed(), daily_number, explicit_char=True)
        elif parg == 'rotating':
            return CalledType(RotatingSpeed(), daily_number, explicit_char=False)
    else:
        return None
