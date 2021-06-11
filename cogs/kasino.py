import math
import discord
import os
import sqlite3
from discord.ext import commands
from cogs import bColors


class Kasino(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ccolor = bColors.bColors()
        self.__init_kasino_db()
        self.__init_bets_db()

    # MAIN COMMANDS
    @commands.command(name='openkasino', aliases=['okas'])
    @commands.cooldown(1, 15, type=commands.BucketType.default)
    async def openkasino(self, ctx, question, op_a, op_b):
        if await self.bot.is_restricted(ctx):
            return

        await ctx.message.delete()

        if not await self.__check_openkasino_args(ctx, question, op_a, op_b):
            return
        kasino = await self.__add_kasino(ctx, question=question, option_1=op_a, option_2=op_b)
        self.__create_kasino_backup(kasino)
        await self.__update_kasino(kasino)

    @openkasino.error
    async def openkasino_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.message.delete()
            output = discord.Embed(
                title=f'Openkasino is on cooldown, you can use it in {round(error.retry_after, 2)} seconds',
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.author.send('Incorrect usage of `-openkasino`, missing required arguments. Please refer to `-help openkasino`')
            print(f'{self.ccolor.FAIL}OPENKASINO ERROR{self.ccolor.ENDC}: Incorrect number of arguments passed')
        else:
            output = discord.Embed(
                title=f'Something might\'ve gone wrong with your openkasino.',
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)

    @commands.command(name='refreshkasino', aliases=['rekas'])
    async def refreshkasino(self, ctx, id):
        if await self.bot.is_restricted(ctx):
            return

        await ctx.message.delete()

        if not self.__is_kasino_open(id):
            await ctx.author.send(f'Kasino with ID {id} currently not open.')
            return

        await self.__resend_kasino(ctx, id)
        await self.__update_kasino(id)

    @refreshkasino.error
    async def refreshkasino_error(self, ctx, error):
        await ctx.message.delete()
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.author.send('Argument missing. Retry refreshing as follows `-refreshkasino <kasino_id>`')
        else:
            await ctx.author.send('Unexpected error occurred while refreshing kasino. Try again.')

    @commands.command(name='closekasino', aliases=['clokas'])
    async def closekasino(self, ctx, id, winner):
        if await self.bot.is_restricted(ctx):
            return

        author = ctx.author.display_name
        author_img = ctx.author.avatar_url

        await ctx.message.delete()

        if not self.__is_kasino_open(id):
            await ctx.author.send(f'Kasino with ID {id} currently not open.')
            return

        try:
            winner = int(winner)
        except ValueError:
            await ctx.author.send(f'Winner has to be 1, 2 or 3 (abort)')
            return

        if winner == 3:
            await self.__abort_kasino(id)
        elif winner == 1:
            await self.__win_kasino_a(id)
        elif winner == 2:
            await self.__win_kasino_b(id)
        else:
            await ctx.author.send(f'Winner has to be 1, 2 or 3 (abort)')
            return

        await self.__send_conclusion(ctx, id, winner, author, author_img)
        await self.__remove_kasino(id)

    @closekasino.error
    async def closekasino_error(self, ctx, error):
        await ctx.message.delete()
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.author.send('Argument missing. Retry closing as follows `-closekasino <kasino_id> <1 or 2 or 3 (abort)>`')
        else:
            await ctx.author.send('Unexpected error occurred while closing kasino. Try again.')

    @commands.command(name='lockkasino', aliases=['lokas'])
    async def lockkasino(self, ctx, id):
        if await self.bot.is_restricted(ctx):
            return

        await ctx.message.delete()

        if not self.__is_kasino_open(id):
            await ctx.author.send(f'Kasino with ID {id} currently not open.')
            return

        if self.__is_kasino_locked(id):
            await ctx.author.send('Kasino is already locked.')
            print(f'{self.ccolor.FAIL}LOCKKASINO ERROR{self.ccolor.ENDC}: Kasino already locked')
            return

        self.__lock_kasino(id)
        await self.__update_kasino(id)

    @lockkasino.error
    async def lockkasino_error(self, ctx, error):
        await ctx.message.delete()
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.author.send('Argument missing. Retry locking as follows `-lockkasino <kasino_id>`')
        else:
            await ctx.author.send('Unexpected error occurred while locking kasino. Try again.')

    @commands.command(name='bet', aliases=['b'])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def bet(self, ctx, id, amount, option):
        if await self.bot.is_restricted(ctx):
            return

        await ctx.message.delete()

        self.__init_user(ctx.author.id)

        try:
            if amount == 'all':
                amount = self.__get_balance(ctx.author.id)
            else:
                amount = int(amount)

            id = int(id)
            option = int(option)
        except ValueError:
            output = discord.Embed(
                title='One of the arguments was not a number.',
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
            return

        if not self.__is_kasino_open(id):
            output = discord.Embed(
                title=f'Kasino with ID {id} currently not open.',
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
            return

        if self.__is_kasino_locked(id):
            output = discord.Embed(
                title=f'Kasino with ID {id} is locked.',
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
            return

        if amount < 1:
            output = discord.Embed(
                title='You tried to bet < 1 karma! Silly you!',
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
            return

        if not self.__has_balance(ctx.author.id, amount):
            output = discord.Embed(
                title=f'Not enough balance left in karma account. Currently left: {self.__get_balance(ctx.author.id)}',
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
            return

        if option != 1 and option != 2:
            output = discord.Embed(
                title=f'Wrong usage of the command. Correct usage is `-bet <kasino_id> <amount> <1 or 2>`',
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
            return

        if self.__has_already_bet(ctx.author.id, id):
            if not self.__is_same_option(ctx.author.id, id, option):
                output = discord.Embed(
                    title=f'You can\'t change your choice on the bet with id {id}. No chickening out!',
                    color=discord.Colour.from_rgb(209, 25, 25)
                )
                await ctx.author.send(embed=output)
                return
            await self.__increase_bet(ctx, id, amount, option)
        else:
            await self.__add_bet(ctx, id, amount, option)

        await self.__update_kasino(id)

    @bet.error
    async def bet_error(self, ctx, error):
        await ctx.message.delete()
        if isinstance(error, commands.CommandOnCooldown):
            output = discord.Embed(
                title=f'Betting is on cooldown, you can use it in {round(error.retry_after, 2)} seconds',
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
        elif isinstance(error, commands.MissingRequiredArgument):
            output = discord.Embed(
                title=f'There\'s an argument missing. Correct usage is `-bet <kasino_id> <amount> <1 or 2>`',
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
        else:
            output = discord.Embed(
                title=f'Something might\'ve gone wrong with your bet. Your karma should be fine.',
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
        return

    # HELPER FUNCTIONS
    def __init_user(self, user_id):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute(f'SELECT * FROM users WHERE user_id=?', [user_id])
        user = cursor.fetchone()
        if user is None:
            self.bot.get_cog('Karma').add_user(user_id)
        cursor.close()
        db.close()

    def __is_same_option(self, user_id, kasino_id, option):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute(f'SELECT option FROM bets WHERE kasino_id=? AND user_id=?;', [kasino_id, user_id])
        current_option = cursor.fetchone()[0]
        cursor.close()
        db.close()
        return current_option == option

    def __get_balance(self, user_id):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute(f'SELECT (post_karma + link_karma) AS total FROM users WHERE user_id=?;', [user_id])
        balance = cursor.fetchone()[0]
        cursor.close()
        db.close()
        return balance

    def __has_balance(self, user_id, amount):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute(f'SELECT (post_karma + link_karma) AS total FROM users WHERE user_id=?;', [user_id])
        balance = cursor.fetchone()[0]
        cursor.close()
        db.close()
        return balance >= amount

    async def __add_bet(self, ctx, kasino_id, amount, option):
        user_id = ctx.author.id
        ratio = self.__get_ratio(user_id)

        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()

        # UPDATE
        cursor.execute(f'INSERT INTO bets '
                       f'(user_id, option, amount, ratio, kasino_id) '
                       f'VALUES (?, ?, ?, ?, ?);',
                       [user_id, option, amount, ratio, kasino_id])
        cursor.execute(f'UPDATE kasino SET '
                       f'bets = bets+1, '
                       f'bets_{option} = bets_{option}+1, '
                       f'amount_{option} = amount_{option}+{amount} '
                       f'WHERE id={kasino_id};')

        self.__remove_karma(user_id, amount, ratio, cursor)

        # GET INFO
        cursor.execute(f'SELECT post_karma, link_karma, (post_karma + link_karma) FROM users WHERE user_id=?', [user_id])
        current_karma = cursor.fetchone()

        cursor.close()
        db.commit()
        db.close()

        # INFORM PERSON WHO BET
        output = discord.Embed(
            title=f'**Successfully added bet on option {option}, on kasino with ID {kasino_id} for {amount} karma! Total bet is now: {amount} Karma**',
            color=discord.Colour.from_rgb(52, 79, 235),
            description=f'Remaining karma => Total: {current_karma[2]} Post: {current_karma[0]} | Link: {current_karma[1]}'
        )
        await ctx.author.send(embed=output)
        return

    async def __increase_bet(self, ctx, kasino_id, amount, option):
        user_id = ctx.author.id

        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        # UPDATE
        cursor.execute(f'UPDATE bets SET '
                       f'amount = amount+{amount} '
                       f'WHERE user_id={user_id} AND kasino_id={kasino_id};')
        cursor.execute(f'UPDATE kasino SET '
                       f'amount_{option} = amount_{option}+{amount} '
                       f'WHERE id={kasino_id};')

        self.__remove_karma(user_id, amount, self.__get_ratio(user_id), cursor)

        # GET INFO
        cursor.execute(f'SELECT amount FROM bets WHERE user_id=? AND kasino_id=?', [user_id, kasino_id])
        new_total = cursor.fetchone()[0]
        cursor.execute(f'SELECT post_karma, link_karma, (post_karma + link_karma) FROM users WHERE user_id=?', [user_id])
        current_karma = cursor.fetchone()

        cursor.close()
        db.commit()
        db.close()

        # INFORM PERSON WHO BET
        output = discord.Embed(
            title=f'**Successfully increased bet on option {option}, on kasino with ID {kasino_id} for {amount} karma! Total bet is now: {new_total} Karma**',
            color=discord.Colour.from_rgb(52, 79, 235),
            description=f'Remaining karma => Total: {current_karma[2]} Post: {current_karma[0]} | Link: {current_karma[1]}'
        )
        await ctx.author.send(embed=output)
        return

    def __has_already_bet(self, user_id, kasino_id):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute(f'SELECT * FROM bets WHERE kasino_id=? AND user_id=?;', [kasino_id, user_id])
        entries = cursor.fetchall()
        cursor.close()
        db.close()
        return len(entries) > 0

    def __lock_kasino(self, id):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute(f'UPDATE kasino SET locked=TRUE WHERE id=?', [id])
        cursor.close()
        db.commit()
        db.close()

    async def __remove_kasino(self, id):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()

        cursor.execute(f'SELECT channel_id, message_id FROM kasino WHERE id=?;', [id])
        msg_location = cursor.fetchone()
        kasino_msg = await (await self.bot.fetch_channel(msg_location[0])).fetch_message(msg_location[1])
        await kasino_msg.delete()
        cursor.execute(f'DELETE FROM kasino WHERE id=?;', [id])

        cursor.close()
        db.commit()
        db.close()

    def __is_kasino_open(self, id):
        try:
            id = int(id)
        except ValueError:
            print(f'{self.ccolor.FAIL}ERROR WITH ID{self.ccolor.ENDC}: Provided ID was not a number.')
            return False

        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute(f'SELECT * FROM kasino WHERE id=?;', [id])
        kasino = cursor.fetchone()
        cursor.close()
        db.close()
        if kasino is None:
            return False
        else:
            return True

    def __is_kasino_locked(self, id):
        try:
            id = int(id)
        except ValueError:
            print(f'{self.ccolor.FAIL}ERROR WITH ID{self.ccolor.ENDC}: Provided ID was not a number.')
            return True

        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute(f'SELECT locked FROM kasino WHERE id=?', [id])
        is_locked = cursor.fetchone()[0]
        cursor.close()
        db.close()
        return is_locked

    def __init_kasino_db(self):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS kasino ('
                       'id INTEGER PRIMARY KEY,'
                       'question TEXT NOT NULL,'
                       'option_1 TEXT NOT NULL,'
                       'option_2 TEXT NOT NULL,'
                       'bets INTEGER DEFAULT 0,'
                       'bets_1 INTEGER DEFAULT 0,'
                       'bets_2 INTEGER DEFAULT 0,'
                       'amount_1 INTEGER DEFAULT 0,'
                       'amount_2 INTEGER DEFAULT 0,'
                       'guild_id INTEGER NOT NULL,'
                       'channel_id INTEGER NOT NULL,'
                       'message_id INTEGER NOT NULL,'
                       'locked BOOLEAN DEFAULT FALSE);')
        cursor.close()
        db.commit()
        db.close()

    def __init_bets_db(self):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS bets ('
                       'id INTEGER PRIMARY KEY,'
                       'user_id INTEGER NOT NULL,'
                       'option INTEGER NOT NULL,'
                       'amount INTEGER DEFAULT 0,'
                       'ratio REAL DEFAULT 0.5,'
                       'kasino_id INTEGER NOT NULL,'
                       'FOREIGN KEY(kasino_id) REFERENCES kasino(id));')
        cursor.close()
        db.commit()
        db.close()

    async def __send_conclusion(self, ctx, id, winner, author, author_img):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute(f'SELECT question, option_1, option_2, amount_1, amount_2 FROM kasino WHERE id=?', [id])
        kasino = cursor.fetchone()
        cursor.close()
        db.close()

        total = kasino[3] + kasino[4]
        to_embed = None

        if winner == 1:
            to_embed = discord.Embed(
                title=f':tada: "{kasino[1]}" was correct! :tada:',
                description=f'Question: {kasino[0]}\nIf you\'ve chosen 1, you\'ve just won karma!\nDistributed to the winners: **{total} Karma**',
                color=discord.Colour.from_rgb(52, 79, 235)
            )
        elif winner == 2:
            to_embed = discord.Embed(
                title=f':tada: "{kasino[2]}" was correct! :tada:',
                description=f'Question: {kasino[0]}\nIf you\'ve chosen 2, you\'ve just won karma!\nDistributed to the winners: **{total} Karma**',
                color=discord.Colour.from_rgb(52, 79, 235)
            )
        elif winner == 3:
            to_embed = discord.Embed(
                title=f':game_die: "{kasino[0]}" has been cancelled.',
                description=f'Amount bet will be refunded to each user.\nReturned: {total} Karma',
                color=discord.Colour.from_rgb(52, 79, 235)
            )

        to_embed.set_footer(
            text='as decided by ' + author,
            icon_url=author_img
        )
        to_embed.set_thumbnail(url='https://cdn.betterttv.net/emote/602548a4d47a0b2db8d1a3b8/3x.gif')
        await ctx.send(embed=to_embed)
        return

    async def __abort_kasino(self, id):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()

        cursor.execute(f'SELECT user_id, amount, ratio FROM bets WHERE kasino_id=?', [id])
        entries = cursor.fetchall()
        cursor.execute(f'SELECT question FROM kasino WHERE id=?', [id])
        question = cursor.fetchone()[0]

        cursor.execute(f'DELETE FROM bets WHERE kasino_id=?', [id])

        for bet in entries:
            self.__add_karma(user_id=bet[0], amount=bet[1], ratio=bet[2], dbcursor=cursor)
            user = cursor.execute(f'SELECT post_karma, link_karma FROM users WHERE user_id=?', [bet[0]]).fetchone()
            output = discord.Embed(
                title=f'**You\'ve been refunded {bet[1]} karma.**',
                color=discord.Colour.from_rgb(52, 79, 235),
                description=f'Question was: {question}\n'
                            f'Remaining karma => Total: {user[0] + user[1]} Post: {user[0]} | Link: {user[1]}'
            )
            await (await self.bot.fetch_user(bet[0])).send(embed=output)
        cursor.close()
        db.commit()
        db.close()

    async def __win_kasino_a(self, id):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()

        cursor.execute(f'SELECT user_id, amount, ratio FROM bets WHERE kasino_id=? AND option=1;', [id])
        winners = cursor.fetchall()
        cursor.execute(f'SELECT user_id, amount FROM bets WHERE kasino_id=? AND option=2;', [id])
        losers = cursor.fetchall()
        cursor.execute(f'SELECT amount_1, (amount_1 + amount_2) AS amount FROM kasino WHERE id=?;', [id])
        amounts = cursor.fetchone()
        amount_1 = amounts[0]
        total_amount = amounts[1]
        cursor.execute(f'SELECT question FROM kasino WHERE id=?', [id])
        question = cursor.fetchone()[0]
        cursor.execute(f'DELETE FROM bets WHERE kasino_id=?', [id])

        for bet in winners:
            win_ratio = bet[1]/amount_1
            win_amount = math.ceil(win_ratio * total_amount)

            self.__add_karma(user_id=bet[0], amount=win_amount, ratio=bet[2], dbcursor=cursor)

            user = cursor.execute(f'SELECT post_karma, link_karma FROM users WHERE user_id=?', [bet[0]]).fetchone()
            output = discord.Embed(
                title=f':tada: **You\'ve won {win_amount} karma!** :tada:',
                color=discord.Colour.from_rgb(66, 186, 50),
                description=f'(Of which {bet[1]} you put down on the table)\n'
                            f'Question was: {question}\n'
                            f'New karma balance => Total: {user[0] + user[1]} Post: {user[0]} | Link: {user[1]}'
            )
            await (await self.bot.fetch_user(bet[0])).send(embed=output)
        for bet in losers:
            user = cursor.execute(f'SELECT post_karma, link_karma FROM users WHERE user_id=?', [bet[0]]).fetchone()
            output = discord.Embed(
                title=f':chart_with_downwards_trend: **You\'ve unfortunately lost {bet[1]} karma...** :chart_with_downwards_trend:',
                color=discord.Colour.from_rgb(209, 25, 25),
                description=f'Question was: {question}\n'
                            f'New karma balance => Total: {user[0] + user[1]} Post: {user[0]} | Link: {user[1]}'
            )
            await (await self.bot.fetch_user(bet[0])).send(embed=output)
        cursor.close()
        db.commit()
        db.close()

    async def __win_kasino_b(self, id):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()

        cursor.execute(f'SELECT user_id, amount, ratio FROM bets WHERE kasino_id=? AND option=2;', [id])
        winners = cursor.fetchall()
        cursor.execute(f'SELECT user_id, amount FROM bets WHERE kasino_id=? AND option=1;', [id])
        losers = cursor.fetchall()
        cursor.execute(f'SELECT amount_2, (amount_1 + amount_2) AS amount FROM kasino WHERE id=?;', [id])
        amounts = cursor.fetchone()
        amount_2 = amounts[0]
        total_amount = amounts[1]
        cursor.execute(f'SELECT question FROM kasino WHERE id=?', [id])
        question = cursor.fetchone()[0]
        cursor.execute(f'DELETE FROM bets WHERE kasino_id=?', [id])

        for bet in winners:
            win_ratio = bet[1]/amount_2
            win_amount = math.ceil(win_ratio * total_amount)

            self.__add_karma(user_id=bet[0], amount=win_amount, ratio=bet[2], dbcursor=cursor)

            user = cursor.execute(f'SELECT post_karma, link_karma FROM users WHERE user_id=?', [bet[0]]).fetchone()
            output = discord.Embed(
                title=f':tada: **You\'ve won {win_amount} karma!** :tada:',
                color=discord.Colour.from_rgb(66, 186, 50),
                description=f'(Of which {bet[1]} you put down on the table)\n'
                            f'Question was: {question}\n'
                            f'New karma balance => Total: {user[0] + user[1]} Post: {user[0]} | Link: {user[1]}'
            )
            await (await self.bot.fetch_user(bet[0])).send(embed=output)
        for bet in losers:
            user = cursor.execute(f'SELECT post_karma, link_karma FROM users WHERE user_id=?', [bet[0]]).fetchone()
            output = discord.Embed(
                title=f':chart_with_downwards_trend: **You\'ve unfortunately lost {bet[1]} karma...** :chart_with_downwards_trend:',
                color=discord.Colour.from_rgb(209, 25, 25),
                description=f'Question was: {question}\n'
                            f'New karma balance => Total: {user[0] + user[1]} Post: {user[0]} | Link: {user[1]}'
            )
            await (await self.bot.fetch_user(bet[0])).send(embed=output)
        cursor.close()
        db.commit()
        db.close()

    def __add_karma(self, user_id, amount, ratio, dbcursor):
        post = round(amount * ratio)
        link = amount - post
        self.bot.get_cog('Karma').change_state_user(user_id, 'upvote', 'post', post, dbcursor)
        self.bot.get_cog('Karma').change_state_user(user_id, 'upvote', 'link', link, dbcursor)

    def __remove_karma(self, user_id, amount, ratio, dbcursor):
        post = round(amount * ratio)
        link = amount - post
        self.bot.get_cog('Karma').change_state_user(user_id, 'downvote', 'post', post, dbcursor)
        self.bot.get_cog('Karma').change_state_user(user_id, 'downvote', 'link', link, dbcursor)

    def __get_ratio(self, user_id):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()
        cursor.execute('SELECT post_karma, link_karma FROM users WHERE user_id=?', [user_id])
        karma = cursor.fetchone()
        cursor.close()
        db.close()
        if karma[0]+karma[1] == 0:
            return 0.5
        else:
            return karma[0]/(karma[0]+karma[1])

    async def __check_openkasino_args(self, ctx, question, op_a, op_b):
        if len(op_a) > 227 or len(op_b) > 227:
            await ctx.author.send(f'One of the two options exceeds the maximum allowed 227 characters\n'
                                  f'Option 1: {op_a}\n'
                                  f'Length: {len(op_a)}\n'
                                  f'Option 2: {op_b}\n'
                                  f'Length: {len(op_b)}')
            return False
        if len(question) > 236:
            await ctx.author.send(f'Question exceeds the maximum allowed 236 characters\n'
                                  f'Question was: {question}\n'
                                  f'Length: {len(question)}')
            return False
        return True

    def __create_kasino_backup(self, id):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        backupdb = sqlite3.connect(os.path.abspath(f'./data/backup/kasino_karma_{id}.db'))
        db.backup(backupdb)
        backupdb.commit()
        backupdb.close()
        db.close()

    async def __add_kasino(self, ctx, question, option_1, option_2):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()

        to_embed = discord.Embed(description="Opening kasino, hold on tight...")
        kasino_msg = await ctx.send(embed=to_embed)

        cursor.execute(f'INSERT INTO kasino '
                       f'(question, option_1, option_2, guild_id, channel_id, message_id) '
                       f'VALUES (?, ?, ?, ?, ?, ?);',
                       (question, option_1, option_2, kasino_msg.guild.id, kasino_msg.channel.id, kasino_msg.id))
        cursor.execute('SELECT last_insert_rowid();')
        kasino_id = int(cursor.fetchone()[0])
        cursor.close()
        db.commit()
        db.close()

        return kasino_id

    async def __resend_kasino(self, ctx, id):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()

        # DELETE OLD
        cursor.execute(f'SELECT channel_id, message_id FROM kasino WHERE id=?', [id])
        msg_location = cursor.fetchone()
        kasino_msg = await (await self.bot.fetch_channel(msg_location[0])).fetch_message(msg_location[1])
        await kasino_msg.delete()

        # CREATE NEW
        to_embed = discord.Embed(description="Refreshing kasino, hold on tight...")
        new_kasino_msg = await ctx.send(embed=to_embed)
        cursor.execute(f'UPDATE kasino SET '
                       f'guild_id={ctx.guild.id},'
                       f'channel_id={ctx.channel.id},'
                       f'message_id={new_kasino_msg.id} '
                       f'WHERE id={id}')
        cursor.close()
        db.commit()
        db.close()

    async def __update_kasino(self, kasino_id):
        db = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = db.cursor()

        cursor.execute(f'SELECT * FROM kasino WHERE id=?;', [kasino_id])
        kasino = cursor.fetchone()
        cursor.close()
        db.close()

        kasino_msg = await (await self.bot.fetch_channel(kasino[10])).fetch_message(kasino[11])

        # FIGURE OUT AMOUNTS AND ODDS
        aAmount = kasino[7]
        bAmount = kasino[8]
        if aAmount != 0:
            aOdds = float(aAmount + bAmount) / aAmount
        else:
            aOdds = 1.0
        if bAmount != 0:
            bOdds = float(aAmount + bAmount) / bAmount
        else:
            bOdds = 1.0

        # CREATE MESSAGE
        to_embed = discord.Embed(
            title=f'{"[LOCKED] " if kasino[12] else ""}:game_die: {kasino[1]}',
            description=f'{"The kasino is locked! No more bets are taken in. Time to wait and see..." if kasino[12] else f"The kasino has been opened! Place your bets using `-bet {kasino_id} <amount> <1 or 2>`"}',
            color=discord.Colour.from_rgb(52, 79, 235)
        )
        to_embed.set_footer(text=f'On the table: {aAmount + bAmount} Karma | ID: {kasino[0]}')
        to_embed.set_thumbnail(url='https://cdn.betterttv.net/emote/602548a4d47a0b2db8d1a3b8/3x.gif')
        to_embed.add_field(name=f'**1:** {kasino[2]}',
                           value=f'**Odds:** 1:{round(aOdds, 2)}\n**Pool:** {aAmount} Karma')
        to_embed.add_field(name=f'**2:** {kasino[3]}',
                           value=f'**Odds:** 1:{round(bOdds, 2)}\n**Pool:** {bAmount} Karma')

        await kasino_msg.edit(embed=to_embed)


def setup(bot):
    bot.add_cog(Kasino(bot))
