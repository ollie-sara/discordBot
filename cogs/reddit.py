import discord
import requests
from discord.ext import commands
import praw
from dotenv import load_dotenv
import os
import random
from cogs import bColors


class Reddit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        load_dotenv()
        R_SECRET = os.getenv('REDDIT_SECRET')
        R_ID = os.getenv('REDDIT_ID')
        self.r_client = praw.Reddit(
            client_secret=R_SECRET,
            client_id=R_ID,
            user_agent=f'discordbot:{R_ID}:v0.2 (by u/Remaked)'
        )
        self.ccolor = bColors.bColors()

    @commands.command(name='printbannedsubs')
    async def printbannedsubs(self, ctx):
        if await self.bot.is_restricted(ctx):
            return
        auth = ctx.message.author.display_name
        auth_img = ctx.message.author.avatar_url
        to_embed = discord.Embed(
            title='Banned subreddits',
            color=discord.Colour.from_rgb(55, 133, 245),
            description='```'
        )
        for sub in self.bot.banned_subs:
            to_embed.description += sub+'\n'
        to_embed.description += '```'
        to_embed.set_footer(
            text='as requested by ' + auth,
            icon_url=auth_img
        )
        await ctx.send(embed=to_embed)

    @commands.command(name='unbansub')
    async def unbansub(self, ctx, arg):
        if await self.bot.is_restricted(ctx):
            return

        with open(os.path.abspath('./data/bannedsubs.txt'), 'w') as f:
            for sub in self.bot.banned_subs:
                if not sub == arg:
                    f.write(sub+'\n')

        await ctx.send(f'*r/{arg}* was succesfully reinstated. :relaxed:')
        with open(os.path.abspath('./data/bannedsubs.txt')) as f:
            self.bot.banned_subs = f.read().splitlines()
        try:
            for m in self.bot.modules:
                self.bot.load_extension('cogs.' + m)
        except Exception as e:
            print(f'{self.ccolor.FAIL}COG ERROR: {self.ccolor.ENDC}' + str(e))

    @commands.command(name='bansub')
    async def bansub(self, ctx, arg):
        if await self.bot.is_restricted(ctx):
            return

        with open(os.path.abspath('./data/bannedsubs.txt'), 'a') as f:
            f.write('\n'+arg)
        await ctx.send(f'*r/{arg}* was succesfully yeeted. :relaxed:')
        with open(os.path.abspath('./data/bannedsubs.txt')) as f:
            self.bot.banned_subs = f.read().splitlines()
        try:
            for m in self.bot.modules:
                self.bot.load_extension('cogs.' + m)
        except Exception as e:
            print(f'{self.ccolor.FAIL}COG ERROR: {self.ccolor.ENDC}' + str(e))

    @commands.command(name='reddit', aliases=['okbr', 'r', 'redditimage', 'ri'])
    async def reddit(self, ctx, *args):
        if await self.bot.is_restricted(ctx):
            return

        command = str(ctx.message.content).replace('§', '')
        if not args and command in ctx.message.content and command != 'okbr':
            await ctx.send('Incorrect use of the command. Refer to `§help reddit` for further instructions.')
            return

        auth = ctx.message.author.display_name
        auth_img = ctx.message.author.avatar_url
        if args:
            sub_string = args[0].lower()
            if '%' in sub_string:
                sub_string = sub_string.split('%')[0]
            if '/' in sub_string:
                sub_string = sub_string.split('/')[0]
            temp = sub_string
            sub_string = ''
            for c in temp:
                if c in 'abcdefghijklmnopqrstuvwxyz_1234567890':
                    sub_string += c
        else:
            sub_string = command
        try:
            if command == 'okbr':
                sub = self.r_client.subreddit('okbuddyretard')
            else:
                if str(sub_string) == 'random':
                    sub = self.r_client.random_subreddit()
                else:
                    if sub_string in self.bot.banned_subs:
                        await ctx.send(f'*r/{sub_string}* was banned.')
                        return
                    sub = self.r_client.subreddit(args[0])

            if sub.over18:
                print(self.ccolor.WARNING + 'Somebody is trying to post NSFW stuff on Discord!' + self.ccolor.ENDC)
                await ctx.send('Not going to browse _r/' + sub_string + '_ on my christian server. :flushed:')
                return

            posts = list(sub.top(limit=20))+list(sub.top(time_filter='year', limit=20))+list(sub.hot(limit=10))
            post = random.choice(posts)
            n = 0
            fits_criteria = False
            while not fits_criteria and not n >= 50:
                fits_criteria = True
                if 'redditimage' in command or 'ri' in command:
                    if post.is_self:
                        fits_criteria = False
                    else:
                        if vars(post).get('url_overridden_by_dest') is None or vars(post) is None:
                            fits_criteria = False
                            n += 1
                            continue
                        url = vars(post).get('url_overridden_by_dest')
                        if post.media is not None:
                            if 'reddit_video' not in str(post.media):
                                fits_criteria = False
                            elif '.mp4' not in str(post.media.get('reddit_video').get('fallback_url')):
                                fits_criteria = False
                        elif '.png' not in url and '.gif' not in url and '.jpg' not in url and 'gfycat' not in url and 'imgur' not in url:
                            fits_criteria = False
                if post.media is not None:
                    if 'reddit_video' in str(post.media):
                        if '.mp4' not in str(post.media.get('reddit_video').get('fallback_url')):
                            fits_criteria = False
                if 'gallery' in post.url:
                    fits_criteria = False
                if post.over_18:
                    fits_criteria = False
                if not fits_criteria:
                    post = random.choice(posts)
                n += 1

            if not fits_criteria:
                if 'redditimage' in command or 'ri' in command:
                    await ctx.send('Couldn\'t find any sendable pictures. Maybe another subreddit?')
                else:
                    await ctx.send('Couldn\'t find any sendable posts. Maybe another subreddit?')
                return
            url = vars(post).get('url_overridden_by_dest')

            post_title = post.title
            if len(post.title) > 256:
                post_title = post.title[0:252]+'...'
            to_embed = discord.Embed(
                title=post_title,
                url='https://www.reddit.com'+post.permalink,
                color=discord.Colour.from_rgb(55, 133, 245)
            )
            to_embed.set_author(
                name='from: r/' + sub.display_name + ' | UP: ' + str(post.score) + ' | DOWN: ' + str(round(post.score*(1-post.upvote_ratio))) + ' | Comments: ' + str(post.num_comments)
            )
            to_embed.set_footer(
                text='called by ' + auth,
                icon_url=auth_img
            )
            # print(vars(post))
            if post.is_self:
                text = post.selftext
                if len(str(post.selftext)) > 1950:
                    text = post.selftext[0:1925] + '...***more on reddit***'
                to_embed.description = text
                await ctx.send(embed=to_embed)
                return
            elif str(post.media) != 'None':
                if 'reddit_video' in post.media:
                    await ctx.send(embed=to_embed)
                    await ctx.send(str(post.media.get('reddit_video').get('fallback_url').replace('?source=fallback', '')))
                else:
                    await ctx.send(embed=to_embed)
                    await ctx.send(post.url)
            else:
                url = vars(post).get('url_overridden_by_dest')
                if str(url).endswith('.png') or str(url).endswith('.jpg') or str(url).endswith('.gif') or str(url).endswith('.jpeg'):
                    to_embed.set_image(url=url)
                    await ctx.send(embed=to_embed)
                else:
                    await ctx.send(embed=to_embed)
                    await ctx.send(post.url)

        except Exception as e:
            print(self.ccolor.FAIL + 'REDDIT EXCEPTION: ' + self.ccolor.ENDC + str(e))
            if str(e).__contains__('search'):
                await ctx.send('It seems the subreddit you supplied doesn\'t exist...')
            else:
                await ctx.send('Something went wrong with your request. Sorry...')


def setup(bot):
    bot.add_cog(Reddit(bot))
