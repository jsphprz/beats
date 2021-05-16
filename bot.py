import asyncio
import os
import discord
from discord.ext import commands, tasks
from discord.voice_client import VoiceClient
import youtube_dl
from random import choice
from dotenv import load_dotenv

load_dotenv()

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

client = commands.AutoShardedBot(commands.when_mentioned_or('$'))
client.remove_command("help")

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online, activity=discord.Game('music | $help')) 
    print('Ready!')

@client.group(invoke_without_command=True)
async def help(ctx):
    em = discord.Embed(title = "Help", color = discord.Color.from_rgb(109,0,0))
    em.set_thumbnail(url='https://cdn.discordapp.com/attachments/840935119866429441/841955752318468116/logo.png')
    em.add_field(name = "Play a music", value = "`$play`")
    em.add_field(name = "Pause", value = "`$pause`")
    em.add_field(name = "Resume", value = "`$resume`")
    em.add_field(name = "Stop", value = "`$stop`")
    em.add_field(name = "Disconnect bot", value = "$`disconnect`")
    em.add_field(name = "Check Bot Latency", value = "`$ping
    em.add_field(name = "GitHub page", value = "``github`", inline=False)

    await ctx.send(embed=em)

@client.command(name='ping')
async def ping(ctx):
    await ctx.send(f'Latancy: {round(client.latency * 1000)}ms')

@client.command('github')
async def ghub(ctx):
    await ctx.send('https://github.com/jsphprz/beats')

@client.command(name='play')
async def play(ctx, url):
    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel")
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()

    #play(discord.FFmpegPCMAudio(executable="C:/ffmpeg/bin/ffmpeg.exe", source="mp3.mp3"))
    server = ctx.message.guild
    voice_channel = server.voice_client

    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=client.loop)
        voice_channel.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

    await ctx.send('Now playing: `{}` '.format(player.title))

@client.command(name='pause')
async def pause(ctx):
    server = ctx.message.guild
    voice_channel = server.voice_client
    await ctx.send("Music paused.")
    voice_channel.pause()

@client.command(name='resume')
async def resume(ctx):
    server = ctx.message.guild
    voice_channel = server.voice_client
    await ctx.send("Music resumed.")
    voice_channel.resume()

@client.command(name='stop')
async def stop(ctx):
    server = ctx.message.guild
    voice_channel = server.voice_client
    await ctx.send("Music stopped.")
    voice_channel.stop()

@client.command(name='disconnect')
async def disconnect(ctx):
    voice_client = ctx.message.guild.voice_client
    await voice_client.disconnect()


client.run(os.getenv("TOKEN"))
