## Given a time string, returns the time in total hundredths of a second, or -1 on failure.
## Allowable string formats:
##  [m]m:ss.hh
##  [m]m:ss:hh
##  [m]m:ss
def from_str(time_str):    
    args = time_str.split(':')
    if len(args) == 1: #look for [m]m.ss.hh format
        args = time_str.split('.')
        if len(args) == 3 and len(args[1]) == 2 and len(args[2]) == 2:
            try:
                t_min = int(args[0])
                t_sec = int(args[1])
                t_hun = int(args[2])
                return 6000*t_min + 100*t_sec + t_hun
            except ValueError:
                return -1
    elif len(args) == 2:
        args_2 = args[1].split('.')
        if len(args_2) == 1 and len(args_2[0]) == 2:    #[m]m:ss format
            try:
                t_min = int(args[0])
                t_sec = int(args_2[0])
                return 6000*t_min + 100*t_sec
            except ValueError:
                return -1
        elif len(args_2) == 2 and len(args_2[0]) == 2 and len(args_2[1]) == 2:
            try:
                t_min = int(args[0])
                t_sec = int(args_2[0])
                t_hun = int(args_2[1])
                return 6000*t_min + 100*t_sec + t_hun        
            except ValueError:
                return -1
    elif len(args) == 3 and len(args[1]) == 2 and len(args[2]) == 2:
        try:
            t_min = int(args[0])
            t_sec = int(args[1])
            t_hun = int(args[2])
            return 6000*t_min + 100*t_sec + t_hun
        except ValueError:
            return -1
    return -1

def to_str(time_hund):      #time_hund in total hundredths of second; returns a string in the form [m]:ss.hh
    minutes = time_hund // 6000
    seconds = time_hund // 100 - 60*minutes
    hundredths = time_hund - 100*(seconds + 60*minutes)
    return str(minutes) + ':' + str(seconds).zfill(2) + '.' + str(hundredths).zfill(2)   
