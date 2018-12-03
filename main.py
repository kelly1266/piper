import discord
import asyncio
from discord.ext.commands import Bot
import random
import requests

BOT_PREFIX='!piper '
TOKEN=''
with open('TOKEN_FILE.txt', 'r') as myfile:
    TOKEN=myfile.read()

client = Bot(command_prefix=BOT_PREFIX)
STREAM_PLAYER=None
VOLUME_HAS_CHANGED=False
STREAM_PLAYER_VOLUME=1

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
    global VOLUME_HAS_CHANGED
    global STREAM_PLAYER_VOLUME
    global STREAM_PLAYER
    user=context.message.author
    voice_channel = user.voice.voice_channel
    channel = None
    if voice_channel != None:
        vc = await client.join_voice_channel(voice_channel)
        player = await vc.create_ytdl_player(url=url)
        STREAM_PLAYER = player
        await client.say('User is in channel: '+ voice_channel.name)
        await client.say('Now playing: '+ player.title)
        player.start()
        while not player.is_done():
            if VOLUME_HAS_CHANGED:
                player.volume=STREAM_PLAYER_VOLUME
                VOLUME_HAS_CHANGED=False
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
    global STREAM_PLAYER
    voice_clients=client.voice_clients
    user_vc=context.message.author.voice.voice_channel
    vc_disconnect=None
    for vc in voice_clients:
        if vc.channel == user_vc:
            vc_disconnect=vc
    if vc_disconnect != None:
        await vc_disconnect.disconnect()
    STREAM_PLAYER=None


@client.command(
    name='volume',
    description='Change the volume that Piper is playing the current song at.',
    pass_context=True,
)
async def volume(context, vol):
    if STREAM_PLAYER != None:
        global STREAM_PLAYER_VOLUME
        global VOLUME_HAS_CHANGED
        STREAM_PLAYER_VOLUME=int(vol)/100
        VOLUME_HAS_CHANGED=True


@client.command(
    name='pause',
    description='Pauses Piper\'s audio stream.',
    pass_context=True,
)
async def pause(context):
    global STREAM_PLAYER
    if STREAM_PLAYER != None:
        if STREAM_PLAYER.is_playing():
            STREAM_PLAYER.pause()
            await client.say('Piper has been paused.')
        else:
            STREAM_PLAYER.resume()
            await client.say('Piper has been resumed.')
    else:
        await client.say('Piper does not currently have an audio stream playing.')


client.run(TOKEN)

#new and improved discord bot