import discord
import discord.http
from necrobot.botbase import server


async def set_channel_category(channel: discord.Channel, category: discord.Channel):
    await server.client.http.request(
        discord.http.Route('PATCH', '/channels/{channel_id}', channel_id=channel.id),
        json={'parent_id': category.id}
    )
