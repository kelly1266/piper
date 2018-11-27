import discord
import asyncio


#Piper token
TOKEN = 'NTE2NzA5OTY3Mjg2NTAxMzc2.Dt3oSA.k2NK-9nu2-jB_QoTyeoajIBXRRc'

#Piper test token
#TOKEN = 'NTE2NzIzMjM0NjY2OTcxMTQ2.Dt30Uw.MqF7ofYtE2GiWTBGSg9hjv_9CIQ'

client = discord.Client()

@client.event
async def on_message(message):
    message.content=message.content.lower()
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    if message.content == '!piper':
        msg = 'Hello, my name is Piper. Type "!piper-help" to see more options.'
        await client.send_message(message.channel, msg)

    if '!piper' in str(message.content):
        message_tokens=tokenize(str(message.content))
        if len(message_tokens)>=2:
            if message_tokens[1] == 'vuvuzela':
                user=message.author
                voice_channel=user.voice.voice_channel
                channel='None'
                if voice_channel != None:
                    channel=voice_channel.name
                    msg = 'User is in channel: ' + channel
                    await client.send_message(message.channel, msg)
                    vc = await client.join_voice_channel(voice_channel)
                    player=vc.create_ffmpeg_player('vuvuzela.mp3', after=lambda: print('done'))
                    player.start()
                    while not player.is_done():
                        await asyncio.sleep(1)
                    player.stop()
                    await vc.disconnect()
                else:
                    msg='User is not in a channel.'
                    await client.send_message(message.channel, msg)


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


def tokenize(commands):
    message_tokens=commands.split('-')
    return message_tokens


client.run(TOKEN)
