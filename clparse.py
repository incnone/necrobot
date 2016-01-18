## "args" should be a list of strings like [-command1, arg1, arg2, -command2, -command3, arg3, ...];
## this command returns the list [command1, arg1, arg2] and pops those three elements from the front of the list.
## if the list does not start with a -command, this returns an empty list and pops nothing
## Notes: strips all '-' characters from the command, so --command is also fine
def pop_command(args):
    list_to_return = []
    if args:
        if args[0].startswith('-'):
            list_to_return.append(args[0].lstrip('-'))
            args.pop(0)
            while args and not args[0].startswith('-'):
                list_to_return.append(args[0].rstrip('\n'))
                args.pop(0)
    return list_to_return

def next_command(args):
    if args and args[0].startswith('-'):
        return args[0].lstrip('-')
    else:
        return None

## sweeps through args, and for each command in args that is also in the command
## list, returns a list [command, args...]. (Thus this method returns a list of lists.)
## these commands and their arguments are removed from args
def pop_commands_from_list(args, cmd_list):
    list_to_return = []
    while True:
        list_next_command = pop_command_from_list(args, cmd_list)
        if not list_next_command:
            return list_to_return
        else:
            list_to_return.append(list_next_command)

def pop_command_from_list(args, cmd_list):
    arg_indicies_to_pop = []
    list_to_return = []
    found_command = False
    for i, arg in enumerate(args):
        if arg.startswith('-'): #this is a command
            if found_command:
                break #for
            else:
                command = arg.lstrip('-')
                if command in cmd_list:
                    list_to_return.append(command)
                    arg_indicies_to_pop.append(i)
                    found_command = True
        elif found_command:
            arg_indicies_to_pop.append(i)
            list_to_return.append(arg)

    for i in reversed(arg_indicies_to_pop):
        del args[i]

    return list_to_return
    
