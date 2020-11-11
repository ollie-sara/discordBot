import os
import xml.etree.ElementTree as ET

import discord
from discord.ext import commands

from cogs import bColors


class Help(commands.Cog):
    def __init__(self, bot):
        self.ccolor = bColors.bColors()
        self.bot = bot
        self.commandInfo = ET.parse(os.path.abspath('./data/help.xml')).getroot()
        self.commandList = ET.parse(os.path.abspath('./data/categories.xml')).getroot()

    @commands.command(name='help', aliases=['h', 'halp'])
    async def myhelp(self, ctx, *args):
        if str(ctx.command) in self.bot.restricted_commands and str(ctx.message.author.id) not in self.bot.owner_ids:
            await ctx.send('This command is currently only available to developers.')
            return

        auth = ctx.message.author.display_name
        auth_img = ctx.message.author.avatar_url
        to_embed = discord.Embed(
            color=discord.Colour.from_rgb(255, 0, 0),
        )
        trans_logo = discord.File(os.path.abspath('Logo_transparent.png'), filename='image.png')
        to_embed.set_thumbnail(
            url='attachment://image.png'
        )
        if args:
            requested = args[0]
        else:
            requested = 'help'
        desc = ''
        usage = ''
        aliases = ''
        title = ''
        if requested != 'help':
            for c in self.commandInfo.findall('command'):
                is_alias = False
                for a in c.find('aliases').findall('a'):
                    if a.text == requested:
                        is_alias = True
                if c.find('name').text == requested or is_alias:
                    title = c.find('name').text
                    usage = c.find('usage').text
                    desc = c.find('description').text
                    for a in c.find('aliases').findall('a'):
                        if a.text != 'none':
                            aliases += '`§'+a.text+'` '
                        else:
                            aliases += 'none'

            to_embed.title = '§' + title
            to_embed.add_field(
                name='Aliases',
                value=aliases,
                inline=False
            )
            to_embed.add_field(
                name='Usage',
                value=usage,
                inline=False
            )
            to_embed.add_field(
                name='Description',
                value=desc,
                inline=False
            )
        else:
            for cat in self.commandList.findall('category'):
                lines = ''
                for com in cat.findall('command'):
                    lines += '`'+com.find('name').text+'` => '+com.find('description').text+'\n'
                to_embed.add_field(
                    name=cat.find('cname').text,
                    value=lines,
                    inline=False
                )

            to_embed.add_field(
                name='_',
                value='To get specific instruction of a command, use `§help <command>` (without §)',
                inline=False
            )

        to_embed.set_footer(
            text='as requested by ' + auth,
            icon_url=auth_img
        )

        await ctx.send(file=trans_logo, embed=to_embed)


def setup(bot):
    bot.add_cog(Help(bot))