import calendar


# TODO: Return a datetime; throw appropriate exceptions
def parse_datetime(args):
    if not len(args) == 3:
        return None

    parsed_args = []

    month_name = args[0].capitalize()
    cmd_len = len(month_name)
    month_found = False
    if cmd_len >= 3:
        for actual_month in calendar.month_name:
            if actual_month[:cmd_len] == month_name:
                month_found = True
                parsed_args.append(list(calendar.month_name).index(actual_month))
                break

    if not month_found:
        parsed_args.append(None)

    try:
        parsed_args.append(int(args[1]))
    except ValueError:
        parsed_args.append(None)

    time_args = args[2].split(':')
    if len(time_args) == 1:
        try:
            time_hr = int(time_args[0].rstrip('apm'))
            if (time_args[0].endswith('p') or time_args[0].endswith('pm')) and not time_hr == 12:
                time_hr += 12
            elif (time_args[0].endswith('a') or time_args[0].endswith('am')) and time_hr == 12:
                time_hr = 0

            parsed_args.append(int(0))
            parsed_args.append(time_hr)
        except ValueError:
            parsed_args.append(None)
            parsed_args.append(None)

    elif len(time_args) == 2:
        try:
            time_min = int(time_args[1].rstrip('apm'))
            parsed_args.append(time_min)
        except ValueError:
            parsed_args.append(None)

        try:
            time_hr = int(time_args[0])
            if (time_args[1].endswith('p') or time_args[1].endswith('pm')) and not time_hr == 12:
                time_hr += 12
            elif (time_args[1].endswith('a') or time_args[1].endswith('am')) and time_hr == 12:
                time_hr = 0

            parsed_args.append(time_hr)
        except ValueError:
            parsed_args.append(None)

    else:
        parsed_args.append(None)
        parsed_args.append(None)
        return parsed_args

    return parsed_args
