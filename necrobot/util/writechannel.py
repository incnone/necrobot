import codecs
import os

from necrobot.config import Config


async def write_channel(client, channel, outfile_name):
    messages = []
    async for message in client.logs_from(channel, 5000):
        messages.insert(0, message)

    outfile_name = outfile_name.encode('utf-8').decode('ascii', 'replace')
    pathname = os.path.join(Config.LOG_DIRECTORY, '{0}.log'.format(outfile_name))
    outfile = codecs.open(pathname, 'w', 'utf-8')
    for message in messages:
        try:
            outfile.write('{1} ({0}): {2}\n'.format(
                message.timestamp.strftime("%m/%d %H:%M:%S"), message.author.name, message.clean_content))
        except UnicodeEncodeError:
            try:
                outfile.write('{1} ({0}): {2}\n'.format(
                    message.timestamp.strftime("%m/%d %H:%M:%S"), message.author.name, message.content))
            except UnicodeEncodeError:
                pass

    outfile.close()
