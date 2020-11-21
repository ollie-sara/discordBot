# -*- coding: utf-8 -*-
import os
import sys
import discord
from discord.ext import commands
from dotenv import load_dotenv
from cogs import bColors


# COLORS FOR CONSOLE ERRORS
ccolor = bColors.bColors()

# LOAD ENV VARIABLES FROM .ENV (NOT MANAGED THROUGH VCS)
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# NECESSARY BOT STUFF
intents = discord.Intents(messages=True, guilds=True, reactions=True, members=True)
bot = commands.Bot(command_prefix='§', description="ANTICOMPSCI", intents=intents)
bot.remove_command('help')


# EVENT HANDLING
@bot.event
async def on_message(message):
    await bot.process_commands(message)


@bot.event
async def on_command_error(_, error):
    print(f'{ccolor.FAIL}COMMAND ERROR:{ccolor.ENDC} {error}')


@bot.event
async def on_reaction_add(reaction, user):
    await bot.get_cog('BotProcesses').on_reaction_add(reaction, user)


@bot.event
async def on_reaction_remove(reaction, user):
    await bot.get_cog('BotProcesses').on_reaction_remove(reaction, user)


@bot.event
async def on_ready():
    await bot.get_cog('BotProcesses').ainit()


@bot.command(name='restart')
async def restart(ctx):
    if await is_restricted(ctx):
        return
    currently_running = bot.cogs.copy()
    await bot.get_cog('BotProcesses').end_loop()
    for cog in currently_running:
        bot.unload_extension('cogs.' + cog.lower())
    bot.load_extension('cogs.botprocesses')
    await bot.get_cog('BotProcesses').ainit()
    await ctx.send('Restarted vital bot processes! Thank you, admin! :relaxed:')


async def is_restricted(ctx):
    if await bot.get_cog('BotProcesses').is_restricted(ctx):
        return True
    else:
        return False
bot.is_restricted = is_restricted

try:
    bot.load_extension('cogs.botprocesses')
except Exception as e:
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    print(f'{ccolor.FAIL}BOT PROCESS ERROR: {ccolor.ENDC}{e} | Line: {lineno}')

bot.run(TOKEN)
