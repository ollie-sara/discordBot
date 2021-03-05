import math

from data.kasino import KasinoSession
import discord
import json
import os
from discord.ext import commands
from cogs import bColors


class Kasino(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ccolor = bColors.bColors()
        self.kasino = self.load_session()

    @commands.command(name='openkasino', aliases=['okas'])
    async def openkasino(self, ctx, *args):
        if await self.bot.is_restricted(ctx):
            return

        if self.kasino is not None:
            await ctx.author.send('Kasino is currently open, close last session to open a new one.')
            return

        if not args:
            await ctx.author.send('Incorrect usage of `§openkasino`. Please refer to `§help openkasino`')
            print(f'{self.ccolor.FAIL}OPENKASINO ERROR{self.ccolor.ENDC}: No arguments passed')
            return
        elif len(args) != 3:
            await ctx.author.send('Incorrect usage of `§openkasino`. Please refer to `§help openkasino`')
            print(f'{self.ccolor.FAIL}OPENKASINO ERROR{self.ccolor.ENDC}: Incorrect number of arguments passed')
            return

        await ctx.message.delete()

        question = args[0]
        optionA = args[1]
        optionB = args[2]

        to_embed = discord.Embed()
        kasinomsg = await ctx.send(embed=to_embed)
        self.kasino = KasinoSession.KasinoSession(question, optionA, optionB, 0, 0, 0, kasinomsg.guild.id, kasinomsg.channel.id, kasinomsg.id)
        await self.update_kasino()
        self.save_session()
        return

    @commands.command(name='refreshkasino', aliases=['rekas'])
    async def refreshkasino(self, ctx):
        if await self.bot.is_restricted(ctx):
            return

        await ctx.message.delete()
        if self.kasino is None:
            await ctx.author.send('Currently, no kasino is open. Use `§openkasino "<question>" "<option A>" "<option B>"` to start a bet.')
            print(f'{self.ccolor.FAIL}REFRESHKASINO ERROR{self.ccolor.ENDC}: No kasino open')
            return

        kmsg = await (await self.bot.fetch_channel(self.kasino.channelID)).fetch_message(self.kasino.messageID)
        await kmsg.delete()
        to_embed = discord.Embed()
        kasinomsg = await ctx.send(embed=to_embed)
        self.kasino.guildID = kasinomsg.guild.id
        self.kasino.channelID = kasinomsg.channel.id
        self.kasino.messageID = kasinomsg.id
        await self.update_kasino()
        self.save_session()
        return

    @commands.command(name='lockkasino', aliases=['lokas'])
    async def lockkasino(self, ctx):
        if await self.bot.is_restricted(ctx):
            return

        await ctx.message.delete()

        if self.kasino is None:
            await ctx.author.send('Currently, no kasino is open. Use `§openkasino "<question>" "<option A>" "<option B>"` to start a bet.')
            print(f'{self.ccolor.FAIL}LOCKKASINO ERROR{self.ccolor.ENDC}: No kasino open')
            return
        if self.kasino.locked:
            await ctx.author.send('Kasino is already locked.')
            print(f'{self.ccolor.FAIL}LOCKKASINO ERROR{self.ccolor.ENDC}: No kasino open')
            return

        self.kasino.locked = True
        await self.update_kasino()
        self.save_session()
        return

    @commands.command(name='closekasino', aliases=['clokas'])
    async def closekasino(self, ctx, arg):
        if await self.bot.is_restricted(ctx):
            return

        auth = ctx.author.display_name
        auth_img = ctx.author.avatar_url

        await ctx.message.delete()

        if self.kasino is None:
            await ctx.author.send('Currently, no kasino is open. Use `§openkasino "<question>" "<option A>" "<option B>"` to start a bet.')
            print(f'{self.ccolor.FAIL}CLOSEKASINO ERROR{self.ccolor.ENDC}: No kasino open')
            return

        if arg is None:
            await ctx.author.send('Incorrect usage of `§closekasino`. Please refer to `§help closekasino`')
            print(f'{self.ccolor.FAIL}CLOSEKASINO ERROR{self.ccolor.ENDC}: No arguments passed')
            return
        if int(arg) < 1 or int(arg) > 3:
            await ctx.author.send('Incorrect usage of `§closekasino`. Please refer to `§help closekasino`')
            print(f'{self.ccolor.FAIL}CLOSEKASINO ERROR{self.ccolor.ENDC}: Argument is not 1, 2 or 3')
            return


        karmaSystem = self.bot.get_cog('Karma')
        to_embed = None

        # ABORT AND RETURN
        if int(arg) == 3:
            for b in self.kasino.optionABets.values():
                postkarma = karmaSystem.users[str(b.userID)].post_karma
                linkkarma = karmaSystem.users[str(b.userID)].link_karma
                if postkarma + linkkarma == 0:
                    postToAll = 0.5
                else:
                    postToAll = float(postkarma / (postkarma + linkkarma))
                postAmount = round(float(b.amount * postToAll))
                karmaSystem.change_state_user(str(b.userID), 'upvote', 'post', postAmount)
                karmaSystem.change_state_user(str(b.userID), 'upvote', 'link', b.amount-postAmount)
                output = discord.Embed(
                    title=f'**You\'ve been refunded {b.amount} karma.**',
                    color=discord.Colour.from_rgb(52, 79, 235),
                    description=f'Remaining karma => Total: {karmaSystem.users[str(b.userID)].post_karma+karmaSystem.users[str(b.userID)].link_karma} Post: {karmaSystem.users[str(b.userID)].post_karma} | Link: {karmaSystem.users[str(b.userID)].link_karma}'
                )
                await (await self.bot.fetch_user(b.userID)).send(embed=output)
            for b in self.kasino.optionBBets.values():
                postkarma = karmaSystem.users[str(b.userID)].post_karma
                linkkarma = karmaSystem.users[str(b.userID)].link_karma
                if postkarma + linkkarma == 0:
                    postToAll = 0.5
                else:
                    postToAll = float(postkarma / (postkarma + linkkarma))
                postAmount = round(float(b.amount * postToAll))
                karmaSystem.change_state_user(str(b.userID), 'upvote', 'post', postAmount)
                karmaSystem.change_state_user(str(b.userID), 'upvote', 'link', b.amount-postAmount)
                output = discord.Embed(
                    title=f'**You\'ve been refunded {b.amount} karma.**',
                    color=discord.Colour.from_rgb(52, 79, 235),
                    description=f'Remaining karma => Total: {karmaSystem.users[str(b.userID)].post_karma+karmaSystem.users[str(b.userID)].link_karma} Post: {karmaSystem.users[str(b.userID)].post_karma} | Link: {karmaSystem.users[str(b.userID)].link_karma}'
                )
                await (await self.bot.fetch_user(b.userID)).send(embed=output)
            to_embed = discord.Embed(
                title=f':game_die: "{self.kasino.question}" has been cancelled.',
                description=f'Amount bet will be refunded to each user.\nReturned: {self.kasino.amountA + self.kasino.amountB} Karma',
                color=discord.Colour.from_rgb(52, 79, 235)
            )
        # OPTION 1 WINS
        elif int(arg) == 1:
            for b in self.kasino.optionABets.values():
                postkarma = karmaSystem.users[str(b.userID)].post_karma
                linkkarma = karmaSystem.users[str(b.userID)].link_karma
                if self.kasino.amountB == 0:
                    totalWon = b.amount
                else:
                    totalWon = b.amount + math.ceil((b.amount / self.kasino.amountA) * self.kasino.amountB)
                if postkarma + linkkarma == 0:
                    postToAll = 0.5
                else:
                    postToAll = float(postkarma / (postkarma + linkkarma))
                postAmount = round(float(totalWon * postToAll))
                karmaSystem.change_state_user(str(b.userID), 'upvote', 'post', postAmount)
                karmaSystem.change_state_user(str(b.userID), 'upvote', 'link', totalWon - postAmount)
                output = discord.Embed(
                    title=f':tada: **You\'ve won {totalWon} karma!** :tada:',
                    color=discord.Colour.from_rgb(66, 186, 50),
                    description=f'(Of which {b.amount} you put down on the table)\nNew karma balance => Total: {karmaSystem.users[str(b.userID)].post_karma+karmaSystem.users[str(b.userID)].link_karma} Post: {karmaSystem.users[str(b.userID)].post_karma} | Link: {karmaSystem.users[str(b.userID)].link_karma}'
                )
                await (await self.bot.fetch_user(b.userID)).send(embed=output)
            for b in self.kasino.optionBBets.values():
                output = discord.Embed(
                    title=f':chart_with_downwards_trend: **You\'ve unfortunately lost {b.amount} karma...** :chart_with_downwards_trend:',
                    color=discord.Colour.from_rgb(209, 25, 25),
                    description=f'New karma balance => Total: {karmaSystem.users[str(b.userID)].post_karma+karmaSystem.users[str(b.userID)].link_karma} Post: {karmaSystem.users[str(b.userID)].post_karma} | Link: {karmaSystem.users[str(b.userID)].link_karma}'
                )
                await (await self.bot.fetch_user(b.userID)).send(embed=output)
            to_embed = discord.Embed(
                title=f':tada: "{self.kasino.optionA}" was correct! :tada:',
                description=f'Question: {self.kasino.question}\nIf you\'ve chosen 1, you\'ve just won karma!\nDistributed to the winners: **{self.kasino.amountA + self.kasino.amountB} Karma**',
                color=discord.Colour.from_rgb(52, 79, 235)
            )
        # OPTION 2 WINS
        elif int(arg) == 2:
            for b in self.kasino.optionBBets.values():
                postkarma = karmaSystem.users[str(b.userID)].post_karma
                linkkarma = karmaSystem.users[str(b.userID)].link_karma
                if self.kasino.amountB == 0:
                    totalWon = b.amount
                else:
                    totalWon = b.amount + math.ceil((b.amount / self.kasino.amountB) * self.kasino.amountA)
                if postkarma + linkkarma == 0:
                    postToAll = 0.5
                else:
                    postToAll = float(postkarma / (postkarma + linkkarma))
                postAmount = round(float(totalWon*postToAll))
                karmaSystem.change_state_user(str(b.userID), 'upvote', 'post', postAmount)
                karmaSystem.change_state_user(str(b.userID), 'upvote', 'link', totalWon-postAmount)
                output = discord.Embed(
                    title=f':tada: **You\'ve won {totalWon} karma!** :tada:',
                    color=discord.Colour.from_rgb(66, 186, 50),
                    description=f'(Of which {b.amount} you put down on the table)\nNew karma balance => Total: {karmaSystem.users[str(b.userID)].post_karma+karmaSystem.users[str(b.userID)].link_karma} Post: {karmaSystem.users[str(b.userID)].post_karma} | Link: {karmaSystem.users[str(b.userID)].link_karma}'
                )
                await (await self.bot.fetch_user(b.userID)).send(embed=output)
            for b in self.kasino.optionABets.values():
                output = discord.Embed(
                    title=f':chart_with_downwards_trend: **You\'ve unfortunately lost {b.amount} karma...** :chart_with_downwards_trend:',
                    color=discord.Colour.from_rgb(209, 25, 25),
                    description=f'New karma balance => Total: {karmaSystem.users[str(b.userID)].post_karma+karmaSystem.users[str(b.userID)].link_karma} Post: {karmaSystem.users[str(b.userID)].post_karma} | Link: {karmaSystem.users[str(b.userID)].link_karma}'
                )
                await (await self.bot.fetch_user(b.userID)).send(embed=output)
            to_embed = discord.Embed(
                title=f':tada: "{self.kasino.optionB}" was correct! :tada:',
                description=f'Question: {self.kasino.question}\nIf you\'ve chosen 2, you\'ve just won karma!\nDistributed to the winners: **{self.kasino.amountA + self.kasino.amountB} Karma**',
                color=discord.Colour.from_rgb(52, 79, 235)
            )
        to_embed.set_footer(
            text='as decided by ' + auth,
            icon_url=auth_img
        )
        kmsg = await (await self.bot.fetch_channel(self.kasino.channelID)).fetch_message(self.kasino.messageID)
        await kmsg.delete()
        to_embed.set_thumbnail(url='https://cdn.betterttv.net/emote/602548a4d47a0b2db8d1a3b8/3x.gif')
        await ctx.send(embed=to_embed, delete_after=30)
        os.remove(os.path.abspath('./data/kasino/session.json'))
        self.kasino = None
        karmaSystem.force_save()
        return

    @commands.command(name='bet', aliases=['b'])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def bet(self, ctx, *args):
        if await self.bot.is_restricted(ctx):
            return

        await ctx.message.delete()

        if self.kasino is None:
            await ctx.author.send('There is currently no open kasino running. You\'ll have to wait till next time.')
            return

        if args is None:
            await ctx.author.send('You didn\'t specify an amount. Write `§bet <amount> <1 or 2>` in chat')
            return

        if len(args) == 1:
            await ctx.author.send('You didn\'t specify an option. Write `§bet <amount> <1 or 2>` in chat')
            return

        if len(args) > 2:
            await ctx.author.send('You passed an incorrect number of arguments. Write `§bet <amount> <1 or 2>` in chat')
            return

        if self.kasino.locked:
            await ctx.author.send('Kasino is locked! Taking in no more bets.')
            return

        alreadyBet = 0
        alreadyBetAmount = 0
        if str(ctx.author.id) in self.kasino.optionABets:
            alreadyBet = 1
            alreadyBetAmount = self.kasino.optionABets[str(ctx.author.id)].amount
        elif str(ctx.author.id) in self.kasino.optionBBets:
            alreadyBet = 2
            alreadyBetAmount = self.kasino.optionBBets[str(ctx.author.id)].amount

        amount = max(int(args[0]), 0)
        option = int(args[1])

        if amount == 0:
            output = discord.Embed(
                title='You tried to bet <= 0 karma! Silly you!',
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
            return

        if option == alreadyBet and amount > alreadyBetAmount:
            increase = amount - alreadyBetAmount
            karmaSystem = self.bot.get_cog('Karma')
            postkarma = karmaSystem.users[str(ctx.author.id)].post_karma
            linkkarma = karmaSystem.users[str(ctx.author.id)].link_karma

            postToAll = float(postkarma / (postkarma + linkkarma))

            betpost = min(round(increase * postToAll), postkarma)
            betlink = min(increase - betpost, linkkarma)

            if betlink + betpost == 0:
                output = discord.Embed(
                    title='Couldn\'t increase your bet because you are broke! Try again after you earn some karma.',
                    color=discord.Colour.from_rgb(209, 25, 25)
                )
                await ctx.author.send(embed=output)
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
                self.kasino.optionABets[str(ctx.author.id)] = KasinoSession.KasinoBet(ctx.author.id, alreadyBetAmount+betlink+betpost)
                output = discord.Embed(
                    title=f'**Successfully increased bet on option {option} for {betpost + betlink} karma! Total bet is now: {betlink+betpost} Karma**',
                    color=discord.Colour.from_rgb(52, 79, 235),
                    description=f'Remaining karma => Total: {(postkarma - betpost)+(linkkarma - betlink)} Post: {postkarma - betpost} | Link: {linkkarma - betlink}'
                )
                await ctx.author.send(embed=output)
            elif option == 2:
                self.kasino.optionBBets[str(ctx.author.id)] = KasinoSession.KasinoBet(ctx.author.id, alreadyBetAmount+betlink+betpost)
                output = discord.Embed(
                    title=f'**Successfully increased bet on option {option} for {betpost + betlink} karma! Total bet is now: {betlink+betpost} Karma**',
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
                return
        else:
            if alreadyBet != 0:
                output = discord.Embed(
                    title=f'You already bet {alreadyBetAmount} Karma on option {alreadyBet}. You may increase it using `§bet <amount over {alreadyBetAmount}> {alreadyBet}`',
                    color=discord.Colour.from_rgb(209, 25, 25)
                )
                await ctx.author.send(embed=output)
                return

            karmaSystem = self.bot.get_cog('Karma')
            postkarma = karmaSystem.users[str(ctx.author.id)].post_karma
            linkkarma = karmaSystem.users[str(ctx.author.id)].link_karma

            postToAll = float(postkarma / (postkarma + linkkarma))

            betpost = min(round(amount * postToAll), postkarma)
            betlink = min(amount - betpost, linkkarma)

            if betlink+betpost == 0:
                await ctx.author.send(f'Couldn\'t place a bet because you are broke! Try again after you earn some karma.')
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

            if option == 1:
                self.kasino.optionABets[str(ctx.author.id)] = KasinoSession.KasinoBet(ctx.author.id, betlink+betpost)
                output = discord.Embed(
                    title=f'**Successfully placed bet on option {option} for {betpost+betlink} karma!**',
                    color=discord.Colour.from_rgb(52, 79, 235),
                    description=f'Remaining karma => Total: {(postkarma - betpost)+(linkkarma - betlink)} Post: {postkarma-betpost} | Link: {linkkarma-betlink}'
                )
                await ctx.author.send(embed=output)
            elif option == 2:
                self.kasino.optionBBets[str(ctx.author.id)] = KasinoSession.KasinoBet(ctx.author.id, betlink+betpost)
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
                return

        karmaSystem.change_state_user(str(ctx.author.id), 'downvote', 'post', betpost)
        karmaSystem.change_state_user(str(ctx.author.id), 'downvote', 'link', betlink)

        if option == 1:
            self.kasino.amountA += betpost+betlink
        elif option == 2:
            self.kasino.amountB += betpost+betlink
        self.kasino.bets += 1

        self.save_session()
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

    def save_session(self):
        with open(os.path.abspath('./data/kasino/session.json'), 'w') as outfile:
            json.dump(self.kasino, outfile, cls=KasinoSession.KasinoEncoder, indent=4)
        print(f'{self.ccolor.OKCYAN}SAVED KASINO SESSION{self.ccolor.ENDC}')

    def load_session(self):
        if os.path.isfile(os.path.abspath('./data/kasino/session.json')):
            print(f'{self.ccolor.OKCYAN}LOADED KASINO SESSION{self.ccolor.ENDC}')
            return json.load(open(os.path.abspath('./data/kasino/session.json')), cls=KasinoSession.KasinoDecoder)
        else:
            return None

    async def update_kasino(self):
        kasinomsg = await (await self.bot.fetch_channel(self.kasino.channelID)).fetch_message(self.kasino.messageID)

        aAmount = self.kasino.amountA
        bAmount = self.kasino.amountB
        if aAmount != 0:
            aOdds = float(aAmount+bAmount)/aAmount
        else:
            aOdds = 1.0
        if bAmount != 0:
            bOdds = float(aAmount+bAmount)/bAmount
        else:
            bOdds = 1.0

        to_embed = discord.Embed(
            title=f'{"[LOCKED] " if self.kasino.locked else ""}:game_die: {self.kasino.question}',
            description=f'**On the table:** {aAmount+bAmount} Karma',
            color=discord.Colour.from_rgb(52, 79, 235)
        )

        footertext = ''
        if self.kasino.locked:
            footertext = 'The kasino is locked! No more bets are taken in. Time to wait and see...'
        else:
            footertext = 'The kasino has been opened! Place your bets using `§bet <amount> <1 or 2>`'

        to_embed.set_footer(text=footertext)
        to_embed.set_thumbnail(url='https://cdn.betterttv.net/emote/602548a4d47a0b2db8d1a3b8/3x.gif')
        to_embed.add_field(name=f'**1:** {self.kasino.optionA}', value=f'**Odds:** 1:{round(aOdds,3)}\n**Pool:** {aAmount} Karma')
        to_embed.add_field(name=f'**2:** {self.kasino.optionB}', value=f'**Odds:** 1:{round(bOdds,3)}\n**Pool:** {bAmount} Karma')

        await kasinomsg.edit(embed=to_embed)
        return


def setup(bot):
    bot.add_cog(Kasino(bot))
