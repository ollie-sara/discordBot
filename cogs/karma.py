import discord
import json
from discord.ext import commands
from cogs import bColors
from data.users import User
from data.posts import Post
import os
from datetime import datetime

class Karma(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ccolor = bColors.bColors()
        self.users = self.load_users()
        self.posts = self.load_posts()

    async def saving_routine(self):
        self.save_posts()
        print(f'{self.ccolor.OKCYAN}SAVED POSTS{self.ccolor.ENDC}')
        self.save_users()
        print(f'{self.ccolor.OKCYAN}SAVED USERS{self.ccolor.ENDC}')
        self.users = self.load_users()
        print(f'{self.ccolor.OKCYAN}LOADED USERS{self.ccolor.ENDC}')
        self.posts = self.load_posts()
        print(f'{self.ccolor.OKCYAN}LOADED POSTS{self.ccolor.ENDC}')

    @commands.command(name='postlb', aliases=['plb'])
    async def postlb(self, ctx):
        if await self.bot.is_restricted(ctx):
            return
        posts = self.posts
        posts = sorted(posts.values(), key=lambda x: x.upvotes, reverse=True)
        all_board = ''
        i = 1
        for post in posts[:5]:
            all_board += f'**{i}.** [{post.content if len(post.content) > 0 else "Message"}...]({post.message_url}) | by {post.author[:10]+("..." if len(post.author)>10 else "")} ({post.upvotes})\n'
            i += 1
        posts = [post for post in posts if (datetime.now() - post.created_at).days < 30]
        month_board = ''
        i = 1
        for post in posts[:5]:
            month_board += f'**{i}.** [{post.content if len(post.content) > 0 else "Message"}...]({post.message_url}) | by {post.author[:10]+("..." if len(post.author)>10 else "")} ({post.upvotes})\n'
            i += 1
        posts = [post for post in posts if (datetime.now() - post.created_at).days < 7]
        week_board = ''
        i = 1
        for post in posts[:5]:
            week_board += f'**{i}.** [{post.content if len(post.content) > 0 else "Message"}...]({post.message_url}) | by {post.author[:10]+("..." if len(post.author)>10 else "")} ({post.upvotes})\n'
            i += 1
        to_embed = discord.Embed(
            title='Top Messages',
            color=discord.Colour.from_rgb(0, 196, 144)
        )
        to_embed.set_thumbnail(
            url=ctx.guild.icon_url
        )
        to_embed.add_field(
            name='Top 5 All Time',
            value=all_board,
            inline=False
        )
        to_embed.add_field(
            name='Top 5 This Month',
            value=month_board,
            inline=False
        )
        to_embed.add_field(
            name='Top 5 This Week',
            value=week_board,
            inline=False
        )
        await ctx.send(embed=to_embed)

    @commands.command(name='karma', aliases=['k'])
    async def karma(self, ctx, *args):
        if await self.bot.is_restricted(ctx):
            return

        if not args:
            uid = ctx.author.id
        elif len(ctx.message.raw_mentions) != 0:
            uid = ctx.message.raw_mentions[0]
        elif args[0] == 'lb':
            await self.print_leaderboard(ctx)
            return
        else:
            uid = None
        try:
            user = self.users[str(uid)]
        except KeyError as e:
            if uid is not None:
                self.add_user(uid)
                user = self.users[str(uid)]
            else:
                await ctx.send(f'Could not find specified user. Id: {uid}')
                print(f'{self.ccolor.FAIL}KEY ERROR: {self.ccolor.ENDC}{e} not in users.json')
                return

        auth = ctx.author.display_name
        auth_img = ctx.author.avatar_url

        to_embed = discord.Embed(
            title=ctx.guild.get_member(uid).display_name,
            color=discord.Colour.from_rgb(0, 196, 144)
        )
        to_embed.set_thumbnail(
            url=ctx.guild.get_member(uid).avatar_url
        )
        to_embed.add_field(
            name='Post Karma',
            inline=True,
            value=user.post_karma
        )
        to_embed.add_field(
            name='Link Karma',
            inline=True,
            value=user.link_karma
        )
        to_embed.set_footer(
            text='called by ' + auth,
            icon_url=auth_img
        )
        await ctx.send(embed=to_embed)

    async def print_leaderboard(self, ctx):
        users = self.users
        users = sorted(users.values(), key=lambda x: x.post_karma + x.link_karma, reverse=True)
        nameboard = ''
        valueboard = ''
        auth = ctx.author.display_name
        auth_img = ctx.author.avatar_url
        i = 1
        for user in users[:10]:
            if ctx.guild.get_member(user.user_id) is None:
                nameboard += f'**{i}.** _Not on this server, sorry_\n'
                valueboard += f'{user.post_karma+user.link_karma} | {user.post_karma} | {user.link_karma}\n'
            else:
                nameboard += f'**{i}.** {ctx.guild.get_member(user.user_id).display_name}\n'
                valueboard += f'{user.post_karma+user.link_karma} | {user.post_karma} | {user.link_karma}\n'
            i += 1
        to_embed = discord.Embed(
            title='Karma Leaderboard',
            color=discord.Colour.from_rgb(0, 196, 144),
        )
        to_embed.add_field(
            name='#. Name',
            value=nameboard
        )
        to_embed.set_footer(
            text='called by ' + auth,
            icon_url=auth_img
        )
        to_embed.add_field(
            name='TOT | POS | LIN',
            value=valueboard
        )
        await ctx.send(embed=to_embed)

    def change_state_user(self, user_id, change, karma_type):
        if str(user_id) not in self.users:
            print(f'{self.ccolor.OKGREEN}ADDED USER: {self.ccolor.ENDC}{user_id}')
            self.add_user(user_id)
        user = self.users[str(user_id)]
        if change == 'upvote':
            user.increase_karma(karma_type)
        elif change == 'downvote':
            user.decrease_karma(karma_type)

    def change_state_post(self, message, value, increase):
        if str(message.jump_url) not in self.posts:
            print(f'{self.ccolor.OKGREEN}ADDED POST: {self.ccolor.ENDC}{message.jump_url}')
            self.add_post(message)
        post = self.posts[str(message.jump_url)]
        post.change_value(value, increase)

    def check_type(self, msg):
        if len(msg.attachments) != 0:
            return 'link'
        if 'http' in msg.content:
            return 'link'
        return 'post'

    def add_user(self, user_id):
        self.users[user_id] = User.User(user_id)

    def add_post(self, message):
        self.posts[message.jump_url] = Post.Post(url=message.jump_url, mid=message.id, created_at=message.created_at, content=message.content[:20], authorname=str(message.author.display_name))

    def load_users(self):
        if os.path.isfile(os.path.abspath('./data/users/users.json')):
            return json.load(open(os.path.abspath('./data/users/users.json')), cls=User.UserDecoder)
        else:
            return {}

    def load_posts(self):
        if os.path.isfile(os.path.abspath('./data/posts/posts.json')):
            return json.load(open(os.path.abspath('./data/posts/posts.json')), cls=Post.PostDecoder)
        else:
            return {}

    def save_users(self):
        with open(os.path.abspath('./data/users/users.json'), 'w') as outfile:
            json.dump(self.users, outfile, cls=User.UserEncoder, indent=4)

    def save_posts(self):
        with open(os.path.abspath('./data/posts/posts.json'), 'w') as outfile:
            json.dump(self.posts, outfile, cls=Post.PostEncoder, indent=4)


def setup(bot):
    bot.add_cog(Karma(bot))
