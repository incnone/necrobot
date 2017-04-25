from necrobot.util import logon, loader


if __name__ == "__main__":
    logon.logon(
        config_filename='data/necrobot_config',
        load_config_fn=loader.load_necrobot_config
    )

