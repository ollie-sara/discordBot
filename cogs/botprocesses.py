from discord.ext import commands
from cogs import bColors
import asyncio
import sys
import os


class BotProcesses(commands.Cog):
    def __init__(self, bot):
        bot.current_image = 0
        self.bot = bot
        self.ccolor = bColors.bColors()
        self.modules = [
            'help',
            'smallutils',
            'image',
            'karma',
            'kasino',
            'multimedia',
            'economy'
        ]
        bot.owner_ids = [
            '108305736131440640',   # OLLIE
            '153929916977643521',   # BATTLERUSH
            '205704051856244736',   # SPRÜTZ
            '299478604809764876',   # AARON
            '223932775474921472'    # LUKAS
        ]
        bot.restricted_commands = [
            'bansub',
            'unbansub',
            'reload',
            'restart',
            'checkpost',
            'openkasino',
            'refreshkasino',
            'closekasino',
            'lockkasino'
        ]
        self.loop = None

    async def ainit(self):
        await self.load_cogs()
        await self.on_ready()

    async def is_restricted(self, ctx):
        bot = self.bot
        if str(ctx.command) in bot.restricted_commands and str(ctx.message.author.id) not in bot.owner_ids:
            await ctx.send('This command is currently only available to developers.')
            return True
        return False

    async def is_admin(self, ctx):
        bot = self.bot
        if str(ctx.message.author.id) in bot.owner_ids:
            return True
        return False

    @commands.command(name='reload')
    async def reload(self, ctx):
        bot = self.bot
        for mo in self.modules:
            bot.reload_extension('cogs.' + mo)
        await ctx.send('Reloaded all cogs! Thank you, admin! :relaxed:')

    async def load_cogs(self):
        ccolor = self.ccolor
        try:
            for m in self.modules:
                self.bot.load_extension('cogs.'+m)
                print(f'{ccolor.OKBLUE}LOADED COG: {ccolor.ENDC}{m}')
        except Exception as e:
            exc_type, exc_obj, tb = sys.exc_info()
            lineno = tb.tb_lineno
            print(f'{ccolor.WARNING}COG ERROR: {ccolor.ENDC}{e} | Line: {lineno}')

    async def background_loop(self):
        while True:
            try:
                await self.bot.get_cog('Karma').saving_routine()
            except Exception as e:
                print(f'{self.ccolor.FAIL}BACKGROUND LOOP ERROR:{self.ccolor.ENDC} COULD NOT START BACKGROUND LOOP | ' + str(e))
                return
            print(f'{self.ccolor.OKBLUE}BACKGROUND LOOP:{self.ccolor.ENDC} FINISHED LOOP SUCCESSFULLY')
            await asyncio.sleep(1200)

    async def on_raw_reaction_add(self, payload):
        bot = self.bot
        emoji = payload.emoji
        member = await bot.fetch_user(payload.user_id)
        message = await (await bot.fetch_channel(payload.channel_id)).fetch_message(payload.message_id)
        if str(emoji) == '<:this:747783377662378004>' and message.author.id != member.id and not member.bot:
            bot.get_cog('Karma').change_state_user(user_id=message.author.id, change='upvote',
                                                   karma_type=bot.get_cog('Karma').check_type(message), amount=1)
            bot.get_cog('Karma').change_state_post(message=message,
                                                   value='up', increase=True)
        elif str(emoji) == '<:that:758262252699779073>' and message.author.id != payload.member.id and not member.bot:
            bot.get_cog('Karma').change_state_user(user_id=message.author.id, change='downvote',
                                                   karma_type=bot.get_cog('Karma').check_type(message), amount=1)
            bot.get_cog('Karma').change_state_post(message=message,
                                                   value='down', increase=True)

    async def on_raw_reaction_remove(self, payload):
        bot = self.bot
        emoji = payload.emoji
        member = await bot.fetch_user(payload.user_id)
        message = await (await bot.fetch_channel(payload.channel_id)).fetch_message(payload.message_id)
        if str(emoji) == '<:this:747783377662378004>' and message.author.id != member.id and not member.bot:
            bot.get_cog('Karma').change_state_user(user_id=message.author.id, change='downvote',
                                                   karma_type=bot.get_cog('Karma').check_type(message), amount=1)
            bot.get_cog('Karma').change_state_post(message=message,
                                                   value='up', increase=False)
        elif str(emoji) == '<:that:758262252699779073>' and message.author.id != member.id and not member.bot:
            bot.get_cog('Karma').change_state_user(user_id=message.author.id, change='upvote',
                                                   karma_type=bot.get_cog('Karma').check_type(message), amount=1)
            bot.get_cog('Karma').change_state_post(message=message,
                                                   value='down', increase=False)

    async def on_reaction_remove(self, reaction, user):
        pass

    async def on_reaction_add(self, reaction, user):
        pass

    async def on_ready(self):
        bot = self.bot
        print(f'{self.ccolor.OKBLUE}{bot.user}{self.ccolor.ENDC} joined on server!')
        with open(os.path.abspath('./data/bannedsubs.txt')) as f:
            bot.banned_subs = f.read().splitlines()
        self.loop = asyncio.create_task(self.background_loop())

    async def end_loop(self):
        if self.loop is not None:
            self.loop.cancel()
            print(f'{self.ccolor.OKBLUE}BACKGROUND LOOP: {self.ccolor.ENDC}CANCELLED LOOP SUCCESFULLY')


def setup(bot):
    bot.add_cog(BotProcesses(bot))