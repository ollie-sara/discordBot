# -*- coding: utf-8 -*-
import os
from discord.ext import commands
from dotenv import load_dotenv
from cogs import bColors


# COLORS FOR CONSOLE ERRORS
ccolor = bColors.bColors()

# LOAD ENV VARIABLES FROM .ENV (NOT MANAGED THROUGH VCS)
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# NECESSARY BOT STUFF
bot = commands.Bot(command_prefix='§', description="ANTICOMPSCI")
bot.remove_command('help')


# BACKGROUND LOOP
async def background_loop():
    return


# EVENT HANDLING
bot.owner_ids = [
    '108305736131440640'
]

with open(os.path.abspath('./data/bannedsubs.txt')) as f:
    bot.banned_subs = f.read().splitlines()


def reload_banned_subs():
    pass


bot.restricted_commands = [
    'bansub',
    'unbansub'
]

@bot.event
async def on_message(message):
    await bot.process_commands(message)


@bot.event
async def on_ready():
    await background_loop()
    print(f'{bot.user} joined on server!')


@bot.event
async def on_command_error(_, error):
    print(ccolor.FAIL + "COMMAND ERROR: " + ccolor.ENDC + str(error))


# COMMANDS
modules = [
    'reddit',
    'help',
    'smallutils'
]

try:
    for m in modules:
        bot.load_extension('cogs.'+m)
except Exception as e:
    print(f'{ccolor.FAIL}COG ERROR: {ccolor.ENDC}'+str(e))

bot.run(TOKEN)
