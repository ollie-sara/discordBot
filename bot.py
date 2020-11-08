import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime
from varname import Wrapper


# COLORS FOR CONSOLE ERRORS
class bColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\u001b[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# LOAD ENV VARIABLES FROM .ENV (NOT MANAGED THROUGH VCS)
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# NECESSARY BOT STUFF
bot = commands.Bot(command_prefix='§', description="ANTICOMPSCI")
bot.remove_command('help')


# BACKGROUND LOOP
async def background_loop():
    await bot.wait_until_ready()
    while not bot.is_closed():
        await bot.change_presence(
            activity=discord.CustomActivity(
                name='Anti Computer Science Action',
                type=discord.ActivityType.custom,
                state='Current Time:',
                details=datetime.now().strftime('#H h #M m #S s')
                )
            )


# EVENT HANDLING
@bot.event
async def on_message(message):
    await bot.process_commands(message)


@bot.event
async def on_ready():
    await background_loop()
    print(f'{bot.user} joined on server!')


@bot.event
async def on_command_error(_, error):
    print(bColors.FAIL + "COMMAND ERROR: " + bColors.ENDC + bColors.UNDERLINE + str(error))


# COMMANDS
utility = Wrapper(['ping', 'echo'])
coms = [utility]


@bot.command(name='help')
async def myHelp(ctx, *args):
    to_embed = discord.Embed(
        color=discord.Colour.from_rgb(255, 0, 0)
    )
    if len(args) == 0:
        to_embed.title = 'ANTICOMPSCI Commands'
        for a in coms:
            val = ''
            for com in a.value:
                val += '`' + '§' + com + '` '
            to_embed.add_field(
                name=a.name.upper(),
                value=val,
                inline=False
            )
        to_embed.set_footer(
            text='You can use §help <command> for further instructions on a specific command'
        )
    elif len(args) > 1:
        to_embed.title = 'Incorrect usage of §help'
        to_embed.description = 'Please use `§help (<command>)`.'
    else:
        com = args.__getitem__(0)
        to_embed.title = '§' + com
        if com == 'ping':
            to_embed.description = 'Used to return latency of bot.'
            to_embed.set_footer(text='Alternative version: §pong')
        elif com == 'pong':
            to_embed.description = 'Used to return latency of bot.'
            to_embed.set_footer(text='Alternative version: §ping')
        elif com == 'echo':
            to_embed.description = 'Largely for debug purposes. Simply returns your message 1:1.'

    await ctx.send(embed=to_embed)


@bot.command(name='ping')
async def ping(ctx):
    try:
        latency = str(round(bot.latency*1000)) + " ms"
        to_embed = discord.Embed(
            title=':ping_pong: Pong!',
            description='Latency in ms: ' + str(latency),
            color=discord.Colour.from_rgb(255, 0, 0),
        )
        to_embed.set_footer(text='As of: ' + datetime.now().strftime('%a, %d.%m.%Y, %H:%M'))
        await ctx.send(embed=to_embed)
    except Exception as e:
        print(e)
        await ctx.send("Couldn't print latency because ollie sucks at coding.")


@bot.command(name='pong')
async def ping(ctx):
    try:
        latency = str(round(bot.latency*1000)) + " ms"
        to_embed = discord.Embed(
            title=':ping_pong: Ping!',
            description='Latency in ms: ' + str(latency),
            color=discord.Colour.from_rgb(255, 0, 0),
        )
        to_embed.set_footer(text='As of: ' + datetime.now().strftime('%a, %d.%m.%Y, %H:%M'))
        await ctx.send(embed=to_embed)
    except Exception as e:
        print(e)
        await ctx.send("Couldn't print latency because ollie sucks at coding.")


@bot.command(name='echo')
async def test(ctx, arg):
    await ctx.send(arg)

bot.run(TOKEN)
