from __future__ import unicode_literals
import discord
import asyncio
from discord.ext.commands import Bot
import random
import urllib.request
import urllib.parse
import re
from yahoo_fin.stock_info import *
from PyDictionary import PyDictionary
import urllib
import json
import ssl
from gtts import gTTS
from helper_methods import is_int, is_word, spellkey, get_company_name, scrape_jokes, dictate
from pathlib import Path
import logging
from os import listdir
from os.path import isfile, join
import config
import youtube_dl
from pydub import AudioSegment


BOT_PREFIX='!harper '
TOKEN=config.TOKEN

#set global variables
# TODO: Create player class
client = Bot(command_prefix=BOT_PREFIX)
STREAM_PLAYER=None


# Command methods
@client.command(
    name='soundboard',
    description='plays a sound from the list of previously saved mp3s',
    pass_context=True,
)
async def soundboard(context, *args):
    #get the full mp3 file name
    mp3_file_name='soundboard/'
    for arg in args:
        mp3_file_name+=arg+' '
    if mp3_file_name.endswith(' '):
        mp3_file_name=mp3_file_name[:-1]
    mp3_file_name+='.mp3'
    mp3_file_name=mp3_file_name.lower()
    # grab the user who sent the command
    user=context.message.author
    voice_channel=user.voice.voice_channel
    channel=None

    #check if a file with the given name exists
    onlyfiles = [f for f in listdir('soundboard/') if isfile(join('soundboard/', f))]
    file_exists=False
    for file in onlyfiles:
        test_file_name='soundboard/'+file
        if mp3_file_name == test_file_name:
            file_exists=True

    # only play music if user is in a voice channel
    if voice_channel!= None and file_exists:
        # grab user's voice channel
        channel=voice_channel.name
        # create StreamPlayer
        vc= await client.join_voice_channel(voice_channel)
        player = vc.create_ffmpeg_player(mp3_file_name, after=lambda: print('done'))
        player.start()
        while not player.is_done():
            await asyncio.sleep(1)
        # disconnect after the player has finished
        player.stop()
        await vc.disconnect()
    else:
        await client.say('User is not in a channel or file doesnt exist.')


@client.command(
    name='list_soundboard',
    description='Lists all of the possible soundboard options',
    pass_context=True,
)
async def list_soundboard(context):
    onlyfiles = [f for f in listdir('soundboard/') if isfile(join('soundboard/', f))]
    for file in onlyfiles:
        file_name=file[:-4]
        await client.say(file_name)
    return


@client.command(
    name='upload_soundboard',
    description='Uploads a new mp3 file to the soundboard. Works by first selecting a file and then adding \"!piper upload_soundboard <title>\"',
    pass_context=True,
)
async def upload_soundboard(context, *args):

    if len(context.message.attachments)>0:
        mp3_file_name = 'soundboard/'
        for arg in args:
            mp3_file_name += arg + ' '
        if mp3_file_name.endswith(' '):
            mp3_file_name = mp3_file_name[:-1]
        mp3_file_name += '.mp3'
        mp3_file_name = mp3_file_name.lower()

        url=context.message.attachments[0]['url']
        req = urllib.request.Request(url, headers={'User-Agent': "Magic Browser"})
        with urllib.request.urlopen(req) as response, open(mp3_file_name, 'wb') as out_file:
            data=response.read()
            out_file.write(data)
    return


@client.command(
    name='update_intro',
    description='Updates or creates a user\'s intro soundbyte.',
    pass_context=True,
)
async def update_intro(context):
    intro_soundbyte='custom_soundbytes/'+context.message.author.name+'.mp3'
    soundboard_file='soundboard/'+context.message.author.name+'.mp3'
    url = context.message.attachments[0]['url']
    req = urllib.request.Request(url, headers={'User-Agent': "Magic Browser"})
    with urllib.request.urlopen(req) as response, open(intro_soundbyte, 'wb') as out_file:
        data = response.read()
        out_file.write(data)
    with urllib.request.urlopen(req) as response, open(soundboard_file, 'wb') as out_file:
        data = response.read()
        out_file.write(data)


@client.command(
    name='play',
    description='Plays the audio from a specified youtube link. If the link is not a valid youtube url it will search youtube and play the first result.',
    pass_context=True,
)
async def play(context, url, *args):
    await play_yt(url, context.message.author.voice.voice_channel, context.message.channel, *args)


async def play_yt(url, voice_channel, text_channel, *args):
    global STREAM_PLAYER
    emojis = client.get_all_emojis()
    play_emoji = next(emojis)
    play_pause_emoji = next(emojis)
    stop_emoji = next(emojis)
    down_emoji = next(emojis)
    up_emoji = next(emojis)
    # grab the voice channel of the user
    channel = None
    if voice_channel != None:
        if 'https://youtube.com/' not in url:
            search = url
            for arg in args:
                search = search + ' ' + arg
                query_string = urllib.parse.urlencode({"search_query": search})
                html_content = urllib.request.urlopen("http://www.youtube.com/results?" + query_string)
                search_results = re.findall(r'href=\"\/watch\?v=(.{11})', html_content.read().decode())
                url = "http://www.youtube.com/watch?v=" + search_results[0]
        vc = await client.join_voice_channel(voice_channel)
        passed = False
        index = 0
        player = None
        while not passed:
            try:
                # check https://github.com/Rapptz/discord.py/issues/315 if you encounter any issues
                beforeArgs = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
                player = await vc.create_ytdl_player(url=url, before_options=beforeArgs)
                passed = True
            except:
                index += 1
                query_string = urllib.parse.urlencode({"search_query": search})
                html_content = urllib.request.urlopen("http://www.youtube.com/results?" + query_string)
                search_results = re.findall(r'href=\"\/watch\?v=(.{11})', html_content.read().decode())
                url = "http://www.youtube.com/watch?v=" + search_results[index]
        STREAM_PLAYER = player
        title = player.title
        url = player.url
        embed = discord.Embed(title=title, color=0x992d22)
        embed.add_field(name='Video URL', value=url, inline=False)
        msg = await client.send_message(text_channel, embed=embed)
        await client.add_reaction(message=msg, emoji=play_pause_emoji)
        await client.add_reaction(message=msg, emoji=stop_emoji)
        await client.add_reaction(message=msg, emoji=down_emoji)
        await client.add_reaction(message=msg, emoji=up_emoji)
        player.start()
        while not player.is_done():
            await asyncio.sleep(1)
        player.stop()
        await vc.disconnect()
    else:
        await client.say('User is not in a channel.')

    return


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
    if STREAM_PLAYER != None:
        STREAM_PLAYER.stop()
    STREAM_PLAYER=None


@client.command(
    name='volume',
    description='Change the volume that Piper is playing the current song at.',
    pass_context=True,
)
async def volume(context, vol):
    global STREAM_PLAYER
    if STREAM_PLAYER != None:
        STREAM_PLAYER.volume=int(vol)/100


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
    name='embed_test',
    description='',
    pass_context=True,
)
async def embed_test(context):
    emojis = client.get_all_emojis()
    play_emoji = next(emojis)
    play_pause_emoji = next(emojis)
    stop_emoji = next(emojis)
    down_emoji = next(emojis)
    up_emoji = next(emojis)
    title='Mashd N Kutcher - Do It Now (Official Lyric Video)'
    url='https://www.youtube.com/watch?v=40KHZ-Jxt6U'
    embed=discord.Embed(title=title, color=0x992d22)
    embed.add_field(name='Video URL', value=url, inline=False)
    msg= await client.send_message(context.message.channel, embed=embed)
    await client.add_reaction(message=msg, emoji=play_pause_emoji)
    await client.add_reaction(message=msg, emoji=stop_emoji)
    await client.add_reaction(message=msg, emoji=down_emoji)
    await client.add_reaction(message=msg, emoji=up_emoji)
    print(play_emoji.name)
    print(play_pause_emoji.name)
    print(stop_emoji.name)
    print(down_emoji.name)
    print(up_emoji.name)
    return

@client.command(
    name='clip',
    description='',
    pass_context=True,
)
async def clip(context, url, start_time, end_time, *args):
    name = ''
    for word in args:
        name = name + str(word) + '+'
    if len(name) > 0:
        name = name[:-1]
    name = name.replace('+', ' ')
    parent_dir='C:\\Users\\Ben\\PycharmProjects\\piper\\soundboard\\'
    filepath = parent_dir + str(name) + '.%(ext)s'
    ydl_opts = {
        'outtmpl': filepath,
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],

    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    audio = AudioSegment.from_mp3(parent_dir+ str(name) + '.mp3')
    start_time=int(start_time)
    end_time=int(end_time)
    start_time *= 1000
    end_time *= 1000
    extract = audio[start_time:end_time]
    extract.export(parent_dir+ str(name) + '.mp3', format='mp3')
    await client.say('Soundbyte added')
    msgs=[]
    soundboard_channel = client.get_channel(config.SOUNDBOARD_CHANNEL_ID)
    async for msg in client.logs_from(soundboard_channel):
        msgs.append(msg)
    if len(msgs)>1:
        await client.delete_messages(msgs)
    elif len(msgs)==1:
        for message in msgs:
            await client.delete_message(message)
    onlyfiles = [f for f in listdir('soundboard/') if isfile(join('soundboard/', f))]
    for file in onlyfiles:
        file_name = file[:-4]
        await client.send_message(soundboard_channel, file_name)
    play_emoji=next(client.get_all_emojis())
    async for msg in client.logs_from(soundboard_channel):
        await client.add_reaction(message=msg, emoji=play_emoji)
    return


#On event methods
@client.event
async def on_message(message):
    if spellkey(message.content) and message.channel.name != 'spellbreak-lobby-codes' and message.channel.name != 'hidden':
        spellbreak_channel=client.get_channel(config.SPELLBREAK_CHANNEL_ID)
        await client.send_message(spellbreak_channel, message.content)
        await client.delete_message(message)
    text=message.content.lower()
    if 'bad bot' == text:
        config.BAD_BOT+=1
        channel = message.channel
        msg = 'Thank you for the constructive feedback, I have been called a naughty bot ' + str(config.BAD_BOT) + ' times.'
        await client.send_message(channel, msg)
    elif 'good bot' == text:
        config.GOOD_BOT+=1
        channel = message.channel
        msg = 'Thank you for your feedback! I have been called a good bot ' + str(config.GOOD_BOT) + ' times!'
        await client.send_message(channel, msg)
    await client.process_commands(message)


@client.event
async def on_voice_state_update(before, after):
    #find the server that the user is in for the conditional
    if before.voice_channel == None:
        server=after.voice_channel.server
    else:
        server=before.voice_channel.server
    #only if the user whos voice state updated is not a bot and the bot is not already connected to the server
    if not after.bot and not client.is_voice_connected(server):
        before_channel = before.voice_channel
        after_channel = after.voice_channel
        if before_channel != after_channel and after_channel != None and before_channel == None:
            #check if a soundbyte for the user exists
            path='custom_soundbytes/'+after.name+'.mp3'
            file_check=Path(path)
            if file_check.exists():
                channel = client.get_channel(after_channel.id)
                user_sound_byte = 'custom_soundbytes/' + after.name + '.mp3'
                # create StreamPlayer
                vc = await client.join_voice_channel(channel)
                player = vc.create_ffmpeg_player(user_sound_byte, after=lambda: print('done'))
                player.start()
                while not player.is_done():
                    await asyncio.sleep(1)
                # disconnect after the player has finished
                player.stop()
                await vc.disconnect()


@client.event
async def on_reaction_add(reaction, user):
    global STREAM_PLAYER
    emojis = client.get_all_emojis()
    play_emoji = next(emojis)
    play_pause_emoji = next(emojis)
    stop_emoji = next(emojis)
    down_emoji = next(emojis)
    up_emoji = next(emojis)
    soundboard_channel = client.get_channel(config.SOUNDBOARD_CHANNEL_ID)
    if reaction.message.channel is soundboard_channel:
        voice_channel=user.voice.voice_channel
        mp3_file_name='soundboard/'+reaction.message.content+'.mp3'
        # check if a file with the given name exists
        onlyfiles = [f for f in listdir('soundboard/') if isfile(join('soundboard/', f))]
        file_exists = False
        for file in onlyfiles:
            test_file_name = 'soundboard/' + file
            if mp3_file_name == test_file_name:
                file_exists = True
        # only play music if user is in a voice channel
        if voice_channel != None and file_exists:
            # grab user's voice channel
            channel = voice_channel.name
            # create StreamPlayer
            vc = await client.join_voice_channel(voice_channel)
            player = vc.create_ffmpeg_player(mp3_file_name, after=lambda: print('done'))
            player.start()
            while not player.is_done():
                await asyncio.sleep(1)
            # disconnect after the player has finished
            player.stop()
            await vc.disconnect()
    elif not user.bot and reaction.emoji.name == play_pause_emoji.name:
        if STREAM_PLAYER != None:
            if STREAM_PLAYER.is_playing():
                STREAM_PLAYER.pause()
            else:
                STREAM_PLAYER.resume()
        else:
            try:
                await play_yt(reaction.message.embeds[0]['fields'][0]['value'], user.voice.voice_channel, reaction.message.channel)
            except:
                return
    elif not user.bot and reaction.emoji.name == stop_emoji.name:
        voice_clients = client.voice_clients
        user_vc = user.voice.voice_channel
        vc_disconnect = None
        for vc in voice_clients:
            if vc.channel == user_vc:
                vc_disconnect = vc
        if vc_disconnect != None:
            await vc_disconnect.disconnect()
        if STREAM_PLAYER != None:
            STREAM_PLAYER.stop()
        STREAM_PLAYER = None
    elif not user.bot and reaction.emoji.name == down_emoji.name:
        if STREAM_PLAYER != None:
            STREAM_PLAYER.volume -=0.1
    elif not user.bot and reaction.emoji.name == up_emoji.name:
        if STREAM_PLAYER != None:
            STREAM_PLAYER.volume +=0.1
    return


@client.event
async def on_reaction_remove(reaction, user):
    global STREAM_PLAYER
    emojis = client.get_all_emojis()
    play_emoji = next(emojis)
    play_pause_emoji = next(emojis)
    stop_emoji = next(emojis)
    down_emoji = next(emojis)
    up_emoji = next(emojis)
    soundboard_channel = client.get_channel(config.SOUNDBOARD_CHANNEL_ID)
    if reaction.message.channel is soundboard_channel:
        voice_channel=user.voice.voice_channel
        mp3_file_name='soundboard/'+reaction.message.content+'.mp3'
        # check if a file with the given name exists
        onlyfiles = [f for f in listdir('soundboard/') if isfile(join('soundboard/', f))]
        file_exists = False
        for file in onlyfiles:
            test_file_name = 'soundboard/' + file
            if mp3_file_name == test_file_name:
                file_exists = True
        # only play music if user is in a voice channel
        if voice_channel != None and file_exists:
            # grab user's voice channel
            channel = voice_channel.name
            # create StreamPlayer
            vc = await client.join_voice_channel(voice_channel)
            player = vc.create_ffmpeg_player(mp3_file_name, after=lambda: print('done'))
            player.start()
            while not player.is_done():
                await asyncio.sleep(1)
            # disconnect after the player has finished
            player.stop()
            await vc.disconnect()
    elif not user.bot and reaction.emoji.name == play_pause_emoji.name:
        if STREAM_PLAYER != None:
            if STREAM_PLAYER.is_playing():
                STREAM_PLAYER.pause()
            elif not STREAM_PLAYER.is_done():
                STREAM_PLAYER.resume()
        else:
            try:
                await play_yt(reaction.message.embeds[0]['fields'][0]['value'], user.voice.voice_channel, reaction.message.channel)
            except:
                return
    elif not user.bot and reaction.emoji.name == stop_emoji.name:
        voice_clients = client.voice_clients
        user_vc = user.voice.voice_channel
        vc_disconnect = None
        for vc in voice_clients:
            if vc.channel == user_vc:
                vc_disconnect = vc
        if vc_disconnect != None:
            await vc_disconnect.disconnect()
        if STREAM_PLAYER != None:
            STREAM_PLAYER.stop()
        STREAM_PLAYER = None
    elif not user.bot and reaction.emoji.name == down_emoji.name:
        if STREAM_PLAYER != None:
            STREAM_PLAYER.volume -=0.1
    elif not user.bot and reaction.emoji.name == up_emoji.name:
        if STREAM_PLAYER != None:
            STREAM_PLAYER.volume +=0.1
    return


@client.event
async def on_ready():
    """
    Displays a short message in the console when the bot is initially run
    :return:
    """
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    #clear all the messages in the soundboard channel
    msgs=[]
    soundboard_channel = client.get_channel(config.SOUNDBOARD_CHANNEL_ID)
    async for msg in client.logs_from(soundboard_channel):
        msgs.append(msg)
    if len(msgs)>1:
        await client.delete_messages(msgs)
    elif len(msgs)==1:
        for message in msgs:
            await client.delete_message(message)
    print('text channel <soundboard> has been cleared')
    onlyfiles = [f for f in listdir('soundboard/') if isfile(join('soundboard/', f))]
    for file in onlyfiles:
        file_name = file[:-4]
        await client.send_message(soundboard_channel, file_name)
    print('mp3 file names listed in soundboard channel')
    play_emoji=next(client.get_all_emojis())
    async for msg in client.logs_from(soundboard_channel):
        await client.add_reaction(message=msg, emoji=play_emoji)
    # print('reactions added')
    print('------')


#code for logging errors and debug errors to the file discord.log
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

client.run(TOKEN)
