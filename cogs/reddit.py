import discord
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
        R_USERNAME = os.getenv('REDDIT_USERNAME')
        R_PASSWORD = os.getenv('REDDIT_PASSWORD')
        self.r_client = praw.Reddit(
            client_secret=R_SECRET,
            client_id=R_ID,
            user_agent=f'discordbot:{R_ID}:v0.2 (by u/Remaked)',
            username=R_USERNAME,
            password=R_PASSWORD
        )
        self.ccolor = bColors.bColors()

    @commands.command(name='reddit', aliases=['okbr', 'r'])
    async def reddit(self, ctx, *args):
        if str(ctx.command) in self.bot.restricted_commands and str(ctx.message.author.id) not in self.bot.owner_ids:
            await ctx.send('This command is currently only available to developers.')
            return

        # BANNED SUBREDDITS
        banned_subreddits =[
            'makemesuffer',
            'makemesuffermore',
            'fiftyfifty',
            'kek'
        ]

        if not args and '§reddit' == ctx.message.content:
            await ctx.send('Incorrect use of the command. Refer to `§help reddit` for further instructions.')
            return

        command = str(ctx.message.content).replace('§', '')

        try:
            if command == 'okbr':
                sub = self.r_client.subreddit('okbuddyretard')
            else:
                if str(args[0]) == 'random':
                    sub = self.r_client.random_subreddit()
                else:
                    if args[0] in banned_subreddits:
                        await ctx.send(f'_r/{args[0]}_ was banned.')
                        return
                    sub = self.r_client.subreddit(args[0])

            if sub.over18:
                print(self.ccolor.WARNING + 'Somebody is trying to post NSFW stuff on Discord!' + self.ccolor.ENDC)
                await ctx.send('Not going to browse _r/' + args[0] + '_ on my christian server. :flushed:')
                return

            posts = list(sub.hot(limit=50))
            post = random.choice(posts)
            n = 0
            while post.over_18:
                if n < 50:
                    post = random.choice(posts)
                else:
                    break
                n += 1
            if post.over_18:
                print(self.ccolor.WARNING + 'Somebody is trying to post NSFW stuff on Discord!' + self.ccolor.ENDC)
                await ctx.send('Couldn\'t find any non-NSFW post. Maybe another subreddit?')
                return

            to_embed = discord.Embed(
                title=post.title,
                url=post.url,
                color=discord.Colour.from_rgb(55, 133, 245)
            )
            to_embed.set_author(
                name='u/'+post.author.name,
                icon_url=post.author.icon_img if 'icon_img' in vars(post.author) else ''
            )

            to_embed.set_footer(
                text='from: r/' + sub.display_name + ' | UP: ' + str(post.score) + ' | DOWN: '
                     + str(round(post.score*(1-post.upvote_ratio))) + ' | Comments: ' + str(post.num_comments)
            )

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

