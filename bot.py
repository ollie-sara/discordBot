import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime
from varname import Wrapper
import praw
import random


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
R_SECRET = os.getenv('REDDIT_SECRET')
R_ID = os.getenv('REDDIT_ID')
R_USERNAME = os.getenv('REDDIT_USERNAME')
R_PASSWORD = os.getenv('REDDIT_PASSWORD')

# NECESSARY BOT STUFF
bot = commands.Bot(command_prefix='§', description="ANTICOMPSCI")
bot.remove_command('help')
r_client = praw.Reddit(
    client_secret=R_SECRET,
    client_id=R_ID,
    user_agent='discordbot:R_ID:v0.2 (by u/Remaked)',
    username=R_USERNAME,
    password=R_PASSWORD
)
owner_ids = ['108305736131440640']


# BACKGROUND LOOP
async def background_loop():
    return


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
    print(bColors.FAIL + "COMMAND ERROR: " + bColors.ENDC + str(error))


# COMMANDS
utility = Wrapper(['ping', 'echo'])
media = Wrapper(['reddit', 'okbr'])
coms = [media, utility]


@bot.command(name='okbr')
async def r_okbr(ctx):
    """
    if owner_ids.__contains__(ctx.message.author.id):
        await ctx.send('Currently locked for development. :face_vomiting:')
        return
    """

    try:
        okbr = r_client.subreddit('okbuddyretard')
        posts = list(okbr.hot())
        post = random.choice(posts)
        n = 0
        while post.over_18:
            if n < 50:
                post = random.choice(posts)
            else:
                break
            n += 1
        if post.over_18:
            print(bColors.WARNING + 'Somebody is trying to post NSFW stuff on Discord!')
            await ctx.send('Couldn\'t find any non-NSFW post. Try again.')
            return

        to_embed = discord.Embed(
            title=post.title,
            url=post.url,
            color=discord.Colour.from_rgb(55, 133, 245)
        )
        to_embed.set_author(
            name=post.author.name,
            icon_url=post.author.icon_img
        )

        to_embed.set_footer(
            text='from: r/' + okbr.display_name + ' | UP: ' + str(post.score) + ' | DOWN: '
                 + str(round(post.score * (1 - post.upvote_ratio))) + ' | Comments: ' + str(post.num_comments)
        )

        if post.is_self:
            to_embed.description = post.selftext
        else:
            to_embed.set_image(
                url=post.url
            )
        await ctx.send(embed=to_embed)
    except Exception as e:
        print(bColors.FAIL + 'REDDIT EXCEPTION: ' + bColors.ENDC + str(e))
        await ctx.send('Something went wrong with your request. Sorry...')


@bot.command(name='source')
async def source(ctx):
    to_embed = discord.Embed(
        title='ANTICOMPSCI Source',
        color=discord.Colour.from_rgb(255, 0, 0),
        description='The source of this bot can be found under following link: \n'
                    'https://github.com/ollie-sara/discordBot'
    )
    trans_logo = discord.File(os.path.abspath('Logo_transparent.png'), filename='image.png')
    to_embed.set_thumbnail(
        url='attachment://image.png'
    )
    to_embed.set_footer(
        text='Created by ollie[16] in HS2020'
    )
    await ctx.send(embed=to_embed, file=trans_logo)


@bot.command(name='reddit')
async def reddit(ctx, arg):
    """
    if owner_ids.__contains__(ctx.message.author.id):
        await ctx.send('Currently locked for development. :face_vomiting:')
        return
    """

    try:
        if str(arg) == 'random':
            sub = r_client.random_subreddit()
        else:
            sub = r_client.subreddit(arg)

        if sub.over18:
            print(bColors.WARNING + 'Somebody is trying to post NSFW stuff on Discord!')
            await ctx.send('Not going to browse _r/' + arg + '_ on my christian server. :flushed:')
            return

        posts = list(sub.hot())
        post = random.choice(posts)
        n = 0
        while post.over_18:
            if n < 50:
                post = random.choice(posts)
            else:
                break
            n += 1
        if post.over_18:
            print(bColors.WARNING + 'Somebody is trying to post NSFW stuff on Discord!')
            await ctx.send('Couldn\'t find any non-NSFW post. Maybe another subreddit?')
            return

        to_embed = discord.Embed(
            title=post.title,
            url=post.url,
            color=discord.Colour.from_rgb(55, 133, 245)
        )
        to_embed.set_author(
            name=post.author.name,
            icon_url=post.author.icon_img
        )

        to_embed.set_footer(
            text='from: r/' + sub.display_name + ' | UP: ' + str(post.score) + ' | DOWN: '
                 + str(round(post.score*(1-post.upvote_ratio))) + ' | Comments: ' + str(post.num_comments)
        )
        if post.is_self:
            if len(post.selftext) < 2000:
                text = post.selftext[0:1985] + '... **read more on reddit**'
            else:
                text = post.selftext
            to_embed.description = text
        else:
            if str(post.url).__contains__('.gifv'):
                # TODO: GET GIFV TO WORK
                await ctx.send('Sorry, no support for .gifv files yet')
                return
            else:
                to_embed.set_image(
                    url=post.url
                )
        await ctx.send(embed=to_embed)
    except Exception as e:
        print(bColors.FAIL + 'REDDIT EXCEPTION: ' + bColors.ENDC + str(e))
        if str(e).__contains__('404') or str(e).__contains__('search'):
            await ctx.send('It seems the subreddit you supplied doesn\'t exist...')
        else:
            await ctx.send('Something went wrong with your request. Sorry...')


@bot.command(name='ping')
async def ping(ctx):
    try:
        latency = str(round(bot.latency*1000)) + " ms"
        to_embed = discord.Embed(
            title=':ping_pong: Pong!',
            description='Latency in ms: `' + str(latency) + '`',
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
            description='Latency in ms: `' + str(latency) + '`',
            color=discord.Colour.from_rgb(255, 0, 0),
        )
        to_embed.set_footer(text='As of: ' + datetime.now().strftime('%a, %d.%m.%Y, %H:%M'))
        await ctx.send(embed=to_embed)
    except Exception as e:
        print(e)
        await ctx.send("Couldn't print latency because ollie sucks at coding.")


@bot.command(name='echo')
async def test(ctx, *args):
    out = ''
    for a in args:
        out += a + ' '
    await ctx.send(out)


@bot.command(name='help')
async def myhelp(ctx, *args):
    to_embed = discord.Embed(
        color=discord.Colour.from_rgb(255, 0, 0),
    )
    trans_logo = discord.File(os.path.abspath('Logo_transparent.png'), filename='image.png')
    to_embed.set_thumbnail(
        url='attachment://image.png'
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
            to_embed.description = 'Correct form: `§ping` \n' \
                                   'Used to return latency of the bot.'
            to_embed.set_footer(text='Alternative version: §pong')
        elif com == 'pong':
            to_embed.description = 'Correct form: `§pong` \n' \
                                   'Used to return latency of the bot.'
            to_embed.set_footer(text='Alternative version: §ping')
        elif com == 'echo':
            to_embed.description = 'Correct form: `§echo` \n' \
                                   'Largely for debug purposes. Simply returns your message 1:1.'
        elif com == 'reddit':
            to_embed.description = 'Correct form: `§reddit <sub>`\n' \
                                   'Returns a random post from subreddit specified in `<sub>`\n' \
                                   '(Text or Image)'
            to_embed.set_footer(text='Use \"random\" as your <sub> for a random subreddit')
        elif com == 'okbr':
            to_embed.description = 'Correct form: `§okbr`\n' \
                                   'Returns a random post from r/okbuddyretard'
        elif com == 'source':
            to_embed.description = 'Correct form: `§source`\n' \
                                   'Returns a link to this bots source code.'

    await ctx.send(file=trans_logo, embed=to_embed)


bot.run(TOKEN)
