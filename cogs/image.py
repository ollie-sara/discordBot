import PIL
from cogs import bColors
import discord
from discord.ext import commands
import os
import textwrap
from data.memegen import memegenerator
from datetime import datetime
import requests
from io import BytesIO


class Image(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ccolor = bColors.bColors()

    @commands.command(name='3x3', aliases=['collage'])
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def collage(self, ctx, *args):
        if await self.bot.is_restricted(ctx):
            return

        await ctx.message.delete()

        if len(args) != 9:
            await ctx.send('You need to send _nine_ links in order to create a 3x3 collage. Please, try again.', delete_after=30)
            return

        images = {}

        for i in range(9):
            if 'http' not in args[i]:
                await ctx.send('It seems one of the arguments you provided was not a link. You need to send _nine_ links in order to create a 3x3 collage. Please, try again.',
                               delete_after=30)
                return
            try:
                response = requests.get(str(args[i]))
                images[i] = PIL.Image.open(BytesIO(response.content))
                if images[i].width < images[i].height:
                    images[i] = images[i].crop(box=(0, 0, images[i].width, images[i].width)).resize((300, 300), resample=PIL.Image.BILINEAR)
                else:
                    images[i] = images[i].crop(box=(0, 0, images[i].height, images[i].height)).resize((300, 300), resample=PIL.Image.BILINEAR)
            except Exception as e:
                print(f'{self.ccolor.FAIL}IMAGE ERROR:{self.ccolor.ENDC} Could not download image from {args[i]}' + str(e))
                await ctx.send(
                    'Something wen\'t wrong with a link you sent. Try again and if it still doesn\'t work, there might be something wrong with the links.',
                    delete_after=30)
                return
            i += 1

        output = PIL.Image.new(size=(900, 900), mode='RGBA', color=(255, 255, 255, 100))
        for i in range(9):
            print((300*int(i/3), 300*(i%3)))
            if images[i].mode == 'RGBA':
                output.paste(im=images[i], box=(300*int(i/3), 300*(i%3),300*int(i/3)+300,300*(i%3)+300), mask=images[i])
            else:
                output.paste(im=images[i],
                             box=(300 * int(i / 3), 300 * (i % 3), 300 * int(i / 3) + 300, 300 * (i % 3) + 300))

        output.convert('RGB').save(open(os.path.abspath(f'./temp/collage_{ctx.author.id}.jpg'), 'wb'), 'JPEG')
        file = discord.File(os.path.abspath(f'./temp/collage_{ctx.author.id}.jpg'), filename=f'collage_{ctx.author.id}.jpg')
        to_embed = discord.Embed(
            title=f'Here is your finished collage, {ctx.author.display_name}!',
            colour=discord.Colour.from_rgb(29, 161, 242)
        )
        to_embed.set_image(
            url=f'attachment://collage_{ctx.author.id}.jpg'
        )
        to_embed.set_footer(
            text=f'created by {ctx.message.author.display_name}',
            icon_url=ctx.message.author.avatar_url
        )
        await ctx.send(file=file, embed=to_embed)
        os.remove(os.path.abspath(f'./temp/collage_{ctx.author.id}.jpg'))


    @collage.error
    async def collage_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.message.delete()
            output = discord.Embed(
                title=f'Collage is on cooldown, you can use it in {round(error.retry_after, 2)} seconds',
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
        else:
            output = discord.Embed(
                title=f'Something might\'ve gone wrong with the collage you tried to make.',
                color=discord.Colour.from_rgb(209, 25, 25)
            )
            await ctx.author.send(embed=output)
        return


    @commands.command(name='meme', aliases=['me'])
    async def meme(self, ctx, *args):
        if await self.bot.is_restricted(ctx):
            return
        if len(args) != 3:
            await ctx.send('Incorrect usage of the command. Use `§meme <url> "<toptext>" "<bottomtext>"`.')
            return
        if len(args[1]) > 120 or len(args[2]) > 120:
            await ctx.send(f'The strings you provided is too long. Limit yourself to 120 characters per line. Your top line was {len(args[1])} characters long and your bottom line {len(args[2])}')
            return
        await ctx.message.delete()
        num = self.bot.current_image
        img_url = args[0]
        try:
            response = requests.get(img_url)
            template = PIL.Image.open(BytesIO(response.content))
        except Exception as e:
            await ctx.send('I\'m sorry, I couldn\'t use the file link you supplied. <:sadge:772760101198102528>')
            print(f'{self.ccolor.FAIL}IMAGE ERROR:{self.ccolor.ENDC} Could not download image from {args[0]}'+str(e))
            return
        meme = memegenerator.make_meme(args[1].upper(), args[2].upper(), template)
        to_embed = discord.Embed(
            colour=discord.Colour.from_rgb(255, 0, 0)
        )
        if meme.mode == 'RGBA':
            meme.save(open(os.path.abspath(f'./temp/memetemp_{num}.png'), 'wb'), 'PNG')
            file = discord.File(os.path.abspath(f'./temp/memetemp_{num}.png'), filename=f'meme_{num}.png')
            to_embed.set_image(
                url=f'attachment://meme_{num}.png'
            )
        else:
            meme.save(open(os.path.abspath(f'./temp/memetemp_{num}.jpg'), 'wb'), 'JPEG')
            file = discord.File(os.path.abspath(f'./temp/memetemp_{num}.jpg'), filename=f'meme_{num}.jpg')
            to_embed.set_image(
                url=f'attachment://meme_{num}.jpg'
            )
        to_embed.set_footer(
            text=f'created by {ctx.author.display_name}',
            icon_url=ctx.author.avatar_url
        )
        await ctx.send(file=file, embed=to_embed)
        if meme.mode == 'RGBA':
            os.remove(os.path.abspath(f'./temp/memetemp_{num}.png'))
        else:
            os.remove(os.path.abspath(f'./temp/memetemp_{num}.jpg'))
        self.bot.current_image += 1

    @commands.command(name='drumpf', aliases=['dr'])
    async def drumpf(self, ctx, *, arg):
        if await self.bot.is_restricted(ctx):
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
        template = PIL.Image.open(os.path.abspath('./data/drumpf_template.jpg'))
        segoe = PIL.ImageFont.truetype(font=os.path.abspath('./data/Segoe UI.ttf'), size=25)

        # TAKES COPIES OF EVERY ELEMENT OF THE TWEET
        header = template.crop((0, 0, 750, 85))
        line = template.crop((0, 85, 750, 85 + spacing))
        footer = template.crop((0, 85, 750, 155))

        # LOWERS THE NUMBER OF CHARACTERS PER LINE TO FIT THE IMAGE
        temp = PIL.ImageDraw.Draw(PIL.Image.new('RGB', (0, 0)))
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
        draw = PIL.ImageDraw.Draw(template)

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
        segoe = PIL.ImageFont.truetype(font=os.path.abspath('./data/Segoe UI.ttf'), size=18)
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
        await ctx.message.delete()
        file = discord.File(os.path.abspath(f'./temp/output_{num}.jpg'), filename='drumpf.jpg')
        to_embed = discord.Embed(
            colour=discord.Colour.from_rgb(29,161,242)
        )
        to_embed.set_image(
            url='attachment://drumpf.jpg'
        )
        to_embed.set_footer(
            text=f'created by {ctx.message.author.display_name}',
            icon_url=ctx.message.author.avatar_url
        )
        await ctx.send(file=file, embed=to_embed)
        os.remove(os.path.abspath(f'./temp/output_{num}.jpg'))


def setup(bot):
    bot.add_cog(Image(bot))