import discord
import asyncio
from discord.ext.commands import Bot
import random
import requests
import urllib.request
import urllib.parse
import re
from yahoo_fin.stock_info import *
import requests
from PyDictionary import PyDictionary
import enchant


BOT_PREFIX='!piper '
#grab the token from a seperate txt file
TOKEN=''
with open('TOKEN_FILE.txt', 'r') as myfile:
    TOKEN=myfile.read()

#set global variables
client = Bot(command_prefix=BOT_PREFIX)
STREAM_PLAYER=None
VOLUME_HAS_CHANGED=False
STREAM_PLAYER_VOLUME=1
LINK_LIST=[]

@client.command(
    name='vuvuzela',
    description='Plays an awful vuvuzela in the voice channel',
    pass_context=True,
)
async def vuvuzela(context):
    #grab the user who sent the command
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
    description='Plays the audio from a specified youtube link. If the link is not a valid youtube url it will search youtube and play the first result.',
    pass_context=True,
)
async def play(context, url, *args):
    global VOLUME_HAS_CHANGED
    global STREAM_PLAYER_VOLUME
    global STREAM_PLAYER
    global LINK_LIST
    user=context.message.author
    voice_channel = user.voice.voice_channel
    channel = None
    if voice_channel != None:
        if 'https://youtube.com/' not in url:
            search=url
            for arg in args:
                search=search+' '+arg
                query_string = urllib.parse.urlencode({"search_query": search})
                html_content = urllib.request.urlopen("http://www.youtube.com/results?" + query_string)
                search_results = re.findall(r'href=\"\/watch\?v=(.{11})', html_content.read().decode())
                url="http://www.youtube.com/watch?v=" + search_results[0]
        LINK_LIST.append(url)
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
        LINK_LIST.pop(0)
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
    STREAM_PLAYER.stop()
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


@client.command(
    name='stock',
    description='Grabs the current price of a given stock',
    pass_context=True,
)
async def stock(context, acronym):
    try:
        price=str(round(get_live_price(acronym), 2))
        company_name=get_company_name(acronym)
        await client.say('The current price of '+company_name+ ' stock is $'+price)
    except:
        await client.say('Not a valid ticker.')


def get_company_name(acronym):
    """
    Retrieves the name of a company from yahoo finance given its ticker.
    :param acronym: company's stock market ticker
    :return: company name
    """
    url = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={}&region=1&lang=en".format(acronym)
    result = requests.get(url).json()
    for x in result['ResultSet']['Result']:
        if x['symbol'] == acronym:
            return x['name']


@client.command(
    name='define',
    description='Defines a given word.',
    pass_context=True,
)
async def define(context, word):
    dictionary=PyDictionary()
    if is_word(word) and not word.isdigit():
        try:
            definitions = dictionary.meaning(word)
            for word_type in definitions:
                await client.say('**' + word_type + ':**')
                index = 1
                for d in definitions[word_type]:
                    await client.say('   ' + str(index) + '. ' + d)
                    index += 1
        except:
            await client.say('A definition for '+word+' could not be found.')
    else:
        await client.say('\"'+str(word)+'\" is not a word.')


def is_word(word):
    """
    checks whether or not the parameter word is in the dictionary
    :param word:
    :return: whether it is in the dictionary or not
    """
    dictionary=enchant.Dict('en_us')
    return dictionary.check(word)


client.run(TOKEN)
