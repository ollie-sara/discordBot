import math
import discord
import os
import sqlite3
from discord.ext import commands
from cogs import bColors

class Multimedia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ccolor = bColors.bColors()
        self.init_db()

    def init_db(self):
        db = sqlite3.connect(os.path.abspath('./data/multimedia.db'))
        cur = db.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS suggestions('
                    'id INTEGER PRIMARY KEY,'
                    'type TEXT NOT NULL,'
                    'title TEXT NOT NULL,'
                    'genre TEXT NOT NULL,'
                    'link TEXT NOT NULL,'
                    'userid INTEGER NOT NULL,'
                    'submitted_by TEXT NOT NULL);')
        cur.execute('CREATE TABLE IF NOT EXISTS best('
                    'id INTEGER PRIMARY KEY,'
                    'userid INTEGER NOT NULL,'
                    'type TEXT NOT NULL,'
                    'attachment_url TEXT NOT NULL,'
                    'submitted_by TEXT NOT NULL);')
        cur.close()
        db.close()
        return

    # @commands.command(name='multimediasuggestion', aliases=['listentothis', 'playthis', 'readthis', 'watchthisshow', 'watchthismovie', 'watchthisanime'])
    # async def multimediasuggestion(self, ctx, *args):
    #     if await self.bot.is_restricted(ctx):
    #         return
    #     return

    @commands.command(name='myfav', aliases=['fav'])
    async def myfav(self, ctx, topic=None, option=None):
        if await self.bot.is_restricted(ctx):
            return

        if topic is None:
            await ctx.author.send('So you\'ve tried using `-myfav`, but might not be familiar with it yet. Here a quick explanation:\n'
                                  '`-myfav` is a command used to save and browse all sorts of other people\'s favorites. Currently following'
                                  ' topics are supported: `games|books|movies|shows|anime|music|mix|pokemon`\n\n'
                                  'To save a collage (commonly 3x3), complete the steps below:\n'
                                  '1. Create a collage in your favorite software/online tool and save it\n'
                                  '2. Drag it into the #spam channel\n'
                                  '3. Under "Comment" write `-myfav <topic>`. Replace `<topic>` with one of the above.\n'
                                  '4. Send the image. Your collage should now be registered.\n\n'
                                  'To browse other people\'s favorites, write `-myfav <topic> @user`\n'
                                  'To show people your favorites, write `-myfav <topic>`\n'
                                  'To delete your favorite, write `-myfav <topic> remove`\n'
                                  'To list who added their favorites to a topic, write `-myfav <topic> list`\n'
                                  'To list what favorites a user has added, write `-myfav @user list`\n'
                                  'This concludes all the information you may need to use `-myfav`. Thank you for reading, and have fun!')
            await ctx.send('Sent you a message in DMs!',
                           delete_after=30)
            await ctx.message.delete()
            return
        topic = topic.lower()

        if len(ctx.message.raw_mentions) != 0:
            user = ctx.message.raw_mentions[0]
        else:
            user = None

        if topic not in ['games', 'books', 'movies', 'shows', 'anime', 'music', 'mix', 'pokemon']:
            if user is not None:
                if option == 'list':
                    await self.list_fav_user(ctx, user)
                    return
                else:
                    await ctx.send('The topic you passed doesn\'t seem to be completely correct. Make sure you write '
                                   '`-myfav <games|books|movies|shows|anime|music|mix|pokemon>`.', delete_after=30)
                    await ctx.message.delete()
                    return
            elif user is None:
                await ctx.send('The topic you passed doesn\'t seem to be completely correct. Make sure you write '
                               '`-myfav <games|books|movies|shows|anime|music|mix|pokemon>`.', delete_after=30)
                await ctx.message.delete()
                return

        if option is None:
            db = sqlite3.connect(os.path.abspath('./data/multimedia.db'))
            cur = db.cursor()
            entry = cur.execute(f'SELECT attachment_url FROM best WHERE userid={ctx.author.id} AND type="{topic}"').fetchone()
            cur.close()
            db.close()
            if entry is None:
                if ctx.message.attachments is None:
                    await ctx.send('There doesn\'t seem to be an image provided. Make sure you write '
                                   '`-myfav <games|books|movies|shows|anime|music|mix|pokemon>` _as a comment_ in the dialog where you send the image.',
                                   delete_after=30)
                    await ctx.message.delete()
                    return
                await self.add_fav(ctx, topic)
            else:
                await self.show_fav(ctx, topic, ctx.author.id)
        elif option == 'list':
            await self.list_fav(ctx, topic)
        elif option == 'remove':
            await self.remove_fav(ctx, topic)
        elif 'http' in option:
            db = sqlite3.connect(os.path.abspath('./data/multimedia.db'))
            cur = db.cursor()
            entry = cur.execute(
                f'SELECT attachment_url FROM best WHERE userid={ctx.author.id} AND type="{topic}"').fetchone()
            cur.close()
            db.close()
            if entry is None:
                await self.add_fav(ctx, topic, option)
            else:
                await ctx.send('There doesn\'t seem to be an image provided. Make sure you write '
                               '`-myfav <games|books|movies|shows|anime|music|mix|pokemon>` _as a comment_ in the dialog where you send the image.',
                               delete_after=30)
                await ctx.message.delete()
                return
        else:
            await self.show_fav(ctx, topic, user)
        return

    async def remove_fav(self, ctx, topic):
        await ctx.message.delete()
        print(f'{self.ccolor.OKBLUE}CALLED REMOVE_FAV ON {topic}{self.ccolor.ENDC}')
        db = sqlite3.connect(os.path.abspath('./data/multimedia.db'))
        cur = db.cursor()
        entry = cur.execute(f'SELECT attachment_url FROM best WHERE userid={ctx.author.id} AND type="{topic}"').fetchone()

        if entry is None:
            await ctx.send(f'No favorite {topic} entry found for '
                           f'{ctx.author.display_name}. Nothing has been removed.', delete_after=30)
            cur.close()
            db.close()
            return

        cur.execute(f'DELETE FROM best WHERE userid={ctx.author.id} AND type="{topic}"')
        cur.close()
        db.commit()
        db.close()

        print(f'{self.ccolor.OKGREEN}REMOVED FAVORITE: {self.ccolor.ENDC}'
              f'{ctx.author.display_name} has removed their favorite {topic}')

        await ctx.send(f'Successfully deleted favorite {topic} entry for {ctx.author.display_name}', delete_after=30)
        return

    async def show_fav(self, ctx, topic, user):
        await ctx.message.delete()
        print(f'{self.ccolor.OKBLUE}CALLED SHOW_FAV ON {topic}, {user}{self.ccolor.ENDC}')

        if user is None:
            await ctx.send('User was either not found or option was incorrectly passed. '
                           'Available options are `list, remove`.',
                           delete_after=30)
            return

        db = sqlite3.connect(os.path.abspath('./data/multimedia.db'))
        cur = db.cursor()
        entry = cur.execute(f'SELECT attachment_url FROM best WHERE userid={int(user)} AND type="{topic}"').fetchone()
        cur.close()
        db.close()

        user = await self.bot.fetch_user(int(user))

        if entry is None:
            await ctx.send(f'No favorite {topic} entry found for {user.name}', delete_after=30)
            return

        to_embed = discord.Embed(
            title=f'{user.name}\'s favorite {topic}',
            color=discord.Colour.from_rgb(201, 30, 59)
        )
        to_embed.set_image(url=entry[0])
        to_embed.set_footer(text=f'requested by {ctx.author.display_name}', icon_url=ctx.author.avatar_url)

        await ctx.send(embed=to_embed)
        return

    async def list_fav_user(self, ctx, user):
        db = sqlite3.connect(os.path.abspath('./data/multimedia.db'))
        cur = db.cursor()
        entries = cur.execute(f'SELECT type FROM best WHERE userid={int(user)}').fetchall()
        cur.close()
        db.close()

        await ctx.message.delete()
        print(entries)
        if len(entries) == 0:
            topics = "...nothing. They didn't share anything (yet)."
        else:
            topics = ""
            for entry in entries:
                topics += entry[0]+"\n"

        username = (await self.bot.fetch_user(int(user))).name

        to_embed= discord.Embed(
            title=f'{username} shared with us their favorite...',
            description=topics,
            color=discord.Colour.from_rgb(201, 30, 59)
        )
        to_embed.set_footer(text=f'requested by {ctx.author.display_name}', icon_url=ctx.author.avatar_url)

        await ctx.send(embed=to_embed, delete_after=45)
        return

    async def list_fav(self, ctx, topic):
        await ctx.message.delete()
        print(f'{self.ccolor.OKBLUE}CALLED LIST_FAV ON {topic}{self.ccolor.ENDC}')
        db = sqlite3.connect(os.path.abspath('./data/multimedia.db'))
        cur = db.cursor()
        entries = cur.execute(f'SELECT submitted_by FROM best WHERE type="{topic}"').fetchall()
        cur.close()
        db.close()

        to_embed = discord.Embed(
            title=f'These users shared their favorite {topic} already:',
            color=discord.Colour.from_rgb(201, 30, 59)
        )

        namegroups = {}
        i = 0
        for entry in entries:
            if i%5 == 0:
                namegroups[int(i/5)] = entry[0]+"\n"
            elif i%5 == 4:
                namegroups[int(i/5)] += str(entry[0])
            else:
                namegroups[int(i/5)] += str(entry[0])+"\n"
            i += 1
        print(namegroups)
        i = 1
        for nameblock in namegroups.values():
            to_embed.add_field(
                name=str(i)+f' to {i+4}',
                value=nameblock,
                inline=True
            )
            i += 1

        to_embed.set_footer(text=f'requested by {ctx.author.display_name}', icon_url=ctx.author.avatar_url)

        await ctx.send(embed=to_embed, delete_after=45)
        return

    async def add_fav(self, ctx, topic, link=None):
        print(f'{self.ccolor.OKBLUE}CALLED ADD_FAV ON {topic}{self.ccolor.ENDC}')
        if link is not None:
            await ctx.message.delete()
            image_url = link
        else:
            if len(ctx.message.attachments) == 0:
                await ctx.send(f'You did not send an image. '
                               f'Please, try again using `-myfav {topic}` _as a comment_ on your collage image.', delete_after=30)
                return
            try:
                image_url = ctx.message.attachments[0].url
            except Exception:
                await ctx.send('There was an unexpected issue with your attachment. Please, try again.', delete_after=30)
                return

        db = sqlite3.connect(os.path.abspath('./data/multimedia.db'))
        cur = db.cursor()
        cur.execute(f'INSERT INTO best (userid, type, attachment_url, submitted_by)'
                    f'VALUES({ctx.author.id}, "{topic}", "{image_url}", "{ctx.author.display_name}")')
        print(f'{self.ccolor.OKGREEN}ADDED FAVORITE: {self.ccolor.ENDC}'
              f'{ctx.author.display_name} has submitted their favorite {topic}')
        db.commit()
        cur.close()
        db.close()

        to_embed = discord.Embed(
            title=f'{ctx.author.display_name} is sharing their favorite {topic}',
            description='Thank you for sharing! Your contribution has been archived for the future. (Do not delete the message with the image, otherwise you will not be able to fetch it anymore)',
            color=discord.Colour.from_rgb(201, 30, 59)
        )

        await ctx.send(embed=to_embed)
        return

def setup(bot):
    bot.add_cog(Multimedia(bot))
