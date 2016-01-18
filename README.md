# Necrobot v 0.3

A Discord bot intended for managing a server dedicated to various Necrodancer racing activities. **This project is very
much in alpha.**

## Installation

This is built on Rapptz's [discord.py](https://github.com/Rapptz/discord.py/tree/async/discord) wrapper, v 0.10.0,
for the Discord API; it uses Python's asyncio module, and so requires Python 3.4 or later.

Running the bot requires supplying a file 'data/login_info' with login info for the Discord account 
that the bot is to use. This file is four lines of plaintext:

```
login_email@email.com
login_password
admin_discord_user_id
server_discord_id
```

Here `login_email@email.com` and `login_password` are the Discord account's login credentials. `admin_discord_user_id` 
is the Discord user id of an admin account (this currently just allows this user to use a logout command, .die). 
This may be set to 0 to have no admin. `server_discord_id` is the Discord id of the server the bot is intended to manage. 
This server should already exist on Discord and the bot account should have full permissions to manage the server.

## Brief code summary

The bot is run through `main.py`. This logs into the Discord server, sets up the databases, and runs the client. The
major workhorses are `necrobot.py`, which handles commands in the primary channel; `daily.py`, which manages things related
to the daily speedrun; and `race.py`, which manages a single custom race channel (such channels are created with the `.make`
command in the main channel).

## Requirements

* Python 3.4+
* `discord.py` library, v 0.10.0 [(here)](https://github.com/Rapptz/discord.py/tree/async/discord) 

## License

Provided under the MIT License.



