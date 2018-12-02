import discord
from discord.ext import commands
import logging, pickle, os, random, asyncio, aiohttp, asyncpg, bs4, datetime, difflib, re, json, aioconsole, tabulate
import sys

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

strcommands = []
with open("dbinfo.json", "r") as f:
    psqluser = json.load(f)["user"]
    f.seek(0)
    psqlpass = json.load(f)["pass"]
    credentials = {"user": psqluser, "password": psqlpass, "database": "kaebot", "host": "127.0.0.1"}
os.system("cls")
print("Starting {}...".format(KAEBOT_VERSION))


async def prefix(instance, msg):
    result = await bot.kaedb.fetch(
        "SELECT prefix FROM server_prefixes WHERE server_id = $1",
        str(msg.guild.id)
    )
    prefixes = []
    for record in result:
        prefixes.append(dict(record)["prefix"])
    return prefixes


bot = commands.Bot(description="Made by TSHMN. Version: {0}".format(KAEBOT_VERSION), command_prefix=prefix,
                   activity=discord.Streaming(name="TSHMN's bot | Default prefix: kae", url="https://twitch.tv/monky"))


async def poolinit(con):
    await con.set_builtin_type_codec("hstore", codec_name="pg_contrib.hstore")


@bot.event
async def on_ready():
    print("{0} up and running on botuser {1}.".format(KAEBOT_VERSION, bot.user))
    print("Running on {} guilds.".format(len(bot.guilds)))
    for command in bot.commands:
        strcommands.append(str(command))
    print("Initialised strcommands.")
    bot.kaedb = await asyncpg.create_pool(
        **credentials,
        max_inactive_connection_lifetime=5,
        init=poolinit
    )
    print("Connection to database established: {}".format(bot.kaedb))
    while True:
        consoleinput = await aioconsole.ainput("KaeBot> ")
        try:
            eval(consoleinput)
        except Exception as e:
            print(e)


@bot.event
async def on_guild_join(guild):
    if guild.system_channel:
        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=KAEBOT_VERSION)
        embed.set_thumbnail(url="https://cdn.pbrd.co/images/HGYlRKR.png")
        embed.add_field(name="Hey there, I'm KaeBot!",
                        value="Hi! I'm KaeBot, a **discord.py** bot written by TSHMN (and aliases).\n"
                              "I currently have {} commands available to use; type 'kae help' to see them!\n"
                              "If you want to change my prefix, use 'kae prefix add'.\n Have fun!".format(len(bot.commands)),
                        inline=False)
        await guild.system_channel.send(embed=embed)

    await bot.kaedb.execute("INSERT INTO server_prefixes VALUES ({}, 'kae ')".format(guild.id))


@bot.event
async def on_guild_remove(guild):
    bot.kaedb.execute("DELETE FROM server_prefixes WHERE server_id = $1", guild.id)


class ErrorHandler:
    @staticmethod
    async def on_command_error(ctx, error):
        embed = discord.Embed(
            title="Fatal Error:",
            colour=discord.Color.from_rgb(81, 0, 124)
        )
        embed.set_footer(text=KAEBOT_VERSION)
        embed.set_thumbnail(url="https://cdn.pbrd.co/images/HGYlRKR.png")

        if hasattr(ctx.command, "on_error"):
            return

        if isinstance(error, commands.CommandNotFound):
            try:
                invalidcommand = re.findall(r"\"([^\"]*)\"", error.args[0])[0]
            except IndexError:
                invalidcommand = None
            similar = difflib.get_close_matches(invalidcommand, strcommands, n=5, cutoff=0.6)  # Get similar words

            similarstr = ""
            if not similar:
                similarstr = "No matches found."
            else:
                for simstr in similar:
                    similarstr += "{}\n".format(simstr)

            embed.add_field(name="Invalid command. Did you mean:",
                            value=similarstr,
                            inline=False)

        else:
            embed.add_field(name="An unhandled exception occurred.",
                            value=error,
                            inline=False)

        await ctx.send(embed=embed)


class BotOwner:
    @commands.command(name="kill", brief="Shuts KaeBot down.",
                      description="Forces Kaebot to shutdown. Only usable by Bot Owner.")
    async def kill(self, ctx):
        if ctx.message.author.id == 283858617973604352:
            await ctx.send("KaeBot signing out.")
            await bot.kaedb.close()
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
            await bot.kaedb.close()
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
            embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
            embed.set_footer(text="{} | Subcommands: add, remove".format(KAEBOT_VERSION))
            embedcontent = ""

            result = await bot.kaedb.fetch(
                "SELECT prefix FROM server_prefixes WHERE server_id = $1",
                str(ctx.guild.id)
            )
            for record in result:
                embedcontent += "{}command\n".format(dict(record)["prefix"])

            embed.add_field(name="Prefixes for {}:".format(ctx.guild.name),
                            value=embedcontent,
                            inline=False)
            await ctx.send(embed=embed)

    @prefix.command(name="add", brief="Add a prefix to the server. Enclose prefix in ' '.",
                    description="Add a server-specific prefix to KaeBot.\n Enclose prefix in ' '.")
    async def add(self, ctx, *, newprefix: str):
        if ctx.author.guild_permissions.administrator:
            if newprefix.startswith("'") and newprefix.endswith("'"):
                newprefix = newprefix[1: -1]
                await bot.kaedb.execute("INSERT INTO server_prefixes VALUES ($1, $2)", str(ctx.guild.id), newprefix)
                await ctx.send("Added '{}' as a prefix.".format(newprefix))
            else:
                await ctx.send("Bad input! Make sure you enclose your new prefix in single quotes like so: `'kae '`.")
        else:
            await ctx.send("You lack the following permissions to do this:\n```css\nAdministrator\n```")

    @prefix.command(name="remove", brief="Remove a prefix from the server.",
                    description="Remove a server-specific prefix from KaeBot.")
    async def remove(self, ctx, *, todelete):
        if ctx.author.guild_permissions.administrator:
            if todelete.startswith("'") and todelete.endswith("'"):
                todelete = todelete[1: -1]
                await bot.kaedb.execute("DELETE FROM server_prefixes WHERE server_id = $1 AND prefix = $2", str(ctx.guild.id), todelete)
                await ctx.send("Deleted the '{}' prefix.".format(todelete))
            else:
                await ctx.send("Bad input! Make sure you enclose the prefix in single quotes like so: `'kae '`.")
        else:
            await ctx.send("You lack the following permissions to do this:\n```css\nAdministrator\n```")


class Moderator:
    @commands.command(name="kick", brief="Kicks a user.",
                      description="Kicks a specified user. Only usable by users with the Kick Members permission.")
    async def kick(self, ctx, user: discord.Member, *, reason=""):
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
    async def ban(self, ctx, user: discord.Member, *, reason=""):
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
            colour=discord.Color.from_rgb(81, 0, 124)
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
        await ctx.send("Rift opened! Type .close. to close the rift.")
        while True:
            message = await bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            if message.content == ".close.":
                await ctx.send("Rift closed.")
                break
            else:
                await targetchannel.send("{} speaks from a rift: '{}'".format(ctx.author.name, message.content))

    @commands.command(name="ping", brief="Pong!",
                      description="Pings the bot and gets websocket latency.")
    async def ping(self, ctx):
        await ctx.send("Pong! Latency: {}ms".format(round(bot.latency * 1000, 2)))

    @commands.command(name="countdown", brief="Start a countdown to 0 (30 seconds max).",
                      description="Start a countdown going down to 0. The maximum start value is 30 seconds.")
    async def countdown(self, ctx, seconds: int):
        if seconds <= 0:
            await ctx.send("The countdown start can't be 0 or less!")
        elif seconds > 30:
            await ctx.send("That value is too big (<30).")
        else:
            while seconds != 0:
                await ctx.send(f"{seconds}...")
                await asyncio.sleep(1)
                seconds -= 1
            await ctx.send("Go!")

    @commands.command(name="pat", brief="Pat someone on the head.",
                      description="Pat someone on the head.")
    async def pat(self, ctx, user: discord.Member, *, reason: str=""):
        if reason:
            await ctx.send(f"{ctx.author.mention} gently pats {user.mention} and says '{reason}'.")
        else:
            await ctx.send(f"{ctx.author.mention} gently pats {user.mention}.")


class Genius:
    baseurl = "https://api.genius.com"
    header = {"Authorization": "Bearer " + GENIUS_CLIENTTOKEN}

    @commands.command(name="lyrics", brief="Get the lyrics to a song.",
                      description="Searches genius.com for the lyrics to a specified song.")
    async def lyrics(self, ctx, *, searchterms):
        embed = discord.Embed(
            colour=discord.Color.from_rgb(81, 0, 124)
        )
        embed.set_footer(text=KAEBOT_VERSION)
        embed.add_field(name="Now searching for '{}' on Genius.com...".format(searchterms),
                        value="Searching for lyrics...",
                        inline=False)
        await ctx.send(embed=embed)

        async with aiohttp.ClientSession() as session:
            async with session.get(Genius.baseurl + "/search",
                                   headers=Genius.header,
                                   data={"q": searchterms}) as response:
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

        lyricsoup = bs4.BeautifulSoup(responsetext, "lxml")
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
    @commands.command(name="spooky", brief="Adds some spook to your nickname.",
                      description="Adds a pumpkin to your nickname. Only usable during October!")
    async def spooky(self, ctx):
        if datetime.datetime.today().month == 10:
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

    @commands.command(name="christmas", brief="Adds some christmas spirit to your nickname.",
                      description="Adds a Christmas tree to your nickname. Only usable during December!")
    async def christmas(self, ctx):
        if datetime.datetime.today().month == 12:
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


class KaeRPG:
    with open("resources/kaerpg_items.json", "r") as f:
        items = json.load(f)

    with open("resources/kaerpg_enemies.json", "r") as f:
        dungeons = json.load(f)["Dungeons"]
        f.seek(0)
        enemies = json.load(f)["Enemies"]

    @staticmethod
    async def playerdamagecalc(self, weapondamage: int, weaponscaling: dict, characterstats: dict, enemyresistance: int):
        scalingmultiplier = {}
        for key, val in weaponscaling.items():
            if val == "A":
                scalingmultiplier[key] = 0.90
            elif val == "B":
                scalingmultiplier[key] = 0.70
            elif val == "C":
                scalingmultiplier[key] = 0.50
            elif val == "D":
                scalingmultiplier[key] = 0.30
            elif val == "N/A":
                scalingmultiplier[key] = 0
            else:
                raise ValueError(f"Bad scaling value in keypair {key}:{val}")

        rawdamageboost = 0
        for key, val in scalingmultiplier.items():
            rawdamageboost += val * int(characterstats[key])

        critboost = 1.5 if random.random() > 0.95 else 1
        fluctuation = random.uniform(weapondamage + rawdamageboost * -0.9, weapondamage + rawdamageboost * 0.9)
        return round(((weapondamage + rawdamageboost) * critboost + fluctuation) / enemyresistance)

    @staticmethod
    async def enemydamagecalc(self, enemydamage: int):
        return round(enemydamage + random.uniform(enemydamage * -0.9, enemydamage * 0.9))

    @commands.group(name="kaerpg", brief="A command group for every KaeRPG command. Aliased to kr.",
                    description="A command group for every KaeRPG command. Aliased to kr.", aliases=["kr"])
    async def kaerpg(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                colour=discord.Color.from_rgb(81, 0, 124)
            )
            embed.set_footer(text=KAEBOT_VERSION)
            embed.set_author(name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png")
            embedcontent = ""
            for command in KaeRPG.kaerpg.commands:
                embedcontent += f"{command}\n"
            embed.add_field(name="KaeRPG commands:",
                            value=embedcontent,
                            inline=False)
            await ctx.send(embed=embed)

    @kaerpg.command(name="beginnersguide", brief="Open a beginner's guide for KaeRPG.",
                    description="Open a beginner's guide for KaeRPG.")
    async def beginnersguide(self, ctx):
        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=KAEBOT_VERSION)
        embed.set_author(name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png")
        embed.add_field(name="Beginner's Guide to KaeRPG",
                        value="To start playing, create a character using 'prefix kaerpg makecharacter'.\n"
                              "Once you have a character, you can access information related to your character using"
                              " 'prefix kaerpg characterinfo'. This includes your character name, level, experience and "
                              "inventory.\nTo access a dungeon and fight enemies for loot, type 'prefix kaerpg dungeonlist'"
                              " to list dungeons and type 'prefix kaerpg raid dungeonname' to raid that dungeon.\n"
                              "For more information, type 'prefix kaerpg info' and then type 'prefix kaerpg info topic'"
                              " to learn about a specific topic.\n"
                              "For a list of other commands, type 'prefix kaerpg'.",
                        inline=False)
        await ctx.send(embed=embed)

    @kaerpg.command(name="makecharacter", brief="Create a KaeRPG character.",
                    description="Start KaeRPG by creating a character.")
    async def makecharacter(self, ctx):
        if await bot.kaedb.fetchrow("SELECT * FROM kaerpg_characterinfo WHERE user_id = $1", str(ctx.author.id)):
            await ctx.send("You already have a character.")
        else:
            embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
            embed.set_footer(text=KAEBOT_VERSION)
            embed.set_author(name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png")

            await ctx.send("Entered character creation!\n"
                           "Firstly, specify your character's name (10 characters or less).")
            while True:
                name = await bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
                name = name.content
                if len(name) <= 10:
                    break
                else:
                    await ctx.send("That name is too long (>10 characters). Try again.")

            statspecs = {
                "1": "STR 14 / DEX 12 / PRE 10 / ARC 8 / CON 13 / AGI 8",
                "2": "STR 8 / DEX 16 / PRE 11 / ARC 8 / CON 10 / AGI 12",
                "3": "STR 10 / DEX 12 / PRE 16 / ARC 10 / CON 8 / AGI 9",
                "4": "STR 21 / DEX 10 / PRE 8 / ARC 9 / CON 8 / AGI 9",
                "5": "STR 8 / DEX 9 / PRE 12 / ARC 16 / CON 8 / AGI 12",
            }
            for key in statspecs.keys():
                embed.add_field(name=key,
                                value=statspecs[key],
                                inline=False)
            await ctx.send(f"Your character is named {name}. What stats will they have? (Choose 1, 2, 3, 4 or 5).",
                           embed=embed)
            embed.clear_fields()

            while True:
                statchoice = await bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
                statchoice = statchoice.content
                if statchoice not in ["1", "2", "3", "4", "5"]:
                    await ctx.send("That's not one of the stat specs previously sent. Make sure to phrase your answer "
                                   "as '1', not 'Stat Spec 1' (no quotes).")
                else:
                    stats = statspecs[statchoice]
                    break

            startweapons = ""
            for weapon in ["Lumber's Axe", "Makeshift Shiv", "Hunter's Bow", "Tattered Scroll"]:
                startweapons += f"{weapon}:\n"
                startweapons += f"Rank: {KaeRPG.items['Weapons'][weapon]['Rank']}\n"
                startweapons += f"Damage: {KaeRPG.items['Weapons'][weapon]['Damage']}\n"
                startweapons += "Scaling: "
                for stat, scale in KaeRPG.items["Weapons"][weapon]["Scaling"].items():
                    startweapons += f"{stat} {scale} / "
                startweapons = startweapons[:-3] + "\n"
                startweapons += f"Info: {KaeRPG.items['Weapons'][weapon]['Info']}"
                if not weapon == "Tattered Scroll":
                    startweapons += "\n\n"
            embed.add_field(name="Starting weapon choices:",
                            value=startweapons,
                            inline=False)

            await ctx.send(f"Your character is named {name} and has the following stats: {stats}. What weapon will they start with?\n", embed=embed)
            embed.clear_fields()
            while True:
                weapon = await bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
                weapon = weapon.content
                if weapon not in ["Lumber's Axe", "Makeshift Shiv", "Hunter's Bow", "Tattered Scroll"]:
                    await ctx.send("That's not one of the specified starting weapons.")
                else:
                    break

            startarmour = ""
            for armour in ["Leather Carapace", "Warrior's Mail", "Rusted Paladin's Armour"]:
                startarmour += f"{armour}:\n"
                startarmour += f"Rank: {KaeRPG.items['Armour'][armour]['Rank']}\n"
                startarmour += f"Protection: {KaeRPG.items['Armour'][armour]['Protection']}\n"
                startarmour += f"Type: {KaeRPG.items['Armour'][armour]['Type']}\n"
                startarmour += f"Info: {KaeRPG.items['Armour'][armour]['Info']}"
                if not armour == "Rusted Paladin's Armour":
                    startarmour += "\n\n"
            embed.add_field(name="Starting armour choices:",
                            value=startarmour,
                            inline=False)

            await ctx.send(f"Your character is named {name} with the stats {stats} and the weapon {weapon}. What armour will they start with?\n",
                           embed=embed)
            embed.clear_fields()
            while True:
                armour = await bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
                armour = armour.content
                if armour not in ["Leather Carapace", "Warrior's Mail", "Rusted Paladin's Armour"]:
                    await ctx.send("That's not one of the specified starting armours.")
                else:
                    break

            embed.add_field(name="Your character was added to KaeRPG!",
                            value=f"{name} was just added to KaeRPG with the following stats:\n"
                            f"{stats}\n"
                            f"...and the following items:\n"
                            f"{weapon}, {armour}\n"
                            "You can now play KaeRPG. Use 'kaerpg beginnersguide' to learn how to play.",
                            inline=False)

            statdict = {}
            stats = stats.split(" / ")
            for stat in stats:
                dlist = stat.split(" ")
                statdict[dlist[0]] = dlist[1]

            await bot.kaedb.execute("INSERT INTO kaerpg_characterinfo VALUES ($1, $2, $3, $4, $5, $6, $7, $8)",
                                    str(ctx.author.id), name, 1, 0, statdict, [weapon, armour], 0, {"armour": armour, "weapon": weapon})
            await ctx.send(embed=embed)

    @kaerpg.command(name="delcharacter", brief="Delete your KaeRPG character.",
                    description="Delete your KaeRPG character permanently.")
    async def delcharacter(self, ctx):
        if await bot.kaedb.fetchrow("SELECT * FROM kaerpg_characterinfo WHERE user_id = $1", str(ctx.author.id)):
            await ctx.send("Are you sure you want to delete your character? (y/n)")
            while True:
                check = await bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
                check = check.content.lower()
                if check == "y":
                    await ctx.send("Deleting character from KaeDB...")
                    await bot.kaedb.execute("DELETE FROM kaerpg_characterinfo WHERE user_id = $1", str(ctx.author.id))
                    return await ctx.send("Character deleted.")
                elif check == "n":
                    return await ctx.send("Character deletion cancelled.")
                else:
                    await ctx.send("Specify Y or N as an answer.")
        else:
            await ctx.send("You don't have a character to delete.")

    @kaerpg.command(name="iteminfo", brief="Check an item.",
                    description="View an item's information.")
    async def iteminfo(self, ctx, *, item: str):
        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=KAEBOT_VERSION)
        embed.set_author(name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png")

        if item in KaeRPG.items["Weapons"].keys():  # If in weapon list:
            itemdict = KaeRPG.items["Weapons"][item]
            embedcontent = f"Rank: {itemdict['Rank']}\n"
            embedcontent += f"Damage: {itemdict['Damage']}\n"
            embedcontent += "Scaling: "
            for scale in itemdict['Scaling']:
                if scale == "ARC":
                    embedcontent += f"{scale} {itemdict['Scaling'][scale]}"
                else:
                    embedcontent += f"{scale} {itemdict['Scaling'][scale]} / "
            embedcontent += f"\nInfo: *{itemdict['Info']}*"

            embed.add_field(name=item,
                            value=embedcontent,
                            inline=False)
            await ctx.send(embed=embed)

        elif item in KaeRPG.items["Armour"].keys():  # If in armour list:
            itemdict = KaeRPG.items["Armour"][item]
            embedcontent = f"Rank: {itemdict['Rank']}\n"
            embedcontent += f"Protection: {itemdict['Protection']}\n"
            embedcontent += f"Type: {itemdict['Type']}\n"
            embedcontent += f"Info: *{itemdict['Info']}*"

            embed.add_field(name=item,
                            value=embedcontent,
                            inline=False)
            await ctx.send(embed=embed)

        elif item in KaeRPG.items["Consumables"]:  # If in consumables list:
            itemdict = KaeRPG.items["Consumables"][item]
            embedcontent = f"Value: {itemdict['Value']}\n"
            embedcontent += f"Effect: {itemdict['Effect']}\n"
            embedcontent += f"Info: *{itemdict['Info']}*"

            embed.add_field(name=item,
                            value=embedcontent,
                            inline=False)
            await ctx.send(embed=embed)

        else:
            similaritems = difflib.get_close_matches(item, KaeRPG.items["Weapons"].keys(), n=5, cutoff=0.6)
            embedcontent = ""
            for similar in similaritems:
                embedcontent += f"{similar}\n"
            embedcontent = embedcontent if embedcontent else "No similar matches found."
            embed.add_field(name="No matches found. Did you mean:",
                            value=embedcontent,
                            inline=False)
            await ctx.send(embed=embed)

    @kaerpg.command(name="characterlist", brief="List all characters in KaeRPG.",
                    description="List all of the characters registered in KaeRPG.")
    async def characterlist(self, ctx):
        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=KAEBOT_VERSION)
        embed.set_author(name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png")

        charlist = await bot.kaedb.fetch("SELECT * FROM kaerpg_characterinfo")
        embedcontent = ""
        for record in charlist:
            embedcontent += f"{record['name']} | {bot.get_user(int(record['user_id'])).display_name} |"
            embedcontent += f" {bot.get_user(int(record['user_id'])).id}\n"
        embed.add_field(name="Character List",
                        value=embedcontent,
                        inline=False)
        await ctx.send(embed=embed)

    @kaerpg.command(name="characterinfo", brief="Get the character info of a user's character. Aliased to inventory.",
                    description="Get character info of your or someone else's character. If a user is not"
                                " specified, this command defaults to your character. Aliased to inventory.",
                    aliases=["inventory"])
    async def characterinfo(self, ctx, user: commands.MemberConverter=None):
        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=KAEBOT_VERSION)
        embed.set_author(name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png")
        embed.set_thumbnail(url=ctx.author.avatar_url)

        if user is None:
            user = ctx.author
        rawinfo = await bot.kaedb.fetchrow("SELECT * FROM kaerpg_characterinfo WHERE user_id = $1", str(user.id))
        if rawinfo is None:  # No info exists, aka no character
            return await ctx.send("This user doesn't have a KaeRPG character.")

        stats = ""
        for key, val in rawinfo['stats'].items():
            stats += f"{key} {val} / "
        stats = stats[:-3]
        items = ""
        for item in rawinfo['items']:
            items += f"{item}, "
        items = items[:-2]
        kaecoins = rawinfo['kaecoins']
        equipped = ""
        for equipment in rawinfo['equipped'].values():
            equipped += f"{equipment}, "
        equipped = equipped[:-2]

        embed.add_field(name=f"Character Information for {user.display_name}:",
                        value=f"Character Name: {rawinfo['name']}\n"
                        f"Level: {rawinfo['level']}\n"
                        f"Current EXP: {rawinfo['exp']}\n"
                        f"Stats: {stats}\n"
                        f"Items: {items}\n"
                        f"Equipped: {equipped}\n"
                        f"KaeCoins: {kaecoins}",
                        inline=False)
        await ctx.send(embed=embed)

    @kaerpg.command(name="dungeonlist", brief="Lists all dungeons in KaeRPG.",
                    description="Lists all dungeons in KaeRPG.")
    async def dungeonlist(self, ctx):
        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=KAEBOT_VERSION)
        embed.set_author(name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png")
        embedcontent = ""
        for dungeon in KaeRPG.dungeons:
            embedcontent += f"{dungeon} (minimum level: {KaeRPG.dungeons[dungeon]['Minlevel']}, number of enemies:"
            embedcontent += f" {KaeRPG.dungeons[dungeon]['Number of Enemies']}, number of bosses: {len(KaeRPG.dungeons[dungeon]['Bosses'])})\n"
        embed.add_field(name="Dungeon List:",
                        value=embedcontent,
                        inline=False)
        await ctx.send(embed=embed)

    @kaerpg.command(name="weaponlist", brief="Lists all weapons in KaeRPG.",
                    description="Lists all weapons in KaeRPG (sorted by rank).")
    async def weaponlist(self, ctx):
        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=KAEBOT_VERSION)
        embed.set_author(name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png")

        embedcontent = dict.fromkeys(["Omega", "Beta", "Alpha", "S", "A", "B", "C", "D"], "")
        for item in KaeRPG.items["Weapons"]:
            embedcontent[KaeRPG.items['Weapons'][item]['Rank']] += f"{item}, "

        for rank, content in embedcontent.items():
            if content.endswith(", "):
                content = content[:-2]
            content = content if content else "No items of this rank exist."
            embedcontent[rank] = content

        embed.add_field(name="Omega Rank:",
                        value=embedcontent["Omega"],
                        inline=False)
        embed.add_field(name="Beta Rank:",
                        value=embedcontent["Beta"],
                        inline=False)
        embed.add_field(name="Alpha Rank:",
                        value=embedcontent["Alpha"],
                        inline=False)
        embed.add_field(name="S Rank:",
                        value=embedcontent["S"],
                        inline=False)
        embed.add_field(name="A Rank:",
                        value=embedcontent["A"],
                        inline=False)
        embed.add_field(name="B Rank:",
                        value=embedcontent["B"],
                        inline=False)
        embed.add_field(name="C Rank:",
                        value=embedcontent["C"],
                        inline=False)
        embed.add_field(name="D Rank:",
                        value=embedcontent["D"],
                        inline=False)
        await ctx.send(embed=embed)

    @kaerpg.command(name="armourlist", brief="Lists all armour in KaeRPG.",
                    description="Lists all armour in KaeRPG (sorted by rank).")
    async def armourlist(self, ctx):
        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=KAEBOT_VERSION)
        embed.set_author(name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png")

        embedcontent = dict.fromkeys(["Omega", "Beta", "Alpha", "S", "A", "B", "C", "D"], "")
        for item in KaeRPG.items["Armour"]:
            embedcontent[KaeRPG.items["Armour"][item]['Rank']] += f"{item}, "

        for rank, content in embedcontent.items():
            if content.endswith(", "):
                content = content[:-2]
            content = content if content else "No items of this rank exist."
            embedcontent[rank] = content

        for key in embedcontent.keys():
            embed.add_field(name=f"{key} Rank:",
                            value=embedcontent[key],
                            inline=False)

        await ctx.send(embed=embed)

    @kaerpg.command(name="equip", brief="Equip an item.",
                    description="Equip an item from your KaeRPG inventory.")
    async def equip(self, ctx, *, toequip: str):
        player = await bot.kaedb.fetchrow("SELECT * FROM kaerpg_characterinfo WHERE user_id = $1", str(ctx.author.id))
        if player:
            equipment = player['equipped']
            equipment = equipment if equipment else {}

            equippableweapons = []
            equippablearmour = []
            for item in player['items']:
                if item in KaeRPG.items["Weapons"]:
                    equippableweapons.append(item)
                elif item in KaeRPG.items["Armour"]:
                    equippablearmour.append(item)

            if toequip in equippableweapons:
                equipment["weapon"] = toequip
            elif toequip in equippablearmour:
                equipment["armour"] = toequip
            else:
                return await ctx.send("That is not a valid, equippable item (is it in your inventory)?")

            await bot.kaedb.execute("UPDATE kaerpg_characterinfo SET equipped = ($1) WHERE user_id = $2", equipment, str(ctx.author.id))
            await ctx.send(f"Equipped {toequip}.")

        else:
            await ctx.send("You don't have a character. Use 'prefix kaerpg makecharacter' to make one.")

    @kaerpg.command(name="raid", brief="Raid a dungeon!",
                    description="Raid a dungeon!")
    async def raid(self, ctx, *, dungeon: str):
        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=KAEBOT_VERSION)
        embed.set_author(name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png")

        if await bot.kaedb.fetchrow("SELECT * FROM kaerpg_characterinfo WHERE user_id = $1", str(ctx.author.id)):
            player = await bot.kaedb.fetchrow("SELECT * FROM kaerpg_characterinfo WHERE user_id = $1", str(ctx.author.id))
            try:  # Test this dungeon exists
                KaeRPG.dungeons[dungeon]
            except KeyError:
                return await ctx.send("That's not a KaeRPG dungeon.")
            if KaeRPG.dungeons[dungeon]['Minlevel'] > (await bot.kaedb.fetchrow("SELECT level FROM kaerpg_characterinfo WHERE user_id = $1", str(ctx.author.id)))['level']:
                return await ctx.send(f"Your level is too low for this dungeon (required level: {KaeRPG.dungeons[dungeon]['Minlevel']}).")
            embed.add_field(name=f"Starting a Raid on {dungeon}!",
                            value="Raid starting in 10 seconds...",
                            inline=False)
            await ctx.send(embed=embed)
            embed.clear_fields()
            await asyncio.sleep(10)

            actions = ["strike", "guard", "flee", "item"]
            for enemyindex in range(0, KaeRPG.dungeons[dungeon]["Number of Enemies"]):
                enemy = random.choice(KaeRPG.dungeons[dungeon]["Enemies"])
                playerhp = float(player['stats']['CON']) * 2 - (float(player['stats']['CON']) * 0.05)
                playermaxhp = playerhp
                enemyhp = KaeRPG.enemies[enemy]["Health"]
                enemymaxhp = enemyhp
                turn = 1

                embed.add_field(name=f"Enemy {enemyindex + 1} of {dungeon}:",
                                value=f"{enemy}",
                                inline=False)
                await ctx.send(embed=embed)
                embed.clear_fields()

                while True:
                    embed.add_field(name=f"Turn {turn}: You're fighting {enemy} ({enemyhp}/{enemymaxhp}HP).",
                                    value=f"{player} health: {playerhp}/{playermaxhp}HP.\nActions:\n"
                                    f"Strike, Guard, Flee, Item",
                                    inline=False)
                    await ctx.send(embed=embed)
                    embed.clear_fields()

                    action = await bot.wait_for("message",
                                                check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in actions)
                    action = action.content.lower()
                    assert action in actions
                    if action == "strike":
                        pass
                    elif action == "guard":
                        pass
                    elif action == "flee":
                        pass
                    elif action == "item":
                        pass

        else:
            await ctx.send("You don't have a character to raid this dungeon with! Use 'prefix kaerpg makecharacter'.")


bot.add_cog(BotOwner())
bot.add_cog(GuildOwner())
bot.add_cog(Administrator())
bot.add_cog(Moderator())
bot.add_cog(Miscellaneous())
bot.add_cog(Seasonal())
bot.add_cog(Genius())
bot.add_cog(KaeRPG())
# bot.add_cog(ErrorHandler())
bot.load_extension("jishaku")

bot.run(TOKEN)
