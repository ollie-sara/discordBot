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
intents = discord.Intents(messages=True, guilds=True, reactions=True, members=True);
bot = commands.Bot(command_prefix='§', description="ANTICOMPSCI", intents=intents)
bot.remove_command('help')


# BACKGROUND LOOP
async def background_loop():
    return


# EVENT HANDLING
bot.owner_ids = [
    '108305736131440640',   # OLLIE
    '153929916977643521',   # BATTLERUSH
    '205704051856244736'    # SPRÜTZ
]

with open(os.path.abspath('./data/bannedsubs.txt')) as f:
    bot.banned_subs = f.read().splitlines()


def reload_banned_subs():
    pass


bot.restricted_commands = [
    'bansub',
    'unbansub',
    'reload'
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
    print(f'{ccolor.FAIL}COMMAND ERROR:{ccolor.ENDC} {error}')


@bot.event
async def on_reaction_add(reaction, user):
    emoji = reaction.emoji.id
    if emoji == 747783377662378004 and reaction.message.author.id != user.id:
        bot.get_cog('Karma').change_state_user(user_id=reaction.message.author.id, change='upvote',
                                               karma_type=bot.get_cog('Karma').check_type(reaction.message))
        bot.get_cog('Karma').change_state_post(message=reaction.message,
                                               value='up', increase=True)
    elif emoji == 747783377662378004 and reaction.message.author.id != user.id:
        bot.get_cog('Karma').change_state_user(user_id=reaction.message.author.id, change='downvote',
                                               karma_type=bot.get_cog('Karma').check_type(reaction.message))
        bot.get_cog('Karma').change_state_post(message=reaction.message,
                                               value='down', increase=True)


@bot.event
async def on_reaction_remove(reaction, user):
    emoji = reaction.emoji.id
    if emoji == 747783377662378004 and reaction.message.author.id != user.id:
        bot.get_cog('Karma').change_state_user(user_id=reaction.message.author.id, change='upvote',
                                               karma_type=bot.get_cog('Karma').check_type(reaction.message))
        bot.get_cog('Karma').change_state_post(message=reaction.message,
                                               value='up', increase=False)
    elif emoji == 747783377662378004 and reaction.message.author.id != user.id:
        bot.get_cog('Karma').change_state_user(user_id=reaction.message.author.id, change='downvote',
                                               karma_type=bot.get_cog('Karma').check_type(reaction.message))
        bot.get_cog('Karma').change_state_post(message=reaction.message,
                                               value='down', increase=False)


# COMMANDS
modules = [
    'reddit',
    'help',
    'smallutils',
    'image',
    'karma'
]


@bot.command(name='reload')
async def reload(ctx):
    if str(ctx.command) in bot.restricted_commands and str(ctx.message.author.id) not in bot.owner_ids:
        await ctx.send('This command is currently only available to developers.')
        return
    for mo in modules:
        bot.reload_extension('cogs.'+mo)
    await ctx.send('Reloaded all cogs! Thank you, admin! :relaxed:')

bot.current_image = 0

try:
    for m in modules:
        bot.load_extension('cogs.'+m)
except Exception as e:
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    print(f'{ccolor.FAIL}COG ERROR: {ccolor.ENDC}{e} | Line: {lineno}')

bot.run(TOKEN)
