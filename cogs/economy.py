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
        self.__init_trousch_db()

    # MAIN COMMANDS
    @commands.command(name='endtrousch', aliases=['endtr', 'enddare', 'endd'])
    async def endtrousch(self, ctx, trousch_id, yn):
        await ctx.message.delete()

        if not self.__is_trousch_open(trousch_id):
            raise ValueError(f'Currently, no dare is open with id {trousch_id}. Double-check and try again.')

        if not self.__is_opener(trousch_id, ctx.author.id):
            raise ValueError(f'You did not open dare with id {trousch_id}')

        username = self.__get_dest_username(trousch_id)

        yn = self.__get_yesno(yn)
        if yn is False:
            raise ValueError(f'Must specify whether or not {username} did the dare or not, using "Y" or "N" for "yes"'
                             f'and "no" respectively. Correct usage is `-endtrousch {trousch_id} <Y/N>`')

        await self.__send_trousch_conclusion(ctx, trousch_id, username, yn)
        await self.__close_trousch(trousch_id, username, yn)

    @endtrousch.error
    async def endtrousch_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            output = discord.Embed(
                title=f'There\'s an argument missing. Correct usage is `-endtrousch <ID> <Did they do it? Y/N>`',
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
        elif isinstance(error, commands.CommandInvokeError):
            output = discord.Embed(
                description=str(error.__cause__),
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
        else:
            print(error.__class__)
            output = discord.Embed(
                title=f'Something unexpected went wrong with your trousch. Please, try again.',
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
        return

    @commands.command(name='ehned', aliases=['noballs', 'en', 'nb'])
    async def ehned(self, ctx, trousch_id, amount):
        await ctx.message.delete()
        self.__init_user(ctx.author.id)

        if not self.__is_trousch_open(trousch_id):
            raise ValueError(f'Currently, no dare is open with id {trousch_id}. Double-check and try again.')

        amount = self.__get_positive_whole_number(ctx.author.id, amount)
        if not amount:
            raise ValueError('Amount of dare is not a positive whole number (>= 1).')

        if not self.__has_balance(ctx.author.id, amount):
            raise ValueError('You do not have enough karma for this dare.')

        if self.__is_directed_to_user(trousch_id, ctx.author.id):
            raise ValueError('You cannot dare yourself.')

        username = self.__get_dest_username(trousch_id)

        if self.__is_increase_dare(trousch_id, ctx.author.id):
            await self.__increase_dare(amount, ctx.author.id, trousch_id, username)
        else:
            await self.__add_dare(amount, ctx.author.id, trousch_id, username)
        await self.__update_trousch(trousch_id)

    @ehned.error
    async def ehned_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            output = discord.Embed(
                title=f'There\'s an argument missing. Correct usage is `-ehned <ID> <amount>`',
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
        elif isinstance(error, commands.CommandInvokeError):
            output = discord.Embed(
                description=str(error.__cause__),
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
        else:
            print(error.__class__)
            output = discord.Embed(
                title=f'Something unexpected went wrong with your trousch. Please, try again.',
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
        return

    @commands.command(name='trousch', aliases=['tr', 'dare'])
    async def trousch(self, ctx, user, bet):
        await ctx.message.delete()

        user = self.__get_user(user)
        if not user or user is None:
            raise ValueError('Specified user could not be found. Try mentioning them, or passing a user ID.')

        if user.bot:
            raise ValueError('Cannot dare a bot.')

        self.__init_user(ctx.author.id)
        self.__init_user(user.id)

        open_id = self.__has_open_trousch(ctx.author.id)
        if open_id is not False:
            raise ValueError(f'You have an opened bet that you need to close first. Use `-endtrousch {open_id} <Y/N>`')

        if self.__is_same_user(ctx.author.id, user.id):
            raise ValueError(f'You cannot dare yourself.')

        max_length = 256-len(user.display_name)-len(', trousch? ')
        if len(bet) > max_length:
            raise ValueError(f'Your prompt is unfortunately {len(bet) - max_length} characters too long. Your prompt was '
                             f'"{bet}".')

        await ctx.send(f'Hey, <@{user.id}>! Somebody is challenging you!')
        to_embed = discord.Embed(description='Opening trousch, wait a second...')
        msg = await ctx.send(embed=to_embed)

        trousch_id = self.__add_trousch(user.id, bet, ctx.author.id, msg)
        await self.__update_trousch(trousch_id)

    @trousch.error
    async def trousch_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            output = discord.Embed(
                title=f'There\'s an argument missing. Correct usage is `-trousch <dest. user> "<trousch prompt>"`',
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
        elif isinstance(error, commands.CommandInvokeError):
            output = discord.Embed(
                description=str(error.__cause__),
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
        else:
            print(error.__class__)
            output = discord.Embed(
                title=f'Something unexpected went wrong with your trousch. Please, try again.',
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
        return

    @commands.command(name='wiretransfer', aliases=['wt', 'donate'])
    async def wiretransfer(self, ctx, user, amount):

        await ctx.message.delete()

        user = self.__get_user(user)
        if not user or user is None:
            raise ValueError('Specified user could not be found. Try mentioning them, or passing a user ID.')

        amount = self.__get_positive_whole_number(ctx.author.id, amount)
        if not amount or amount is None:
            raise ValueError('Amount of transfer is not a positive whole number (>= 1).')

        self.__init_user(ctx.author.id)
        self.__init_user(user.id)

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
                description=str(error.__cause__),
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
    async def __notify_daree_of_conclusion(self, user, yn, prompt, total, cursor):
        to_embed = None

        cursor.execute('SELECT (post_karma + link_karma), post_karma, link_karma FROM users WHERE user_id=?', [user.id])
        karma = cursor.fetchone()

        if yn == 'y':
            to_embed = discord.Embed(
                title=f'You actually did it! Let\'s gooo!',
                description=f'You got **{total}** Karma! And you\'ve earned it!\n'
                            f'The prompt was: **"{prompt}"**\n'
                            f'New karma balance => Total: {karma[0]} | Post: {karma[1]} | Link: {karma[2]}',
                color=discord.Colour.from_rgb(255, 170, 43)
            )
        if yn == 'n':
            to_embed = discord.Embed(
                title=f':chicken: bawk bawk. You chickened out...',
                description=f'You won\'t get those juicy **{total}** Karma.\n'
                            f'The prompt was: **"{prompt}"**\n'
                            f'Karma balance remains => Total: {karma[0]} | Post: {karma[1]} | Link: {karma[2]}',
                color=discord.Colour.from_rgb(255, 170, 43)
            )
        await user.send(embed=to_embed)

    async def __notify_user_of_trousch_conclusion(self, user, dest_name, yn, total, amount, cursor):
        cursor.execute('SELECT (post_karma + link_karma), post_karma, link_karma FROM users WHERE user_id=?', [user.id])
        karma = cursor.fetchone()
        to_embed = None

        if yn == 'y':
            to_embed = discord.Embed(
                title=f'{dest_name} actually did it, and you made them do it!',
                description=f'They got **{total}** Karma, of which you contributed **{amount}** Karma!\n'
                            f'New karma balance => Total: {karma[0]} | Post: {karma[1]} | Link: {karma[2]}',
                color=discord.Colour.from_rgb(255, 170, 43)
            )
        elif yn == 'n':
            to_embed = discord.Embed(
                title=f'{dest_name} chickened out...',
                description=f'They didn\'t get their promised **{total}** Karma. '
                            f'You were returned the {amount} Karma you submitted.\n'
                            f'New karma balance => Total: {karma[0]} | Post: {karma[1]} | Link: {karma[2]}',
                color=discord.Colour.from_rgb(255, 170, 43)
            )

        await user.send(embed=to_embed)

    async def __close_trousch(self, trousch_id, username, yn):
        trousch_msg = await self.__get_trousch_msg(trousch_id)
        await trousch_msg.delete()

        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute('SELECT user_id, amount, ratio FROM trousch_reward WHERE trousch_id=?', [trousch_id])
        rewards = cursor.fetchall()
        cursor.execute('SELECT dest_user_id, amount, prompt FROM trousch WHERE id=?', [trousch_id])
        trousch = cursor.fetchone()
        cursor.execute('DELETE FROM trousch_reward WHERE trousch_id=?', [trousch_id])
        cursor.execute('DELETE FROM trousch WHERE id=?', [trousch_id])

        if yn == 'y':
            self.__add_karma(trousch[0], trousch[1], cursor)

        await self.__notify_daree_of_conclusion(self.bot.get_user(trousch[0]), yn, trousch[2], trousch[1], cursor)

        for entry in rewards:
            user = self.bot.get_user(entry[0])
            if yn == 'n':
                self.__add_karma(user.id, entry[1], cursor, entry[2])
            await self.__notify_user_of_trousch_conclusion(user, username, yn, trousch[1], entry[1], cursor)

        cursor.close()
        db.commit()
        db.close()

    async def __get_trousch_msg(self, trousch_id):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute('SELECT channel_id, message_id FROM trousch WHERE id=?', [trousch_id])
        tr_loc = cursor.fetchone()
        cursor.close()
        db.close()
        trousch_msg = (await (await self.bot.fetch_channel(tr_loc[0])).fetch_message(tr_loc[1]))
        return trousch_msg

    async def __send_trousch_conclusion(self, ctx, trousch_id, username, yn):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute('SELECT opener_id, amount, prompt FROM trousch WHERE id=?', [trousch_id])
        trousch = cursor.fetchone()
        cursor.close()
        db.close()

        to_embed = discord.Embed(
            title=f'{username} {"actually did it!" if yn=="y" else "chickened out..."}',
            description=('They got: ' if yn=='y' else 'They won\'t get: ') + f'**{trousch[1]}**\n' +
                         f'Their prompt: {trousch[2]}',
            color=discord.Colour.from_rgb(255, 170, 43)
        )

        to_embed.set_footer(text=f'opened by {self.bot.get_user(trousch[0]).display_name} | ID: {trousch_id}')

        await ctx.send(embed=to_embed)

    def __get_yesno(self, yn):
        yn = str(yn).lower().strip(' ')
        if yn in ['yes', 'y', 'da', 'yep', 'yup', 'yesh', 'ya', 'yus', 'ja', 'yis']:
            return 'y'
        elif yn in ['no', 'n', 'ne', 'na', 'nope', 'nuhuh', 'nopers', 'nein']:
            return 'n'
        else:
            return False

    def __is_opener(self, trousch_id, user_id):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute('SELECT opener_id FROM trousch WHERE id=?', [trousch_id])
        opener_id = cursor.fetchone()[0]
        cursor.close()
        db.close()
        return opener_id == user_id

    def __get_dest_username(self, trousch_id):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute('SELECT dest_user_id FROM trousch WHERE id=?', [trousch_id])
        id = cursor.fetchone()[0]
        cursor.close()
        db.close()
        return self.bot.get_user(id).display_name

    async def __increase_dare(self, amount, user_id, trousch_id, dest_username):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute('UPDATE trousch_reward SET '
                       'amount = amount + ? WHERE user_id = ? AND trousch_id = ?', [amount, user_id, trousch_id])
        cursor.execute('UPDATE trousch SET '
                       'amount = amount + ? WHERE id = ?', [amount, trousch_id])
        self.__remove_karma(user_id, amount, cursor)
        cursor.execute('SELECT (post_karma + link_karma), post_karma, link_karma FROM users WHERE user_id=?', [user_id])
        karma = cursor.fetchone()
        cursor.close()
        db.commit()
        db.close()
        to_embed = discord.Embed(
            title=f'You increased your dare for {dest_username} by {amount} karma.',
            description=f'Remaining karma => Total: {karma[0]} | Post: {karma[1]} | Link: {karma[2]}',
            color=discord.Colour.from_rgb(255, 170, 43)
        )
        await self.bot.get_user(user_id).send(embed=to_embed)

    async def __add_dare(self, amount, user_id, trousch_id, dest_username):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute('INSERT INTO trousch_reward(user_id, amount, ratio, trousch_id) VALUES '
                       '(?, ?, ?, ?);', [user_id, amount, self.__get_ratio(user_id), trousch_id])
        cursor.execute('UPDATE trousch SET '
                       'amount = amount + ? WHERE id = ?;', [amount, trousch_id])
        self.__remove_karma(user_id, amount, cursor)
        cursor.execute('SELECT (post_karma + link_karma), post_karma, link_karma FROM users WHERE user_id=?', [user_id])
        karma = cursor.fetchone()
        cursor.close()
        db.commit()
        db.close()
        to_embed = discord.Embed(
            title=f'You dared {dest_username} {amount} karma.',
            description=f'Remaining karma: Total {karma[0]} | Post: {karma[1]} | Link: {karma[2]}',
            color=discord.Colour.from_rgb(255, 170, 43)
        )
        await self.bot.get_user(user_id).send(embed=to_embed)

    def __is_directed_to_user(self, trousch_id, user_id):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute('SELECT dest_user_id FROM trousch WHERE id=?', [trousch_id])
        dest_user_id = cursor.fetchone()[0]
        cursor.close()
        db.close()
        return dest_user_id == user_id

    def __is_increase_dare(self, trousch_id, user_id):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute('SELECT * FROM trousch_reward WHERE trousch_id=? AND user_id=?', [trousch_id, user_id])
        dare = cursor.fetchone()
        cursor.close()
        db.close()
        if dare is None:
            return False
        else:
            return True

    def __is_trousch_open(self, trousch_id):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute('SELECT * FROM trousch WHERE id=?', [trousch_id])
        trousch = cursor.fetchone()
        cursor.close()
        db.close()
        if trousch is None:
            return False
        else:
            return True

    async def __update_trousch(self, trousch_id):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute(f'SELECT prompt, opener_id, dest_user_id, amount FROM trousch '
                       f'WHERE id=?;', [trousch_id])
        trousch = cursor.fetchone()
        cursor.close()
        db.close()

        username = self.bot.get_user(trousch[2]).display_name

        to_embed = discord.Embed(
            title=f'{username}, trousch? {trousch[0]}',
            description=f'Current pool: **{trousch[3]}**\n'
                        f'Use `-ehned {trousch_id} <amount>` to provide an incentive for {username}.',
            color=discord.Colour.from_rgb(255, 170, 43)
        )

        to_embed.set_footer(text=f'opened by {self.bot.get_user(trousch[1]).display_name} | ID: {trousch_id}')
        trousch_msg = (await self.__get_trousch_msg(trousch_id))
        await trousch_msg.edit(embed=to_embed)

    def __has_open_trousch(self, user_id):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute(f'SELECT id FROM trousch WHERE opener_id={user_id}')
        open_trousch = cursor.fetchone()
        cursor.close()
        db.close()
        if open_trousch is None:
            return False
        else:
            return open_trousch[0]

    def __add_trousch(self, dest_user_id, bet, opener_id, msg):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute(f'INSERT INTO trousch (prompt, opener_id, dest_user_id, guild_id, channel_id, message_id)'
                       f'VALUES(?,?,?,?,?,?);',
                       [bet, opener_id, dest_user_id, msg.guild.id, msg.channel.id, msg.id])
        cursor.execute('SELECT last_insert_rowid();')
        trousch_id = cursor.fetchone()[0]
        cursor.close()
        db.commit()
        db.close()
        return trousch_id

    def __init_user(self, user_id):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute(f'SELECT * FROM users WHERE user_id={user_id}')
        user = cursor.fetchone()
        if user is None:
            self.bot.get_cog('Karma').add_user(user_id)
        cursor.close()
        db.close()

    def __init_trousch_db(self):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS trousch ('
                       'id INTEGER PRIMARY KEY,'
                       'prompt TEXT NOT NULL,'
                       'opener_id INTEGER UNIQUE NOT NULL,'
                       'dest_user_id INTEGER NOT NULL,'
                       'amount INTEGER DEFAULT 0,'
                       'guild_id INTEGER NOT NULL,'
                       'channel_id INTEGER NOT NULL,'
                       'message_id INTEGER NOT NULL);')
        cursor.execute('CREATE TABLE IF NOT EXISTS trousch_reward ('
                       'id INTEGER PRIMARY KEY,'
                       'user_id INTEGER NOT NULL,'
                       'amount INTEGER CHECK(amount > 0) NOT NULL,'
                       'ratio REAL DEFAULT 0.5,'
                       'trousch_id INTEGER NOT NULL,'
                       'FOREIGN KEY(trousch_id) REFERENCES trousch(id));')
        cursor.close()
        db.commit()
        db.close()

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

    def __add_karma(self, user_id, amount, dbcursor, ratio=None):
        if ratio is None:
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
        if re.match(r'^[0-9]{18}$', str(user)):
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