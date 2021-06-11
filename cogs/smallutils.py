from datetime import datetime
import discord
from discord.ext import commands
import os


class SmallUtils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.VERSION = '**v1.4**'

    @commands.command(name='source', aliases=['s', 'info'])
    async def source(self, ctx):
        if await self.bot.is_restricted(ctx):
            return

        to_embed = discord.Embed(
            title='ANTICOMPSCI Source',
            color=discord.Colour.from_rgb(255, 0, 0),
            description=f'Current version: {self.VERSION}\n'
                        f'Source: [link](https://github.com/ollie-sara/discordBot)'
        )
        trans_logo = discord.File(os.path.abspath('Logo_transparent.png'), filename='image.png')
        to_embed.set_thumbnail(
            url='attachment://image.png'
        )
        to_embed.set_footer(
            text='Created by ollie[16] in HS2020'
        )
        await ctx.send(embed=to_embed, file=trans_logo)

    @commands.command(name='ping', aliases=['pong', 'p'])
    async def ping(self, ctx):
        if await self.bot.is_restricted(ctx):
            return

        command = str(ctx.message.content).replace('-', '')
        command = 'pong' if command == 'ping' else 'ping'
        try:
            latency = str(round(self.bot.latency*1000)) + " ms"
            to_embed = discord.Embed(
                title=f':ping_pong: {command.capitalize()}!',
                description='Latency in ms: `' + str(latency) + '`',
                color=discord.Colour.from_rgb(255, 0, 0),
            )
            to_embed.set_footer(text='As of: ' + datetime.now().strftime('%a, %d.%m.%Y, %H:%M'))
            await ctx.send(embed=to_embed)
        except Exception as e:
            print(e)
            await ctx.send("Couldn't print latency because ollie sucks at coding.")

    @commands.command(name='echo', aliases=['e'])
    async def test(self, ctx, *args):
        if await self.bot.is_restricted(ctx):
            return

        out = ''
        for a in args:
            out += a + ' '
        await ctx.send(out)

    @commands.command(name='suggest', aliases=['sug','sugg'])
    async def suggest(self, ctx, *, arg):
        if await self.bot.is_restricted(ctx):
            return

        await ctx.message.delete()

        if not arg:
            await ctx.send('Incorrect use of the command. Refer to `-help suggest` for further instructions.', delete_after=10)
            return

        suggestion = str(arg)
        author = ctx.author.name
        author_img = ctx.author.avatar_url

        to_embed = discord.Embed(
            title='You have a new suggestion:',
            description=suggestion,
            color=discord.Colour.from_rgb(50, 168, 82)
        )
        to_embed.set_footer(
            text=author,
            icon_url=author_img
        )

        await self.bot.get_user(108305736131440640).send(embed=to_embed)
        await ctx.send('Your suggestion has been sent successfully!', delete_after=10)
        return


def setup(bot):
    bot.add_cog(SmallUtils(bot))