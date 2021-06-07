from datetime import datetime
import math
import discord
import os
import sqlite3
import re
from discord.ext import commands
from cogs import bColors

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ccolor = bColors.bColors()

    # MAIN COMMANDS
    @commands.command(name='wiretransfer', aliases=['wt', 'donate'])
    async def wiretransfer(self, ctx, user, amount):

        await ctx.message.delete()

        user = self.__get_user(user)
        if not user or user is None:
            raise ValueError('Specified user could not be found. Try mentioning them, or passing a user ID.')

        amount = self.__get_positive_whole_number(ctx.author.id, amount)
        if not amount or amount is None:
            raise ValueError('Amount of transfer is not a positive whole number (>= 1).')

        if not self.__has_balance(ctx.author.id, amount):
            raise ValueError('You do not have enough karma for this wiretransfer.')

        if self.__is_same_user(ctx.author.id, user.id):
            raise ValueError('Cannot send karma to oneself.')

        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        self.__remove_karma(ctx.author.id, amount, cursor)
        self.__add_karma(user.id, amount, cursor)
        try:
            await self.__notify_users(ctx.author.id, user.id, amount, cursor)
        finally:
            cursor.close()
            db.commit()
            db.close()

    @wiretransfer.error
    async def wiretransfer_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            output = discord.Embed(
                title=f'There\'s an argument missing. Correct usage is `-wiretransfer <dest. user> <amount>`',
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
        elif isinstance(error, commands.CommandInvokeError):
            output = discord.Embed(
                title=str(error.__cause__),
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
        else:
            print(error.__class__)
            output = discord.Embed(
                title=f'Something unexpected went wrong with your wiretransfer. It most likely did not affect your karma, however.',
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
        return

    # HELPER FUNCTIONS
    def __get_ratio(self, user_id):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute(f'SELECT post_karma, link_karma FROM users WHERE user_id={user_id}')
        karma = cursor.fetchone()
        cursor.close()
        db.close()
        if karma[0] + karma[1] == 0:
            return 0.5
        else:
            return karma[0] / (karma[0] + karma[1])

    def __get_balance(self, user_id):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute(f'SELECT (post_karma + link_karma) FROM users WHERE user_id={user_id}')
        total = cursor.fetchone()[0]
        cursor.close()
        db.close()
        return total

    def __has_balance(self, user_id, amount):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute(f'SELECT (post_karma + link_karma) FROM users WHERE user_id={user_id}')
        total = cursor.fetchone()[0]
        cursor.close()
        db.close()
        return amount <= total

    def __is_same_user(self, from_id, to_id):
        return from_id == to_id

    def __remove_karma(self, user_id, amount, dbcursor):
        ratio = self.__get_ratio(user_id)
        post = round(amount * ratio)
        link = amount - post
        self.bot.get_cog('Karma').change_state_user(user_id, 'downvote', 'post', post, dbcursor)
        self.bot.get_cog('Karma').change_state_user(user_id, 'downvote', 'link', link, dbcursor)
        print(f'{self.ccolor.OKGREEN}REMOVED KARMA{self.ccolor.ENDC}: From user {user_id}, amount {amount}')

    def __add_karma(self, user_id, amount, dbcursor):
        ratio = self.__get_ratio(user_id)
        post = round(amount * ratio)
        link = amount - post
        self.bot.get_cog('Karma').change_state_user(user_id, 'upvote', 'post', post, dbcursor)
        self.bot.get_cog('Karma').change_state_user(user_id, 'upvote', 'link', link, dbcursor)
        print(f'{self.ccolor.OKGREEN}ADDED KARMA{self.ccolor.ENDC}: From user {user_id}, amount {amount}')

    async def __notify_users(self, from_id, to_id, amount, dbcursor):
        from_user = self.bot.get_user(from_id)
        to_user = self.bot.get_user(to_id)

        dbcursor.execute(f'SELECT post_karma, link_karma, (post_karma + link_karma) FROM users WHERE user_id={from_id}')
        from_karma = dbcursor.fetchone()
        dbcursor.execute(f'SELECT post_karma, link_karma, (post_karma + link_karma) FROM users WHERE user_id={to_id}')
        to_karma = dbcursor.fetchone()

        from_msg = discord.Embed(
            title=':credit_card: Wiretransfer sent on ' + datetime.now().strftime('%d.%m.%Y, %H:%M'),
            description=f'Sent {amount} Karma to {to_user.name}\n'
                        f'Remaining karma => Total: {from_karma[2]} Post: {from_karma[0]} | Link: {from_karma[1]}',
            color=discord.Colour.from_rgb(37, 204, 81)
        )

        to_msg = discord.Embed(
            title=':credit_card: Wiretransfer received on ' + datetime.now().strftime('%d.%m.%Y, %H:%M'),
            description=f'Received {amount} Karma from {from_user.name}\n'
                        f'Remaining karma => Total: {to_karma[2]} Post: {to_karma[0]} | Link: {to_karma[1]}',
            color=discord.Colour.from_rgb(37, 204, 81)
        )

        if not from_user.bot:
            await from_user.send(embed=from_msg)
        if not to_user.bot:
            await to_user.send(embed=to_msg)

    def __get_user(self, user):
        if user.startswith('<@!') and user.endswith('>'):
            user = int(user.replace('<@!', '').replace('>', ''))
        elif len(user) == 18 and re.match(r'^[0-9]{18}$', user):
            user = int(user)
        else:
            return False
        return self.bot.get_user(user)

    def __get_positive_whole_number(self, user_id, amount):
        if re.match(r'^[0-9]{1,}$', amount):
            return int(amount)
        elif amount == 'all':
            return self.__get_balance(user_id)
        else:
            return False

def setup(bot):
    bot.add_cog(Economy(bot))