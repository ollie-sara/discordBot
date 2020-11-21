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
            'reddit',
            'help',
            'smallutils',
            'image',
            'karma'
        ]
        bot.owner_ids = [
            '108305736131440640',   # OLLIE
            '153929916977643521',   # BATTLERUSH
            '205704051856244736'    # SPRÜTZ
        ]
        bot.restricted_commands = [
            'bansub',
            'unbansub',
            'reload',
            'restart'
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
            await self.bot.get_cog('Karma').saving_routine()
            print(f'{self.ccolor.OKBLUE}BACKGROUND LOOP:{self.ccolor.ENDC} FINISHED LOOP SUCCESSFULLY')
            await asyncio.sleep(600)

    async def on_reaction_add(self, reaction, user):
        bot = self.bot
        emoji = reaction.emoji.id
        if emoji == 747783377662378004 and reaction.message.author.id != user.id:
            bot.get_cog('Karma').change_state_user(user_id=reaction.message.author.id, change='upvote',
                                                   karma_type=bot.get_cog('Karma').check_type(reaction.message))
            bot.get_cog('Karma').change_state_post(message=reaction.message,
                                                   value='up', increase=True)
        elif emoji == 758262252699779073 and reaction.message.author.id != user.id:
            bot.get_cog('Karma').change_state_user(user_id=reaction.message.author.id, change='downvote',
                                                   karma_type=bot.get_cog('Karma').check_type(reaction.message))
            bot.get_cog('Karma').change_state_post(message=reaction.message,
                                                   value='down', increase=True)

    async def on_reaction_remove(self, reaction, user):
        bot = self.bot
        emoji = reaction.emoji.id
        if emoji == 747783377662378004 and reaction.message.author.id != user.id and not user.bot:
            bot.get_cog('Karma').change_state_user(user_id=reaction.message.author.id, change='downvote',
                                                   karma_type=bot.get_cog('Karma').check_type(reaction.message))
            bot.get_cog('Karma').change_state_post(message=reaction.message,
                                                   value='up', increase=False)
        elif emoji == 758262252699779073 and reaction.message.author.id != user.id and not user.bot:
            bot.get_cog('Karma').change_state_user(user_id=reaction.message.author.id, change='upvote',
                                                   karma_type=bot.get_cog('Karma').check_type(reaction.message))
            bot.get_cog('Karma').change_state_post(message=reaction.message,
                                                   value='down', increase=False)

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