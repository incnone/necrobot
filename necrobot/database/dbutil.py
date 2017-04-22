import discord
from necrobot.database.dbconnect import DBConnect


def register_discord_user(user: discord.User):
    params = (user.id, user.display_name,)
    with DBConnect(commit=True) as cursor:
        cursor.execute(
            "INSERT INTO user_data "
            "(discord_id, discord_name) "
            "VALUES (%s, %s) "
            "ON DUPLICATE KEY UPDATE "
            "discord_name = VALUES(discord_name)",
            params
        )
