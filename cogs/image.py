from PIL import Image, ImageFont, ImageDraw
from cogs import bColors
import discord
from discord.ext import commands
import os
import textwrap
from datetime import datetime


class ImageCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ccolor = bColors.bColors()

    @commands.command(name='drumpf', aliases=['dr'])
    async def drumpf(self, ctx, *, arg):
        if str(ctx.command) in self.bot.restricted_commands and str(ctx.message.author.id) not in self.bot.owner_ids:
            await ctx.send('This command is currently only available to developers.')
            return

        # INVALID INPUT
        if not arg:
            await ctx.send('Incorrect use of the command. Refer to `§help drumpf` for further instructions.')
            return

        # STARTING VALUES
        num = self.bot.current_image
        self.bot.current_image += 1
        string = str(arg)
        spacing = 35
        maxchars = 80
        for u in ctx.message.mentions:
            string = string.replace(f'<@!{u.id}>', '@'+str(u.display_name))
        for r in ctx.message.role_mentions:
            string = string.replace(f'<@&{r.id}>', '@'+str(r.name))
        for c in ctx.message.channel_mentions:
            string = string.replace(f'<#{c.id}>', '#'+str(c.name))

        if len(string) > 280:
            await ctx.send(f'Sorry, Twitter has a 280 character limit. Your message was {len(string)} characters long.')
            return

        # LOADS NECESSARY FILES
        template = Image.open(os.path.abspath('./data/drumpf_template.jpg'))
        segoe = ImageFont.truetype(font=os.path.abspath('./data/Segoe UI.ttf'), size=25)

        # TAKES COPIES OF EVERY ELEMENT OF THE TWEET
        header = template.crop((0, 0, 750, 85))
        line = template.crop((0, 85, 750, 85 + spacing))
        footer = template.crop((0, 85, 750, 155))

        # LOWERS THE NUMBER OF CHARACTERS PER LINE TO FIT THE IMAGE
        temp = ImageDraw.Draw(Image.new('RGB', (0, 0)))
        correct_size = False
        while not correct_size:
            correct_size = True
            for s in textwrap.wrap(string, width=maxchars):
                if temp.textsize(text=s, font=segoe)[0] > 700:
                    maxchars -= 5
                    correct_size = False
                    break

        # PREPARES THE BACKGROUND FOR THE TEXT TO GO ON IN THE CORRECT SIZE
        height = 155
        height += spacing * len(textwrap.wrap(string, width=maxchars))
        template = template.resize((750, height), resample=0)
        template.paste(header, box=(0, 0))
        n = 85
        while n < height - 60:
            template.paste(im=line, box=(0, n))
            n += spacing
        template.paste(footer, box=(0, height - 70))
        draw = ImageDraw.Draw(template)

        # DRAWS EVERY LINE ACCORDING TO OUR SETTINGS
        offset = 120
        for line in textwrap.wrap(string, width=maxchars):
            draw.text(
                xy=(25, offset),
                text=line,
                font=segoe,
                anchor='ls',
                fill=(255, 255, 255),
                align='left'
            )
            offset += spacing
        curtime = datetime.now()
        footer = curtime.strftime('%I:%M %p') + ' · ' + curtime.strftime('%b %d, %Y') + ' · Twitter for Discord'
        segoe = ImageFont.truetype(font=os.path.abspath('./data/Segoe UI.ttf'), size=18)
        draw.text(
            xy=(25, height - 25),
            text=footer,
            fill=(136, 153, 166),
            align='left',
            anchor='ls',
            font=segoe
        )

        # OUTPUTS FINISHED TWEET
        template.save(open(os.path.abspath(f'./temp/output_{num}.jpg'), 'w'), 'JPEG')
        # await ctx.message.delete()
        await ctx.send(file=discord.File(os.path.abspath(f'./temp/output_{num}.jpg'), filename='drumpf.jpg'))
        os.remove(os.path.abspath(f'./temp/output_{num}.jpg'))


def setup(bot):
    bot.add_cog(ImageCommands(bot))