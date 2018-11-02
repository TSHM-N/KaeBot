import discord
from discord.ext import commands
import logging
import pickle
import os
import random
import asyncio
import urllib.parse
import aiohttp
import json
from bs4 import BeautifulSoup
from datetime import datetime
import youtube_dl
import pafy

# Made by TSHMN

KAEBOT_VERSION = "KaeBot Alpha"
logging.basicConfig(level=logging.INFO)
discord.opus.load_opus("libopus-0.x64.dll")

PAFYKEY = pickle.load(open("pafyapikey.kae", "rb"))
TOKEN = pickle.load(open("token.kae", "rb"))
with open("geniusapiinfo.kae", "rb") as f:
    genius_info = pickle.load(f)
    GENIUS_CLIENTID = genius_info["client_id"]
    GENIUS_CLIENTSECRET = genius_info["client_secret"]
    GENIUS_CLIENTTOKEN = genius_info["client_access_token"]
pafy.set_api_key(PAFYKEY)

with open("serverprefixes.json", "r") as f:
    prefixes_str = f.read()
    prefixes = json.loads(prefixes_str)
default_prefix = "kae "


def prefix(instance, msg):
    contextualguildid = str(msg.guild.id)
    if contextualguildid not in prefixes:
        with open("serverprefixes.json", "r+") as file:
            prefixes.update({contextualguildid: ["kae "]})
            json.dump(prefixes, file, indent=4)
    return prefixes.get(contextualguildid, default_prefix)


bot = commands.Bot(description="Made by TSHMN. Version: {0}".format(KAEBOT_VERSION), command_prefix=prefix,
                   activity=discord.Streaming(name="TSHMN's bot.", url="https://twitch.tv/monky"))

os.system("cls")
print("Starting {}...".format(KAEBOT_VERSION))


@bot.event
async def on_ready():
    print("{0} up and running on botuser {1}.".format(KAEBOT_VERSION, bot.user))
    print("Running on {} guilds.".format(len(bot.guilds)))


class BotOwner:
    @commands.command(name="kill", brief="Shuts KaeBot down.",
                      description="Forces Kaebot to shutdown. Only usable by Bot Owner.")
    async def kill(self, ctx):
        if ctx.message.author.id == 283858617973604352:
            await ctx.send("KaeBot signing out.")
            await bot.logout()
        else:
            await ctx.send("You lack the following permissions to do this:\n```css\nBot Owner\n```")

    @commands.command(name="restart", brief="Restarts KaeBot.",
                      description="Restarts KaeBot. Only usable by Bot Owner.")
    async def restart(self, ctx):
        if ctx.message.author.id == 283858617973604352:
            await ctx.send("Restarting...")
            # hacky af BUT it works
            os.system("py .\KBRestartHax.py")
            await bot.logout()
        else:
            await ctx.send("You lack the following permissions to do this:\n```css\nBot Owner\n```")


class GuildOwner:
    pass


class Administrator:
    @commands.group(name="prefix", brief="Server-specific prefix commands. Run to view prefixes.",
                    description="This command group contains 'add' and 'remove' commands for prefix adjustment.\n"
                                "Prefixes can be viewed by anyone, but only changed by admins.")
    async def prefix(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                colour=discord.Color.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            )
            embed.set_footer(text="{} | Subcommands: add, remove".format(KAEBOT_VERSION))
            embedcontent = ""
            for i in prefixes[str(ctx.guild.id)]:
                if i == prefixes[str(ctx.guild.id)][-1]:
                    embedcontent += "'{}command'".format(i)
                else:
                    embedcontent += "'{}command', ".format(i)
            embed.add_field(name="Prefixes for {}:".format(ctx.guild.name),
                            value=embedcontent,
                            inline=False)
            await ctx.send(embed=embed)

    @prefix.command(name="add", brief="Add a prefix to the server.",
                    description="Add a server-specific prefix to KaeBot.")
    async def add(self, ctx, *, newprefix):
        if ctx.author.guild_permissions.administrator:
            newprefix += " "
            prefixes.setdefault(str(ctx.guild.id), []).append(newprefix)
            with open("serverprefixes.json", "w") as prefixfile:
                json.dump(prefixes, prefixfile, indent=4)
            await ctx.send("Added '{}' as a prefix.".format(newprefix))
        else:
            await ctx.send("You lack the following permissions to do this:\n```css\nAdministrator\n```")

    @prefix.command(name="remove", brief="Remove a prefix from the server.",
                    description="Remove a server-specific prefix from KaeBot.")
    async def remove(self, ctx, *, todelete):
        if ctx.author.guild_permissions.administrator:
            todelete += " "
            if todelete == "kae ":
                await ctx.send("Sorry, but you can't delete the default prefix.")
            elif todelete not in prefixes[str(ctx.guild.id)]:
                await ctx.send("That prefix does not exist.")
            else:
                prefixes[str(ctx.guild.id)].remove(todelete)
                with open("serverprefixes.json", "w") as prefixfile:
                    json.dump(prefixes, prefixfile, indent=4)
                await ctx.send("Removed '{}' from the prefix list.".format(todelete))
        else:
            await ctx.send("You lack the following permissions to do this:\n```css\nAdministrator\n```")


class Moderator:
    @commands.command(name="kick", brief="Kicks a user.",
                      description="Kicks a specified user. Only usable by users with the Kick Members permission.")
    async def kick(self, ctx, user: discord.Member, reason=""):
        print("Attempted kick by {0}. Target: {1}".format(ctx.message.author, user))
        if ctx.message.author.guild_permissions.kick_members:
            await user.send(content="You have been kicked from {0} by {1}.".format(ctx.message.guild,
                                                                                   ctx.message.author))
            if not reason == "":
                await user.send(content="Reason: '{0}'".format(reason))
            await user.kick(reason=reason)
            await ctx.send("{0} has been kicked.".format(user))
            print("Kick successful.")
        else:
            await ctx.send("You lack the following permissions to do this:\n```css\nKick Members\n```")
            print("Kick denied due to bad perms.")

    @commands.command(name="ban", brief="Bans a user.",
                      description="Bans a specified user. Only usable by users with the Ban Members permission.")
    async def ban(self, ctx, user: discord.Member, reason=""):
        print("Attempted ban by {0}. Target: {1}".format(ctx.message.author, user))
        if ctx.message.author.guild_permissions.ban_members:
            await user.send(content="You have been banned from {0} by {1}.".format(ctx.message.guild,
                                                                                   ctx.message.author))
            if not reason == "":
                await user.send(content="Reason: '{0}'".format(reason))
            await user.ban(reason=reason, delete_message_days=0)
            await ctx.send("{0} has been banned. Their ID: {1}".format(user, user.id))
            print("Ban successful.")
        else:
            await ctx.send("You lack the following permissions to do this:\n```css\nBan Members\n```")
            print("Ban denied due to bad perms.")

    @commands.command(name="unban", brief="Unbans a user.",
                      description="Unbans a specified user through their ID. Only usable by users with the Ban Members"
                                  " permission.")
    async def unban(self, ctx, user: int):
        print("Attempted ban by {0}. Target: {1}".format(ctx.message.author, user))
        if ctx.message.author.guild_permissions.ban_members:
            true_user = bot.get_user(user)
            await ctx.message.guild.unban(true_user)
            await ctx.send("{} unbanned.".format(true_user))
            print("Unban successful.")
        else:
            await ctx.send("You lack the following permissions to do this:\n```css\nBan Members\n```")
            print("Unban denied due to bad perms.")


class Voice:
    def __init__(self):
        self.voiceclient = None
        self.stream = None
        self.songqueue = []
        self.holdcontext = None

    async def delplay(self, error=""):
        self.voiceclient.stop()
        del self.songqueue[0]
        coro = self.playnext(self.holdcontext)
        asyncio.run_coroutine_threadsafe(coro, bot.loop).result()

    async def playnext(self, ctx):
        if self.songqueue is False:
            self.holdcontext = None
            return
        await ctx.send("Now playing: '{}'.".format(self.songqueue[0]["title"]))
        audio = self.songqueue[0]["pafyobj"].getbestaudio()
        self.stream = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(audio.url))
        self.holdcontext = ctx
        self.voiceclient.play(self.stream, after=self.delplay)

    @commands.command(name="summon", brief="Summons the bot to the invoking user's channel.",
                      description="Summons the bot to the invoking user's voice channel.")
    async def summon(self, ctx):
        for channel in ctx.message.guild.voice_channels:
            if ctx.message.author in channel.members:
                try:
                    self.voiceclient = await channel.connect()
                    print("Bot successfully summoned by {0} to {1}".format(ctx.message.author, channel))
                except discord.ClientException:
                    await self.voiceclient.move_to(channel)

    @commands.command(name="volume", brief="Alter the volume of the bot.",
                      description="Changes the volume of the audio being played by the bot.\n"
                                  "Percentage can be anything between 0 and 100.\n"
                                  "Note that by default, the bot's volume is already max (100%).")
    async def volume(self, ctx, percentage: str):
        stripped_percentage = float(percentage.strip("%"))
        if stripped_percentage in range(0, 100):
            volume = stripped_percentage / 100
            try:
                self.stream.volume = volume
                await ctx.send("Volume set to {0}%.".format(percentage))
            except AttributeError:
                await ctx.send("Try using this command once the bot has joined voice.")
        else:
            await ctx.send("Cannot set volume to {0}% (range: 0%-100%).".format(percentage.strip("%")))

    @commands.command(name="play", brief="Plays a Youtube video in a voice channel. Aliased to 'p'.",
                      description="Summons the bot to the invoking user's voice channel, then plays a Youtube link or"
                                  " searches Youtube, fetches the top result and plays that instead.\n"
                                  "Aliased to 'p'.", aliases=["p"])
    async def play(self, ctx, *, to_play):
        # Summon bot
        for channel in ctx.message.guild.voice_channels:
            if ctx.message.author in channel.members:
                try:
                    self.voiceclient = await channel.connect()
                    print("Bot successfully summoned by {0} to {1}".format(ctx.message.author, channel))
                except discord.ClientException:
                    await self.voiceclient.move_to(channel)
        # Search for video if necessary, get information
        await ctx.send("Searching for '{}' on Youtube...".format(to_play))
        if "youtube.com/" in to_play:
            # Treat as URL
            video = pafy.new(to_play)
        else:
            # Search youtube
            await ctx.send("urlencode")
            query = urllib.parse.urlencode({"search_query": to_play})
            await ctx.send("async with clientsesh")
            async with aiohttp.ClientSession() as session:
                await ctx.send("getresp")
                async with session.get("http://www.youtube.com/results?{}".format(query)) as response:
                    await ctx.send("assert 200 OK")
                    assert response.status == 200
                    await ctx.send("readcontent")
                    content = await response.read()
            await ctx.send("soupify")
            souped_content = BeautifulSoup(content, "lxml")
            await ctx.send("findattrs")
            firstvideo_href = souped_content.find(attrs={"class": "yt-uix-tile-link"})
            await ctx.send("pafy obj")
            video = pafy.new("https://www.youtube.com" + firstvideo_href["href"])
        await ctx.send("create vidinfo dict")
        video_info = {
            "pafyobj": video,
            "title": video.title,
            "author": video.author,
            "duration": video.length,
            "thumbnail": video.thumb,
            "id": video.videoid
        }
        # Add to queue
        await ctx.send("append to q")
        self.songqueue.append(video_info)
        await ctx.send("Got video information! Added {} to song queue.".format(video_info["title"]))
        if self.voiceclient.is_playing() or self.voiceclient.is_paused():
            return
        else:
            await self.playnext(ctx)

    @commands.command(name="disconnect", brief="Disconnects the bot from the current voice channel.",
                      description="Disconnects the bot from the current voice channel.", aliases=["d", "dc"])
    async def disconnect(self, ctx):
        await self.voiceclient.disconnect()

    @commands.command(name="skip", brief="Skips the current song. Aliased to 's'.",
                      description="Skips the current song. Aliased to 's'.", aliases=["s"])
    async def skip(self, ctx):
        await self.delplay()

    @commands.command(name="stop", brief="Stops the bot's audio. Different to 'pause'.",
                      description="Completely stops the bot's audio.\n"
                                  "Note that this command is different to pause: pause temporarily stops the bot and"
                                  " allows it to be resumed through 'play'/'resume', whereas stop silences the bot, "
                                  "clears the queue and does not allow the bot to resume playing until a new song"
                                  " has been queued.")
    async def stop(self, ctx):
        self.songqueue.clear()
        self.voiceclient.stop()

    @commands.command(name="queue", brief="Displays the bot's queue. Aliased to 'q'.",
                      description="Displays the bot's queue. Aliased to 'q'.", aliases=["q"])
    async def queue(self, ctx):
        await ctx.send(self.songqueue)


class Miscellaneous:
    @commands.command(name="random", brief="Generates a random number between 'start' and 'end'. Int only.",
                      description="Generates a random int between int 'start' and int 'end' such that "
                                  "'start <= n <= end'. Only accepts int arguments.")
    async def random(self, ctx, start: int, end: int):
        r = random.randint(start, end)
        await ctx.send("Your number is: {}.".format(r))

    @commands.command(name="russianroulette", brief="Play a quick game of Russian Roulette.",
                      description="Play a game of Russian Roulette.\n Choose the number of bullets in your barrel "
                                  "(default: 1), spin the barrel and fire.", aliases=["rr"])
    async def russianroulette(self, ctx, bullets: int=1):
        if bullets in range(0, 7):
            if bullets == 0:
                await ctx.send("Huh? That's not Russian Roulette, you pussy.")
            elif bullets == 6:
                await ctx.send("Do you have a death wish or something?")
            else:
                if random.random() < (bullets / 6):
                    await ctx.send("You took a bullet to the head. Better luck next time!")
                else:
                    await ctx.send("You survived! You live to play another day.")
        else:
            await ctx.send("That's not an appropriate number of bullets.")

    @commands.command(name="banroulette", brief="Play a quick game of Ban Roulette.",
                      description="Play a game of Ban Roulette.\n Choose the number of bullets in your barrel "
                                  "(default: 1), spin the barrel and fire.\n However, the difference between this and"
                                  " normal Russian Roulette is that if you die in this mode, you get banned!\n Be care"
                                  "ful!", aliases=["br"])
    async def banroulette(self, ctx, bullets: int=1):
        if bullets in range(0, 7):
            if bullets == 0:
                await ctx.send("Huh? That's not Russian Roulette, you pussy.")
            elif bullets == 6:
                await ctx.send("Do you want to get banned or something?")
            else:
                if random.random() < (bullets / 6):
                    await ctx.send("Sorry chief, but you died! You have five seconds to say your goodbyes before you"
                                   " get banned.")
                    await asyncio.sleep(5)
                    await ctx.send("{0} has been banned. Their ID: {1}".format(ctx.message.author,
                                                                               ctx.message.author.id))
                    await ctx.message.author.ban(reason="You failed Ban Roulette.", delete_message_days=0)
                else:
                    await ctx.send("You survived Ban Roulette! Nice job.")
        else:
            await ctx.send("That's not an appropriate number of bullets.")

    @commands.command(name="flip", brief="Flips a coin.", description="Flips a coin and returns the result.")
    async def flip(self, ctx):
        if random.randint(1, 2) == 1:
            await ctx.send("Heads.")
        else:
            await ctx.send("Tails.")

    @commands.command(name="slap", brief="Slap someone!", description="Slap someone!")
    async def slap(self, ctx, user: discord.Member, *, reason: str=""):
        if reason:
            await ctx.send("{0} just got slapped by {1}! Reason: '{2}'.".format(user.mention,
                                                                                ctx.message.author.mention, reason))
        else:
            await ctx.send("{0} just got slapped by {1}!".format(user.mention, ctx.message.author.mention))

    @commands.command(name="getinvite", brief="Invite KaeBot to your server.",
                      description="Gets two invites (one with admin permissions, and one without) that allows you"
                                  " to bring KaeBot to your server.")
    async def getinvite(self, ctx):
        embed = discord.Embed(
            title="Invite KaeBot to your server!",
            colour=discord.Color.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        )
        embed.set_thumbnail(url="https://cdn.pbrd.co/images/HGYlRKR.png")
        embed.set_footer(text=KAEBOT_VERSION)
        embed.add_field(name="Non-admin invite link",
                        value="If you want to add KaeBot to your server without giving it administrative permissions, "
                              "click the following link:\n https://discordapp.com/oauth2/authorize?client_id=49443105"
                              "6297197568&scope=bot&permissions=0",
                        inline=False)
        embed.add_field(name="Admin invite link",
                        value="If you want to add KaeBot to your server and give it administrative permissions, "
                              "click the following link:\n https://discordapp.com/oauth2/authorize?client_id=49443105"
                              "6297197568&scope=bot&permissions=8",
                        inline=False)
        embed.add_field(name="Warning:",
                        value="Note that both of these links require you to have at least the 'Manage Server' "
                              "permission for the server you want to invite KaeBot to.",
                        inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="rift", brief="Creates a rift between one channel and another.",
                      description="Opens a rift between the channel the command is executed in and the target channel."
                                  "\nThis rift transmits all messages made by you to the target channel until closed.")
    async def rift(self, ctx, targetchannel: discord.TextChannel):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        await ctx.send("Rift opened! Type .close. to close the rift.")
        while True:
            message = await bot.wait_for("message", check=check)
            if message.content == ".close.":
                await ctx.send("Rift closed.")
                break
            else:
                await targetchannel.send("{} speaks from a rift: '{}'".format(ctx.author.name, message.content))


class Genius:
    baseurl = "https://api.genius.com"
    header = {"Authorization": "Bearer " + GENIUS_CLIENTTOKEN}

    @commands.command(name="lyrics", brief="Get the lyrics to a song.",
                      description="Searches genius.com for the lyrics to a specified song.")
    async def lyrics(self, ctx, *, search_terms):
        embed = discord.Embed(
            colour=discord.Color.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        )
        embed.set_footer(text=KAEBOT_VERSION)
        embed.add_field(name="Now searching for '{}' on Genius.com...".format(search_terms),
                        value="Searching for lyrics...",
                        inline=False)
        await ctx.send(embed=embed)

        async with aiohttp.ClientSession() as session:
            async with session.get(Genius.baseurl + "/search",
                                   headers=Genius.header,
                                   data={"q": search_terms}) as response:
                resultjson = await response.json()

            async with session.get(Genius.baseurl + resultjson["response"]["hits"][0]["result"]["api_path"],
                                   headers=Genius.header) as response:
                songjson = await response.json()

            songurl = songjson["response"]["song"]["url"]
            songtitle = songjson["response"]["song"]["title"]
            songartist = songjson["response"]["song"]["album"]["artist"]["name"]
            songthumbnail = songjson["response"]["song"]["song_art_image_thumbnail_url"]

            async with session.get(songurl) as response:
                responsetext = await response.read()
                
        lyricsoup = BeautifulSoup(responsetext, "lxml")
        lyrics = lyricsoup.find("div", class_="lyrics").get_text()
        try:
            embed.set_thumbnail(url=songthumbnail)
        except AttributeError:  # No album art
            pass

        try:
            if len(lyrics) <= 1000:
                embed.add_field(name="Lyrics for '{0}' by '{1}':".format(songtitle, songartist),
                                value=lyrics,
                                inline=False)
                await ctx.send(embed=embed)
            else:
                for i in range(0, len(lyrics), 1000):
                    embed.clear_fields()
                    embedcontent = lyrics[i:i+1000]
                    if not i == list(reversed(range(0, len(lyrics), 1000)))[-0]:
                        embedcontent += "..."
                    if not i == list(range(0, len(lyrics), 1000))[0]:
                        embedcontent = "..." + embedcontent
                    embed.add_field(name="Lyrics for '{0}' by {1}:".format(songtitle, songartist),
                                    value=embedcontent,
                                    inline=False)
                    await ctx.send(embed=embed)

        except AttributeError:  # No lyrics, artist, title, song etc.
            embed.add_field(name="Something went wrong...",
                            value="Oops, something broke. Try another song.",
                            inline=False)
            await ctx.send(embed=embed)


class Seasonal:
    @commands.group(name="seasonal", brief="Commands such as spooky, christmas and more.",
                    description="This command contains several seasonal subcommands.\n"
                                "Subcommands: spooky, christmas\n"
                                "These can't be used until the time is right...")
    async def seasonal(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Subcommands: spooky, christmas")

    @seasonal.command(name="spooky", brief="Adds some spook to your nickname.",
                      description="Adds a pumpkin to your nickname. Only usable during October!")
    async def spooky(self, ctx):
        if datetime.today().month == 10:
            try:
                if not ctx.message.author.nick.endswith("\U0001f383"):
                    if ctx.message.author.nick.endswith("\U0001f384"):  # If already ends with Christmas emoji
                        changednick = ctx.message.author.nick[:-1] + " \U0001f383"
                    else:
                        changednick = ctx.message.author.nick + " \U0001f383"
                    await ctx.message.author.edit(nick=changednick)
                    await ctx.send("Your nickname is now '{}'.".format(changednick))
                else:
                    await ctx.send("Your nickname is already spooky!")

            except AttributeError:  # except if the person has no nick, because endswith is null
                if not ctx.message.author.name.endswith("\U0001f383"):
                    if ctx.message.author.name.endswith("\U0001f384"):  # If already ends with Christmas emoji
                        changednick = ctx.message.author.name[:-1] + " \U0001f383"
                    else:
                        changednick = ctx.message.author.name + " \U0001f383"
                    await ctx.message.author.edit(nick=changednick)
                    await ctx.send("Your nickname is now '{}'.".format(changednick))
                else:
                    await ctx.send("Your nickname is already spooky!")
        else:
            await ctx.send("It's not October, you can't use this yet!")

    @seasonal.command(name="christmas", brief="Adds some christmas spirit to your nickname.",
                      description="Adds a Christmas tree to your nickname. Only usable during December!")
    async def christmas(self, ctx):
        if datetime.today().month == 12:
            try:
                if not ctx.message.author.nick.endswith("\U0001f384"):
                    if ctx.message.author.nick.endswith("\U0001f383"):  # If already ends with Spooky emoji
                        changednick = ctx.message.author.nick[:-1] + " \U0001f384"
                    else:
                        changednick = ctx.message.author.nick + " \U0001f384"
                    await ctx.message.author.edit(nick=changednick)
                    await ctx.send("Your nickname is now '{}'.".format(changednick))
                else:
                    await ctx.send("Your nickname is already Christmassy!")

            except AttributeError:  # except if the person has no nick, because endswith is null
                if not ctx.message.author.name.endswith("\U0001f384"):
                    if ctx.message.author.name.endswith("\U0001f383"):  # If already ends with Spooky emoji
                        changednick = ctx.message.author.name[:-1] + " \U0001f384"
                    else:
                        changednick = ctx.message.author.name + " \U0001f384"
                    await ctx.message.author.edit(nick=changednick)
                    await ctx.send("Your nickname is now '{}'.".format(changednick))
                else:
                    await ctx.send("Your nickname is already Christmassy!")
        else:
            await ctx.send("It's not December, you can't use this yet!")


bot.add_cog(BotOwner())
bot.add_cog(GuildOwner())
bot.add_cog(Administrator())
bot.add_cog(Moderator())
bot.add_cog(Voice())
bot.add_cog(Miscellaneous())
bot.add_cog(Seasonal())
bot.add_cog(Genius())
bot.load_extension("jishaku")
bot.run(TOKEN)
