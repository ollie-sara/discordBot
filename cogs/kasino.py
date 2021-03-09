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

    @commands.command(name='openkasino', aliases=['okas'])
    async def openkasino(self, ctx, *args):
        if await self.bot.is_restricted(ctx):
            return
        karmadb = sqlite3.connect(os.path.abspath('./data/karma.db'))
        backupdb = sqlite3.connect(os.path.abspath('./data/backup/kasino_karma.db'))
        cursor = karmadb.cursor()
        cursor.execute('SELECT * FROM kasino')
        session = cursor.fetchone()

        if session is not None:
            await ctx.author.send('Kasino is currently open, close last session to open a new one.')
            cursor.close()
            karmadb.close()
            return

        if not args:
            await ctx.author.send('Incorrect usage of `§openkasino`. Please refer to `§help openkasino`')
            print(f'{self.ccolor.FAIL}OPENKASINO ERROR{self.ccolor.ENDC}: No arguments passed')
            cursor.close()
            karmadb.close()
            return
        elif len(args) != 3:
            await ctx.author.send('Incorrect usage of `§openkasino`. Please refer to `§help openkasino`')
            print(f'{self.ccolor.FAIL}OPENKASINO ERROR{self.ccolor.ENDC}: Incorrect number of arguments passed')
            cursor.close()
            karmadb.close()
            return

        await ctx.message.delete()
        karmadb.backup(backupdb)
        backupdb.commit()
        backupdb.close()

        question = args[0]
        optionA = args[1]
        optionB = args[2]

        to_embed = discord.Embed()
        kasinomsg = await ctx.send(embed=to_embed)
        cursor.execute(f'INSERT INTO kasino (question, option_a, option_b, guild_id, channel_id, message_id) '
                       f'VALUES("{str(question)}", "{str(optionA)}", "{str(optionB)}", {kasinomsg.guild.id}, {kasinomsg.channel.id}, {kasinomsg.id})')
        cursor.execute(f'CREATE TABLE IF NOT EXISTS a_bets('
                       f'id INTEGER PRIMARY KEY,'
                       f'user_id INTEGER NOT NULL,'
                       f'amount INTEGER DEFAULT 0);')
        cursor.execute(f'CREATE TABLE IF NOT EXISTS b_bets('
                       f'id INTEGER PRIMARY KEY,'
                       f'user_id INTEGER NOT NULL,'
                       f'amount INTEGER DEFAULT 0);')
        cursor.close()
        karmadb.commit()
        karmadb.close()
        await self.update_kasino()
        return

    @commands.command(name='refreshkasino', aliases=['rekas'])
    async def refreshkasino(self, ctx):
        if await self.bot.is_restricted(ctx):
            return

        await ctx.message.delete()
        karmadb = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = karmadb.cursor()
        cursor.execute('SELECT * FROM kasino')
        session = cursor.fetchone()

        if session is None:
            await ctx.author.send('Currently, no kasino is open. Use `§openkasino "<question>" "<option A>" "<option B>"` to start a bet.')
            print(f'{self.ccolor.FAIL}REFRESHKASINO ERROR{self.ccolor.ENDC}: No kasino open')
            cursor.close()
            karmadb.close()
            return
        try:
            kmsg = await (await self.bot.fetch_channel(session[10])).fetch_message(session[11])
            await kmsg.delete()
        except Exception:
            pass

        to_embed = discord.Embed()
        kasinomsg = await ctx.send(embed=to_embed)
        cursor.execute(f'UPDATE kasino SET guild_id={kasinomsg.guild.id}, channel_id={kasinomsg.channel.id}, message_id={kasinomsg.id}')
        cursor.close()
        karmadb.commit()
        karmadb.close()
        await self.update_kasino()
        return

    @commands.command(name='lockkasino', aliases=['lokas'])
    async def lockkasino(self, ctx):
        if await self.bot.is_restricted(ctx):
            return

        await ctx.message.delete()
        karmadb = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = karmadb.cursor()
        cursor.execute('SELECT * FROM kasino')
        session = cursor.fetchone()

        if session is None:
            await ctx.author.send('Currently, no kasino is open. Use `§openkasino "<question>" "<option A>" "<option B>"` to start a bet.')
            print(f'{self.ccolor.FAIL}LOCKKASINO ERROR{self.ccolor.ENDC}: No kasino open')
            cursor.close()
            karmadb.close()
            return
        if session[12]:
            await ctx.author.send('Kasino is already locked.')
            print(f'{self.ccolor.FAIL}LOCKKASINO ERROR{self.ccolor.ENDC}: Kasino already locked')
            cursor.close()
            karmadb.close()
            return

        cursor.execute(f'UPDATE kasino SET locked=TRUE')
        cursor.close()
        karmadb.commit()
        karmadb.close()
        await self.update_kasino()
        return

    @commands.command(name='closekasino', aliases=['clokas'])
    async def closekasino(self, ctx, arg):
        if await self.bot.is_restricted(ctx):
            return

        auth = ctx.author.display_name
        auth_img = ctx.author.avatar_url

        await ctx.message.delete()

        karmadb = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = karmadb.cursor()
        cursor.execute('SELECT * FROM kasino')
        session = cursor.fetchone()

        if session is None:
            await ctx.author.send('Currently, no kasino is open. Use `§openkasino "<question>" "<option A>" "<option B>"` to start a bet.')
            print(f'{self.ccolor.FAIL}CLOSEKASINO ERROR{self.ccolor.ENDC}: No kasino open')
            cursor.close()
            karmadb.close()
            return

        if arg is None:
            await ctx.author.send('Incorrect usage of `§closekasino`. Please refer to `§help closekasino`')
            print(f'{self.ccolor.FAIL}CLOSEKASINO ERROR{self.ccolor.ENDC}: No arguments passed')
            cursor.close()
            karmadb.close()
            return
        if int(arg) < 1 or int(arg) > 3:
            await ctx.author.send('Incorrect usage of `§closekasino`. Please refer to `§help closekasino`')
            print(f'{self.ccolor.FAIL}CLOSEKASINO ERROR{self.ccolor.ENDC}: Argument is not 1, 2 or 3')
            cursor.close()
            karmadb.close()
            return

        to_embed = None
        cursor.execute('SELECT user_id, amount FROM a_bets')
        a_bets = cursor.fetchall()
        cursor.execute('SELECT user_id, amount FROM b_bets')
        b_bets = cursor.fetchall()

        # ABORT AND RETURN
        if int(arg) == 3:
            for b in a_bets:
                postkarma = cursor.execute(f'SELECT post_karma FROM users WHERE user_id={b[0]}').fetchone()[0]
                linkkarma = cursor.execute(f'SELECT link_karma FROM users WHERE user_id={b[0]}').fetchone()[0]
                if postkarma + linkkarma == 0:
                    postToAll = 0.5
                else:
                    postToAll = float(postkarma / (postkarma + linkkarma))
                postAmount = round(float(b[1] * postToAll))
                self.bot.get_cog('Karma').change_state_user(b[0], 'upvote', 'post', postAmount)
                self.bot.get_cog('Karma').change_state_user(b[0], 'upvote', 'link', b[1]-postAmount)
                user = cursor.execute(f'SELECT post_karma, link_karma FROM users WHERE user_id={b[0]}').fetchone()
                output = discord.Embed(
                    title=f'**You\'ve been refunded {b[1]} karma.**',
                    color=discord.Colour.from_rgb(52, 79, 235),
                    description=f'Remaining karma => Total: {user[0]+user[1]} Post: {user[0]} | Link: {user[1]}'
                )
                await (await self.bot.fetch_user(b[0])).send(embed=output)
            for b in b_bets:
                postkarma = cursor.execute(f'SELECT post_karma FROM users WHERE user_id={b[0]}').fetchone()[0]
                linkkarma = cursor.execute(f'SELECT link_karma FROM users WHERE user_id={b[0]}').fetchone()[0]
                if postkarma + linkkarma == 0:
                    postToAll = 0.5
                else:
                    postToAll = float(postkarma / (postkarma + linkkarma))
                postAmount = round(float(b[1] * postToAll))
                self.bot.get_cog('Karma').change_state_user(b[0], 'upvote', 'post', postAmount)
                self.bot.get_cog('Karma').change_state_user(b[0], 'upvote', 'link', b[1] - postAmount)
                user = cursor.execute(f'SELECT post_karma, link_karma FROM users WHERE user_id={b[0]}').fetchone()
                output = discord.Embed(
                    title=f'**You\'ve been refunded {b[1]} karma.**',
                    color=discord.Colour.from_rgb(52, 79, 235),
                    description=f'Remaining karma => Total: {user[0]+user[1]} Post: {user[0]} | Link: {user[1]}'
                )
                await (await self.bot.fetch_user(b[0])).send(embed=output)
            to_embed = discord.Embed(
                title=f':game_die: "{session[1]}" has been cancelled.',
                description=f'Amount bet will be refunded to each user.\nReturned: {session[7] + session[8]} Karma',
                color=discord.Colour.from_rgb(52, 79, 235)
            )
        # OPTION 1 WINS
        elif int(arg) == 1:
            for b in a_bets:
                postkarma = cursor.execute(f'SELECT post_karma FROM users WHERE user_id={b[0]}').fetchone()[0]
                linkkarma = cursor.execute(f'SELECT link_karma FROM users WHERE user_id={b[0]}').fetchone()[0]
                if session[8] == 0:
                    totalWon = b[1]
                else:
                    totalWon = b[1]+ math.ceil((b[1]/ session[7]) * session[8])
                if postkarma + linkkarma == 0:
                    postToAll = 0.5
                else:
                    postToAll = float(postkarma / (postkarma + linkkarma))
                postAmount = round(float(totalWon * postToAll))
                self.bot.get_cog('Karma').change_state_user(b[0], 'upvote', 'post', postAmount)
                self.bot.get_cog('Karma').change_state_user(b[0], 'upvote', 'link', totalWon - postAmount)
                user = cursor.execute(f'SELECT post_karma, link_karma FROM users WHERE user_id={b[0]}').fetchone()
                output = discord.Embed(
                    title=f':tada: **You\'ve won {totalWon} karma!** :tada:',
                    color=discord.Colour.from_rgb(66, 186, 50),
                    description=f'(Of which {b[1]} you put down on the table)\nNew karma balance => Total: {user[0]+user[1]} Post: {user[0]} | Link: {user[1]}'
                )
                await (await self.bot.fetch_user(b[0])).send(embed=output)
            for b in b_bets:
                user = cursor.execute(f'SELECT post_karma, link_karma FROM users WHERE user_id={b[0]}').fetchone()
                output = discord.Embed(
                    title=f':chart_with_downwards_trend: **You\'ve unfortunately lost {b[1]} karma...** :chart_with_downwards_trend:',
                    color=discord.Colour.from_rgb(209, 25, 25),
                    description=f'New karma balance => Total: {user[0]+user[1]} Post: {user[0]} | Link: {user[1]}'
                )
                await (await self.bot.fetch_user(b[0])).send(embed=output)
            to_embed = discord.Embed(
                title=f':tada: "{session[2]}" was correct! :tada:',
                description=f'Question: {session[1]}\nIf you\'ve chosen 1, you\'ve just won karma!\nDistributed to the winners: **{session[7] + session[8]} Karma**',
                color=discord.Colour.from_rgb(52, 79, 235)
            )
        # OPTION 2 WINS
        elif int(arg) == 2:
            for b in b_bets:
                postkarma = cursor.execute(f'SELECT post_karma FROM users WHERE user_id={b[0]}').fetchone()[0]
                linkkarma = cursor.execute(f'SELECT link_karma FROM users WHERE user_id={b[0]}').fetchone()[0]
                if session[8] == 0:
                    totalWon = b[1]
                else:
                    totalWon = b[1] + math.ceil((b[1] / session[8]) * session[7])
                if postkarma + linkkarma == 0:
                    postToAll = 0.5
                else:
                    postToAll = float(postkarma / (postkarma + linkkarma))
                postAmount = round(float(totalWon*postToAll))
                self.bot.get_cog('Karma').change_state_user(b[0], 'upvote', 'post', postAmount)
                self.bot.get_cog('Karma').change_state_user(b[0], 'upvote', 'link', totalWon-postAmount)
                user = cursor.execute(f'SELECT post_karma, link_karma FROM users WHERE user_id={b[0]}').fetchone()
                output = discord.Embed(
                    title=f':tada: **You\'ve won {totalWon} karma!** :tada:',
                    color=discord.Colour.from_rgb(66, 186, 50),
                    description=f'(Of which {b[1]} you put down on the table)\nNew karma balance => Total: {user[0]+user[1]} Post: {user[0]} | Link: {user[1]}'
                )
                await (await self.bot.fetch_user(b[0])).send(embed=output)
            for b in a_bets:
                user = cursor.execute(f'SELECT post_karma, link_karma FROM users WHERE user_id={b[0]}').fetchone()
                output = discord.Embed(
                    title=f':chart_with_downwards_trend: **You\'ve unfortunately lost {b[1]} karma...** :chart_with_downwards_trend:',
                    color=discord.Colour.from_rgb(209, 25, 25),
                    description=f'New karma balance => Total: {user[0]+user[1]} Post: {user[0]} | Link: {user[1]}'
                )
                await (await self.bot.fetch_user(b[0])).send(embed=output)
            to_embed = discord.Embed(
                title=f':tada: "{session[3]}" was correct! :tada:',
                description=f'Question: {session[1]}\nIf you\'ve chosen 2, you\'ve just won karma!\nDistributed to the winners: **{session[7] + session[8]} Karma**',
                color=discord.Colour.from_rgb(52, 79, 235)
            )
        to_embed.set_footer(
            text='as decided by ' + auth,
            icon_url=auth_img
        )
        kmsg = await (await self.bot.fetch_channel(session[10])).fetch_message(session[11])
        await kmsg.delete()
        to_embed.set_thumbnail(url='https://cdn.betterttv.net/emote/602548a4d47a0b2db8d1a3b8/3x.gif')
        await ctx.send(embed=to_embed, delete_after=30)
        cursor.execute("DELETE FROM kasino")
        cursor.execute("DROP TABLE IF EXISTS a_bets")
        cursor.execute("DROP TABLE IF EXISTS b_bets")
        cursor.close()
        karmadb.commit()
        karmadb.close()
        return

    @commands.command(name='bet', aliases=['b'])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def bet(self, ctx, *args):
        if await self.bot.is_restricted(ctx):
            return

        await ctx.message.delete()
        karmadb = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = karmadb.cursor()
        cursor.execute('SELECT * FROM kasino')
        session = cursor.fetchone()

        if session is None:
            output = discord.Embed(
                title='There is currently no open kasino running. You\'ll have to wait till next time.',
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
            cursor.close()
            karmadb.close()
            return

        if args is None:
            output = discord.Embed(
                title='You didn\'t specify an amount. Write `§bet <amount> <1 or 2>` in chat',
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
            cursor.close()
            karmadb.close()
            return

        if len(args) == 1:
            output = discord.Embed(
                title='You didn\'t specify an option. Write `§bet <amount> <1 or 2>` in chat',
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
            cursor.close()
            karmadb.close()
            return

        if len(args) > 2:
            output = discord.Embed(
                title='You passed an incorrect number of arguments. Write `§bet <amount> <1 or 2>` in chat',
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
            cursor.close()
            karmadb.close()
            return

        if session[12]:
            output = discord.Embed(
                title='Kasino is locked! Taking in no more bets.',
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
            cursor.close()
            karmadb.close()
            return

        cursor.execute(f'SELECT * FROM a_bets WHERE user_id={ctx.author.id}')
        a_bets = cursor.fetchone()
        cursor.execute(f'SELECT * FROM b_bets WHERE user_id={ctx.author.id}')
        b_bets = cursor.fetchone()

        alreadyBet = 0
        alreadyBetAmount = 0
        if a_bets is not None:
            alreadyBet = 1
            alreadyBetAmount = a_bets[2]
        elif b_bets is not None:
            alreadyBet = 2
            alreadyBetAmount = b_bets[2]

        amount = max(int(args[0]), 0)
        option = int(args[1])

        if amount == 0:
            output = discord.Embed(
                title='You tried to bet <= 0 karma! Silly you!',
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
            cursor.close()
            karmadb.close()
            return

        if option == alreadyBet and amount > alreadyBetAmount:
            increase = amount - alreadyBetAmount
            postkarma = cursor.execute(f'SELECT post_karma FROM users WHERE user_id={ctx.author.id}').fetchone()[0]
            linkkarma = cursor.execute(f'SELECT link_karma FROM users WHERE user_id={ctx.author.id}').fetchone()[0]

            postToAll = float(postkarma / (postkarma + linkkarma))

            betpost = min(round(increase * postToAll), postkarma)
            betlink = min(increase - betpost, linkkarma)

            if betlink + betpost == 0:
                output = discord.Embed(
                    title='Couldn\'t increase your bet because you are broke! Try again after you earn some karma.',
                    color=discord.Colour.from_rgb(209, 25, 25)
                )
                await ctx.author.send(embed=output)
                cursor.close()
                karmadb.close()
                return

            if (postkarma - betpost)+(linkkarma - betlink) == 0:
                madman = discord.Embed(
                    title=f':bangbang: **{ctx.author.name if ctx.author.nick is None else ctx.author.nick} is a madman!** :bangbang:',
                    description=f'They bet all of their {postkarma+linkkarma} karma!',
                    color=discord.Colour.from_rgb(52, 79, 235)
                )
                madman.set_thumbnail(url=ctx.author.avatar_url)
                madman.set_footer(text='Wish them luck!')
                await ctx.send(embed=madman, delete_after=20)

            if option == 1:
                cursor.execute(f'UPDATE a_bets SET amount={alreadyBetAmount+betlink+betpost} WHERE user_id={ctx.author.id}')
                output = discord.Embed(
                    title=f'**Successfully increased bet on option {option} for {betpost + betlink} karma! Total bet is now: {alreadyBetAmount+betlink+betpost} Karma**',
                    color=discord.Colour.from_rgb(52, 79, 235),
                    description=f'Remaining karma => Total: {(postkarma - betpost)+(linkkarma - betlink)} Post: {postkarma - betpost} | Link: {linkkarma - betlink}'
                )
                await ctx.author.send(embed=output)
            elif option == 2:
                cursor.execute(f'UPDATE b_bets SET amount={alreadyBetAmount+betlink+betpost} WHERE user_id={ctx.author.id}')
                output = discord.Embed(
                    title=f'**Successfully increased bet on option {option} for {betpost + betlink} karma! Total bet is now: {alreadyBetAmount+betlink+betpost} Karma**',
                    color=discord.Colour.from_rgb(52, 79, 235),
                    description=f'Remaining karma => Total: {(postkarma - betpost)+(linkkarma - betlink)} Post: {postkarma - betpost} | Link: {linkkarma - betlink}'
                )
                await ctx.author.send(embed=output)
            else:
                output = discord.Embed(
                    title='Something was wrong with your bet. Try again with `§bet <amount> <1 or 2>`',
                    color=discord.Colour.from_rgb(209, 25, 25)
                )
                await ctx.author.send(embed=output)
                cursor.close()
                karmadb.close()
                return
        else:
            if alreadyBet != 0:
                output = discord.Embed(
                    title=f'You already bet {alreadyBetAmount} Karma on option {alreadyBet}. You may increase it using `§bet <amount over {alreadyBetAmount}> {alreadyBet}`',
                    color=discord.Colour.from_rgb(209, 25, 25)
                )
                await ctx.author.send(embed=output)
                cursor.close()
                karmadb.close()
                return

            postkarma = cursor.execute(f'SELECT post_karma FROM users WHERE user_id={ctx.author.id}').fetchone()[0]
            linkkarma = cursor.execute(f'SELECT link_karma FROM users WHERE user_id={ctx.author.id}').fetchone()[0]

            postToAll = float(postkarma / (postkarma + linkkarma))

            betpost = min(round(amount * postToAll), postkarma)
            betlink = min(amount - betpost, linkkarma)

            if betlink+betpost == 0:
                await ctx.author.send(f'Couldn\'t place a bet because you are broke! Try again after you earn some karma.')
                cursor.close()
                karmadb.close()
                return

            if (postkarma - betpost) + (linkkarma - betlink) == 0:
                madman = discord.Embed(
                    title=f':bangbang: **{ctx.author.name if ctx.author.nick is None else ctx.author.nick} is a madman!** :bangbang:',
                    description=f'They bet all of their {postkarma + linkkarma} karma!',
                    color=discord.Colour.from_rgb(52, 79, 235)
                )
                madman.set_thumbnail(url=ctx.author.avatar_url)
                madman.set_footer(text='Wish them luck!')
                await ctx.send(embed=madman, delete_after=20)

            cursor.execute(f'UPDATE kasino SET bets=bets+1')

            if option == 1:
                cursor.execute(f'INSERT INTO a_bets (user_id, amount) VALUES({ctx.author.id},{betlink+betpost})')
                cursor.execute(f'UPDATE kasino SET bets_a=bets_a+1')
                output = discord.Embed(
                    title=f'**Successfully placed bet on option {option} for {betpost+betlink} karma!**',
                    color=discord.Colour.from_rgb(52, 79, 235),
                    description=f'Remaining karma => Total: {(postkarma - betpost)+(linkkarma - betlink)} Post: {postkarma-betpost} | Link: {linkkarma-betlink}'
                )
                await ctx.author.send(embed=output)
            elif option == 2:
                cursor.execute(f'INSERT INTO b_bets (user_id, amount) VALUES({ctx.author.id},{betlink+betpost})')
                cursor.execute(f'UPDATE kasino SET bets_b=bets_b+1')
                output = discord.Embed(
                    title=f'**Successfully placed bet on option {option} for {betpost + betlink} karma!**',
                    color=discord.Colour.from_rgb(52, 79, 235),
                    description=f'Remaining karma => Total: {(postkarma - betpost) + (linkkarma - betlink)} Post: {postkarma - betpost} | Link: {linkkarma - betlink}'
                )
                await ctx.author.send(embed=output)
            else:
                output = discord.Embed(
                    title=f'Something was wrong with your bet. Try again with `§bet <amount> <1 or 2>`',
                    color=discord.Colour.from_rgb(209, 25, 25)
                )
                await ctx.author.send(embed=output)
                cursor.close()
                karmadb.close()
                return

        if option == 1:
            cursor.execute(f'UPDATE kasino SET amount_a=amount_a+{betpost+betlink}')
        elif option == 2:
            cursor.execute(f'UPDATE kasino SET amount_b=amount_b+{betpost + betlink}')
        cursor.close()
        karmadb.commit()
        karmadb.close()

        self.bot.get_cog('Karma').change_state_user(ctx.author.id, 'downvote', 'post', betpost)
        self.bot.get_cog('Karma').change_state_user(ctx.author.id, 'downvote', 'link', betlink)

        await self.update_kasino()
        return

    @bet.error
    async def bet_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.message.delete()
            output = discord.Embed(
                title=f'Betting is on cooldown, you can use it in {round(error.retry_after, 2)} seconds',
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

    async def update_kasino(self):
        karmadb = sqlite3.connect(os.path.abspath('./data/karma.db'))
        cursor = karmadb.cursor()
        cursor.execute('SELECT * FROM kasino')
        session = cursor.fetchone()

        kasinomsg = await (await self.bot.fetch_channel(session[10])).fetch_message(session[11])

        aAmount = session[7]
        bAmount = session[8]
        if aAmount != 0:
            aOdds = float(aAmount+bAmount)/aAmount
        else:
            aOdds = 1.0
        if bAmount != 0:
            bOdds = float(aAmount+bAmount)/bAmount
        else:
            bOdds = 1.0

        to_embed = discord.Embed(
            title=f'{"[LOCKED] " if session[12] else ""}:game_die: {session[1]}',
            description=f'**On the table:** {aAmount+bAmount} Karma',
            color=discord.Colour.from_rgb(52, 79, 235)
        )

        footertext = ''
        if session[12]:
            footertext = 'The kasino is locked! No more bets are taken in. Time to wait and see...'
        else:
            footertext = 'The kasino has been opened! Place your bets using `§bet <amount> <1 or 2>`'

        to_embed.set_footer(text=footertext)
        to_embed.set_thumbnail(url='https://cdn.betterttv.net/emote/602548a4d47a0b2db8d1a3b8/3x.gif')
        to_embed.add_field(name=f'**1:** {session[2]}', value=f'**Odds:** 1:{round(aOdds,2)}\n**Pool:** {aAmount} Karma')
        to_embed.add_field(name=f'**2:** {session[3]}', value=f'**Odds:** 1:{round(bOdds,2)}\n**Pool:** {bAmount} Karma')

        await kasinomsg.edit(embed=to_embed)
        cursor.close()
        karmadb.close()
        return


def setup(bot):
    bot.add_cog(Kasino(bot))
