from necrobot import logon, loader


if __name__ == "__main__":
    logon.logon(
        config_filename='data/condorbot_config',
        load_config_fn=loader.load_condorbot_config
    )
