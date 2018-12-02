import discord
import asyncio
from discord.ext.commands import Bot
import random
import requests


BOT_PREFIX='!piper '
#Piper token
TOKEN = 'NTE2NzA5OTY3Mjg2NTAxMzc2.Dt3oSA.k2NK-9nu2-jB_QoTyeoajIBXRRc'

#Piper test token
TOKEN = 'NTE2NzIzMjM0NjY2OTcxMTQ2.Dt30Uw.MqF7ofYtE2GiWTBGSg9hjv_9CIQ'


client = Bot(command_prefix=BOT_PREFIX)


@client.command(
    name='vuvuzela',
    description='Plays an awful vuvuzela in the voice channel',
    pass_context=True,
)
async def vuvuzela(context):
    user=context.message.author
    voice_channel=user.voice.voice_channel
    channel=None
    if voice_channel!= None:
        channel=voice_channel.name
        await client.say('User is in channel: '+ channel)
        vc= await client.join_voice_channel(voice_channel)
        player = vc.create_ffmpeg_player('vuvuzela.mp3', after=lambda: print('done'))
        player.start()
        while not player.is_done():
            await asyncio.sleep(1)
        player.stop()
        await vc.disconnect()
    else:
        await client.say('User is not in a channel.')


@client.command(
    name='play',
    description='Plays the audio from a specified youtube link.',
    pass_context=True,
)
async def play(context, url):
    user=context.message.author
    voice_channel = user.voice.voice_channel
    channel = None
    if voice_channel != None:
        vc = await client.join_voice_channel(voice_channel)
        player = await vc.create_ytdl_player(url=url)
        await client.say('User is in channel: '+ voice_channel.name)
        await client.say('Now playing: '+ player.title)
        player.start()
        while not player.is_done():
            await asyncio.sleep(1)
        player.stop()
        await vc.disconnect()
    else:
        await client.say('User is not in a channel.')


@client.command(
    name='roll',
    description='Rolls dice. Format is [Number of dice to be rolled]d[Max value of dice]',
    pass_context=True,
)
async def roll(context, die):
    num_die=die.split('d')[0]
    max_val=die.split('d')[1]
    results=[]
    total=0
    if int(num_die)<=0 or int(max_val)<1:
        await client.say('Stop trying to fuck with my bot Zach')
        return
    for die in range(1, int(num_die)+1):
        x=random.randrange(1, int(max_val)+1)
        results.append(x)
        total+=x
    msg=''
    for result in results:
        msg+=str(result)+' + '
    if msg.endswith(' + '):
        msg=msg[:-3]
    await client.say(msg)
    await client.say('Total is: '+str(total))


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


@client.command(
    name='stop',
    description='Immediately stops whatever audio piper is playing and disconnects piper from the channel',
    pass_context=True
)
async def stop(context):
    voice_clients=client.voice_clients
    user_vc=context.message.author.voice.voice_channel
    vc_disconnect=None
    for vc in voice_clients:
        if vc.channel == user_vc:
            vc_disconnect=vc
    if vc_disconnect != None:
        await vc_disconnect.disconnect()



client.run(TOKEN)