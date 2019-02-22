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
import urllib
import json
import ssl
from gtts import gTTS


BOT_PREFIX='!pipes '
#grab the token from a local txt file
with open('TOKEN_FILE.txt', 'r') as myfile:
    TOKEN=myfile.read()

#set global variables
# TODO: Create player class
client = Bot(command_prefix=BOT_PREFIX)
STREAM_PLAYER=None
VOLUME_HAS_CHANGED=False
STREAM_PLAYER_VOLUME=1
LINK_LIST=[]


# Command methods
@client.command(
    name='vuvuzela',
    description='Plays an awful vuvuzela in the voice channel',
    pass_context=True,
)
async def vuvuzela(context):
    # grab the user who sent the command
    user=context.message.author
    voice_channel=user.voice.voice_channel
    channel=None
    # only play music if user is in a voice channel
    if voice_channel!= None:
        # grab user's voice channel
        channel=voice_channel.name
        await client.say('User is in channel: '+ channel)
        # create StreamPlayer
        vc= await client.join_voice_channel(voice_channel)
        player = vc.create_ffmpeg_player('vuvuzela.mp3', after=lambda: print('done'))
        player.start()
        while not player.is_done():
            await asyncio.sleep(1)
        # disconnect after the player has finished
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
    #grab the voice channel of the user
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
        passed=False
        index=0
        player=None
        while not passed:
            try:
                player = await vc.create_ytdl_player(url=url)
                passed=True
            except:
                index+=1
                query_string = urllib.parse.urlencode({"search_query": search})
                html_content = urllib.request.urlopen("http://www.youtube.com/results?" + query_string)
                search_results = re.findall(r'href=\"\/watch\?v=(.{11})', html_content.read().decode())
                url = "http://www.youtube.com/watch?v=" + search_results[index]
        STREAM_PLAYER = player
        msg='Now playing: '+player.title
        await client.say(msg)
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
    """
    Displays a short message in the console when the bot is initially run
    :return:
    """
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


@client.command(
    name='urban-define',
    description='Scrapes urban dictionary for the definition of a given phrase.',
    pass_context=True
)
async def urban_define(context, *args):
    phrase=''
    for word in args:
        phrase=phrase+str(word)+'+'
    if len(phrase)>0:
        phrase= phrase[:-1]
    url='http://api.urbandictionary.com/v0/define?term='+phrase
    phrase=phrase.replace('+', ' ')
    response=urllib.request.urlopen(url)
    data=json.loads(response.read())
    if len(data['list'])>0:
        definition=data['list'][0]['definition']
        definition=definition.replace('[', '')
        definition = definition.replace(']', '')
        await client.say('**'+phrase+'**: '+definition)
    else:
        await client.say('No definition found for' +phrase + '.')



@client.command(
    name='urban-random',
    description='Gives a random urban dictionary definition.',
    pass_context=True
)
async def urban_random(context):
    url='https://api.urbandictionary.com/v0/random'
    verify=ssl._create_unverified_context()
    response=urllib.request.urlopen(url, context=verify)
    data=json.loads(response.read())
    if len(data['list'])>0:
        definition=data['list'][0]['definition']
        definition=definition.replace('[', '')
        definition = definition.replace(']', '')
        await client.say('**'+data['list'][0]['word']+'**: '+definition)
    else:
        await client.say('An error has occurred, try again.')


@client.command(
    name='parrot',
    description='Converts arguments into speech and then plays that audio file in the user\'s voice channel.',
    pass_context=True,
)
async def parrot(context, *args):
    phrase = ''
    for word in args:
        phrase = phrase + str(word) + '+'
    if len(phrase) > 0:
        phrase = phrase[:-1]
    phrase = phrase.replace('+', ' ')
    language = 'en'
    phrase_mp3=gTTS(text=phrase, lang=language, slow=False)
    phrase_mp3.save("piper_dialogue.mp3")
    # grab the user who sent the command
    user = context.message.author
    voice_channel = user.voice.voice_channel
    channel = None
    # only play music if user is in a voice channel
    if voice_channel != None:
        # grab user's voice channel
        channel = voice_channel.name
        # create StreamPlayer
        vc = await client.join_voice_channel(voice_channel)
        player = vc.create_ffmpeg_player('piper_dialogue.mp3', after=lambda: print('done'))
        player.start()
        while not player.is_done():
            await asyncio.sleep(1)
        # disconnect after the player has finished
        player.stop()
        await vc.disconnect()
    else:
        await client.say('User is not in a channel.')


@client.command(
    name='joke',
    description='',
    pass_context=True,
)
async def joke(context):
    return None


#On message methods
@client.event
async def on_message(message):
    if spellkey(message.content) and message.channel.name != 'spellbreak-lobby-codes':
        spellbreak_channel=client.get_channel('546689788682436620')
        await client.send_message(spellbreak_channel, message.content)
        await client.delete_message(message)
    text=message.content.lower()
    if 'bad bot' in text:
        reputation_file_read = open('bad_bot.txt', 'r')
        counter = int(reputation_file_read.read())
        counter += 1
        reputation_file_write = open('bad_bot.txt', 'w')
        reputation_file_write.write(str(counter))
        channel = message.channel
        msg = 'Thank you for the constructive feedback, I have been called a naughty bot ' + str(counter) + ' times.'
        await client.send_message(channel, msg)
        reputation_file_read.close()
        reputation_file_write.close()
    elif 'good bot' in text:
        reputation_file_read = open('good_bot.txt', 'r')
        counter = int(reputation_file_read.read())
        counter += 1
        reputation_file_write = open('good_bot.txt', 'w')
        reputation_file_write.write(str(counter))
        channel = message.channel
        msg = 'Thank you for your feedback! I have been called a good bot ' + str(counter) + ' times!'
        await client.send_message(channel, msg)
        reputation_file_read.close()
        reputation_file_write.close()
    await client.process_commands(message)


# Helper Methods

def spellkey(code):
    return re.match(r'[A-Z0-9][A-Z0-9][A-Z0-9]-[A-Z0-9][A-Z0-9][A-Z0-9]-[A-Z0-9][A-Z0-9][A-Z0-9]', code)


def is_word(word):
    """
    checks whether or not the parameter word is in the dictionary
    :param word:
    :return: whether it is in the dictionary or not
    """
    return True




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


def scrape_jokes(subreddit):
    return


async def dictate(context, phrase, vc):
    language = 'en'
    phrase_mp3 = gTTS(text=phrase, lang=language, slow=False)
    phrase_mp3.save("piper_dialogue.mp3")
    # grab the user who sent the command
    user = context.message.author
    voice_channel = user.voice.voice_channel
    channel = None
    # only play music if user is in a voice channel
    if voice_channel != None:
        # grab user's voice channel
        channel = voice_channel.name
        # create StreamPlayer
        player = vc.create_ffmpeg_player('piper_dialogue.mp3', after=lambda: print('done'))
        player.start()
        while not player.is_done():
            await asyncio.sleep(1)
        # disconnect after the player has finished
        player.stop()
    else:
        await client.say('User is not in a channel.')
    return


client.run(TOKEN)
