import codecs
import os
import discord

from necrobot.config import Config


async def write_channel(channel: discord.TextChannel, outfile_name: str):
    try:
        messages = []
        async for message in channel.history(limit=5000):
            messages.insert(0, message)

        outfile_name = outfile_name.encode('utf-8').decode('ascii', 'replace')
        pathname = os.path.join(Config.LOG_DIRECTORY, '{0}.log'.format(outfile_name))
        with codecs.open(pathname, 'w', 'utf-8') as outfile:
            for message in messages:
                try:
                    outfile.write('{1} ({0}): {2}\n'.format(
                        message.created_at.strftime("%m/%d %H:%M:%S"), message.author.name, message.clean_content))
                except UnicodeEncodeError:
                    try:
                        outfile.write('{1} ({0}): {2}\n'.format(
                            message.created_at.strftime("%m/%d %H:%M:%S"), message.author.name, message.content))
                    except UnicodeEncodeError:
                        pass
    except UnicodeEncodeError:
        pass
