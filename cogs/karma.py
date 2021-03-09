import os
import sqlite3
import discord
from discord.ext import commands
from cogs import bColors


class Karma(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ccolor = bColors.bColors()
        self.saveIterations = 0

    async def saving_routine(self):
        self.backup_karma()
        print(f'{self.ccolor.OKCYAN}KARMA BACKUP COMPLETE{self.ccolor.ENDC}')

    def force_save(self):
        self.backup_karma()
        print(f'{self.ccolor.OKCYAN}KARMA BACKUP COMPLETE{self.ccolor.ENDC}')

    @commands.command(name='checkpost', aliases=['chp'])
    async def checkpost(self, ctx, *args):
        if await self.bot.is_restricted(ctx):
            return
        message_id = args[0]
        channel_id = args[1]
        message = await (await ctx.bot.fetch_channel(channel_id)).fetch_message(message_id)
        up = 0
        down = 0
        for reaction in message.reactions:
            if str(reaction.emoji) == '<:this:747783377662378004>':
                up = reaction.count-1
            if str(reaction.emoji) == '<:that:758262252699779073>':
                down = reaction.count-1
        self.set_state_post(message, up, down)
        await ctx.send('Checked and updated the post you supplied. Thank you admin! :relaxed:')

    @commands.command(name='postlb', aliases=['plb'])
    async def postlb(self, ctx):
        if await self.bot.is_restricted(ctx):
            return

        karmadb = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = karmadb.cursor()

        posts = cursor.execute('SELECT content, message_url, author, upvotes-downvotes AS net FROM posts ORDER BY net DESC LIMIT 5')
        all_board = ''
        i = 1
        for post in posts:
            all_board += f'**{i}.** [{post[0] if len(post[0]) > 0 else "Message"}...]({post[1]}) | by {post[2][:10]+("..." if len(post[2])>10 else "")} ({post[3]})\n'
            i += 1
        posts = cursor.execute(
            "SELECT content, message_url, author, upvotes-downvotes AS net FROM posts WHERE created_at > date('now', '-30 days') ORDER BY net DESC LIMIT 5")
        month_board = ''
        i = 1
        for post in posts:
            month_board += f'**{i}.** [{post[0] if len(post[0]) > 0 else "Message"}...]({post[1]}) | by {post[2][:10]+("..." if len(post[2])>10 else "")} ({post[3]})\n'
            i += 1
        posts = cursor.execute(
            "SELECT content, message_url, author, upvotes-downvotes AS net FROM posts WHERE created_at > date('now', '-7 days') ORDER BY net DESC LIMIT 5")
        week_board = ''
        i = 1
        for post in posts:
            week_board += f'**{i}.** [{post[0] if len(post[0]) > 0 else "Message"}...]({post[1]}) | by {post[2][:10]+("..." if len(post[2])>10 else "")} ({post[3]})\n'
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
        cursor.close()
        karmadb.close()
        await ctx.send(embed=to_embed)

    @commands.command(name='karma', aliases=['k'])
    async def karma(self, ctx, *args):
        if await self.bot.is_restricted(ctx):
            return

        await ctx.message.delete()
        karmadb = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = karmadb.cursor()

        if not args:
            uid = ctx.author.id
        elif len(ctx.message.raw_mentions) != 0:
            uid = ctx.message.raw_mentions[0]
        elif args[0] == 'lb':
            await self.print_leaderboard(ctx)
            return
        else:
            uid = None
        cursor.execute(f'SELECT * FROM users WHERE user_id={uid}')
        user = cursor.fetchone()
        if user is None:
            if uid is not None:
                self.add_user(uid)
                cursor.execute(f'SELECT * FROM users WHERE user_id={uid}')
                user = cursor.fetchone()
            else:
                await ctx.send(f'Could not find specified user. Id: {uid}')
                print(f'{self.ccolor.FAIL}KEY ERROR: {self.ccolor.ENDC}{uid} not in karma.db')
                cursor.close()
                karmadb.close()
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
            name='Total Karma',
            inline=True,
            value=(user[2]+user[3])
        )
        to_embed.add_field(
            name='Post Karma',
            inline=True,
            value=user[2]
        )
        to_embed.add_field(
            name='Link Karma',
            inline=True,
            value=user[3]
        )
        to_embed.set_footer(
            text='called by ' + auth,
            icon_url=auth_img
        )
        cursor.close()
        karmadb.close()
        await ctx.send(embed=to_embed, delete_after=20)

    async def print_leaderboard(self, ctx):
        karmadb = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = karmadb.cursor()
        users = cursor.execute(f'SELECT *, (post_karma + link_karma) AS total_karma FROM users ORDER BY total_karma DESC')
        nameboard = ''
        valueboard = ''
        auth = ctx.author.display_name
        auth_img = ctx.author.avatar_url
        for i in range(15):
            user = users.fetchone()
            userObj = await (self.bot.fetch_user(user[1]))
            if userObj is None:
                nameboard += f'**{i+1}.** _Not on this server, sorry_\n'
                valueboard += f'{user[4]} | {user[2]} | {user[3]}\n'
            else:
                nameboard += f'**{i+1}.** {userObj.name}\n'
                valueboard += f'{user[4]} | {user[2]} | {user[3]}\n'
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
        cursor.close()
        karmadb.close()
        await ctx.send(embed=to_embed)

    def change_state_user(self, user_id, change, karma_type, amount):
        karmadb = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = karmadb.cursor()
        cursor.execute(f'SELECT * FROM users WHERE user_id={int(user_id)}')
        user = cursor.fetchone()
        if user is None:
            print(f'{self.ccolor.OKGREEN}ADDED USER: {self.ccolor.ENDC}{user_id}')
            self.add_user(user_id)
            cursor.execute(f'SELECT * FROM users WHERE user_id={int(user_id)}')
            user = cursor.fetchone()
        if change == 'upvote':
            cursor.execute(f'UPDATE users SET {karma_type}_karma = {karma_type}_karma+{amount} WHERE user_id={int(user_id)}');
            cursor.close()
            karmadb.commit()
        elif change == 'downvote':
            cursor.execute(f'UPDATE users SET {karma_type}_karma = {karma_type}_karma-{amount} WHERE user_id={int(user_id)}');
            cursor.close()
            karmadb.commit()
        cursor.close()
        karmadb.close()

    def change_state_post(self, message, value, increase):
        karmadb = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = karmadb.cursor()
        cursor.execute(f'SELECT * FROM posts WHERE message_url="{message.jump_url}"')
        post = cursor.fetchone()
        if post is None:
            print(f'{self.ccolor.OKGREEN}ADDED POST: {self.ccolor.ENDC}{message.jump_url}')
            self.add_post(message)
        if value == 'up':
            if increase:
                cursor.execute(f'UPDATE posts SET upvotes=upvotes+1 WHERE message_id={message.id}')
            else:
                cursor.execute(f'UPDATE posts SET upvotes=upvotes-1 WHERE message_id={message.id}')
        elif value == 'down':
            if increase:
                cursor.execute(f'UPDATE posts SET downvotes=downvotes+1 WHERE message_id={message.id}')
            else:
                cursor.execute(f'UPDATE posts SET downvotes=downvotes-1 WHERE message_id={message.id}')
        cursor.close()
        karmadb.close()

    def set_state_post(self, message, upvotes, downvotes):
        karmadb = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = karmadb.cursor()
        cursor.execute(f'SELECT * FROM posts WHERE message_url="{message.jump_url}"')
        post = cursor.fetchone()
        if post is None:
            print(f'{self.ccolor.OKGREEN}ADDED POST: {self.ccolor.ENDC}{message.jump_url}')
            self.add_post(message)
        cursor.execute(f'UPDATE posts SET upvotes={upvotes}, downvotes={downvotes} WHERE message_url="{message.jump_url}"')
        cursor.close()
        karmadb.close()
        return

    def check_type(self, msg):
        if len(msg.attachments) != 0:
            return 'link'
        if 'http' in msg.content:
            return 'link'
        return 'post'

    def add_user(self, user_id):
        karmadb = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = karmadb.cursor()
        cursor.execute(f'INSERT INTO users (user_id) VALUES({user_id})')
        cursor.close()
        karmadb.commit()
        karmadb.close()

    def add_post(self, message):
        karmadb = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = karmadb.cursor()
        contentfix = message.content.replace('"', '')[:20]
        authorfix = message.author.display_name.replace('"', '')
        cursor.execute(f'INSERT INTO posts (message_url, message_id, content, author, created_at)'
                       f'VALUES("{message.jump_url}", {message.id}, "{contentfix}", "{authorfix}", "{message.created_at.strftime("%Y-%m-%d %H:%M:%S")}")')
        cursor.close()
        karmadb.close()
        return

    def backup_karma(self):
        karmadb = sqlite3.connect(os.path.abspath('./data/karma.db'))
        backupdb = sqlite3.connect(os.path.abspath('./data/backup/karma.db'))
        karmadb.backup(backupdb)
        karmadb.close()
        backupdb.commit()
        backupdb.close()
        return

def setup(bot):
    bot.add_cog(Karma(bot))
