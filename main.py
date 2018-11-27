# Work with Python 3.6
import discord
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

    if message.content.startswith('!piper'):
        msg = 'Hello, my name is Piper.'
        await client.send_message(message.channel, msg)

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

client.run(TOKEN)

#checks 2