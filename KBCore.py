import discord
from discord.ext import commands
import logging, pickle, os, random, asyncio, aiohttp, asyncpg, bs4, datetime, difflib, re, json, aioconsole, tabulate

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


@bot.event
async def on_ready():
    print("{0} up and running on botuser {1}.".format(KAEBOT_VERSION, bot.user))
    print("Running on {} guilds.".format(len(bot.guilds)))
    for command in bot.commands:
        strcommands.append(str(command))
    print("Initialised strcommands.")
    bot.kaedb = await asyncpg.create_pool(**credentials)
    print("Connection to database established: {}".format(bot.kaedb))
    while True:
        consoleinput = await aioconsole.ainput("KaeBot> ")
        try:
            exec(consoleinput)
        except Exception as e:
            print(e)


@bot.event
async def on_guild_join(guild):
    if guild.system_channel:
        embed = discord.Embed(
            colour=discord.Color.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        )
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
            colour=discord.Color.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
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
            embed = discord.Embed(
                colour=discord.Color.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            )
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
            colour=discord.Color.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
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
    with open("kaerpg_items.json", "r") as f:
        items = json.load(f)

    @commands.group(name="kaerpg", brief="A command group for every KaeRPG command.",
                    description="A command group for every KaeRPG command.")
    async def kaerpg(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                colour=discord.Color.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
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

    @kaerpg.command(name="info", brief="Learn about KaeRPG.",
                    description="View an explanation of KaeRPG and its mechanics.")
    async def info(self, ctx):
        embed = discord.Embed(
            colour=discord.Color.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        )
        embed.set_footer(text=KAEBOT_VERSION)
        embed.set_author(name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png")
        embed.add_field(name="Overview",
                        value="KaeRPG is a built-in RPG integrated fully into KaeBot.\n"
                        "Everything you do in KaeRPG is saved for later use, so you can come and go as you please.\n"
                        "Information is saved across servers, so you can start on one server and continue on"
                        "another.\n"
                        "KaeRPG also features multiplayer, both in the same server or across servers!",
                        inline=False)
        embed.add_field(name="Stats",
                        value="KaeRPG has six stats: Strength, Dexterity, Precision, Arcane, Constitution and Agility"
                        " (STR, DEX, PRE, ARC, CON, AGI).\n"
                        "Strength, Dexterity, Precision and Arcane scale the strength of your weapons (see Items).\n"
                        "Constitution determines your character's base HP, and Agility determines who strikes first"
                        " in a battle.",
                        inline=True)
        embed.add_field(name="Weapons",
                        value="Weapons are used in combat to deal damage. They have three attributes:\n"
                        "Rank: How valuable the item is compared to other weapons (D, C, B, A, S, Alpha, Beta,"
                        " Omega).\n"
                        "Damage: The base damage of the weapon, without scaling.\n"
                        "Scaling: How the weapon's damage increases based on your stats. For example, if a weapon"
                        " has a STR scale of C and a DEX scale of B, your dexterity stat will be more important"
                        " to the weapon's damage than your strength stat.\n"
                        "Also, note that many weapons have no Arcane scaling whatsoever because they lack magical"
                        " power of any sort.",
                        inline=True)
        embed.add_field(name="Armour",
                        value="Armour is used in combat to negate damage. Armour has two attributes: "
                        "rank (how valuable the item is compared to other armour (D, C, B, A, S, Alpha, Beta,"
                        " Omega)) and protection (how much damage the armour negates).",
                        inline=True)
        embed.add_field(name="Consumables",
                        value="The other kind of items in KaeRPG are consumables, which are one-use items that provide "
                              "an effect. Most of them can be used in and out of combat.",
                        inline=True)
        await ctx.send(embed=embed)

    @kaerpg.command(name="makecharacter", brief="Create a KaeRPG character.",
                    description="Start KaeRPG by creating a character.")
    async def makecharacter(self, ctx):
        await ctx.send("Entered character creation!\nFirstly, specify your character's name (10 characters or less).")
        while True:
            name = await bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            name = name.content
            if len(name) <= 10 or len(name) == 0:
                break
            else:
                await ctx.send("That name is too long (>10 characters). Try again.")

        await ctx.send(KaeRPG.items)
        # for i in KaeRPG.items:
        # await ctx.send(f"Your character is named {name}. What weapon will they start with?\n"
        #                f"```css{weapons}```")

    @kaerpg.command(name="iteminfo", brief="Check an item.")
    async def iteminfo(self, ctx, *, item: str):
        embed = discord.Embed(
            colour=discord.Color.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        )
        embed.set_footer(text=KAEBOT_VERSION)
        embed.set_author(name="KaeRPG", icon_url="https://cdn.pbrd.co/images/HGYlRKR.png")

        try:
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

        except KeyError:
            similaritems = difflib.get_close_matches(item, KaeRPG.items["Weapons"].keys(), n=5, cutoff=0.6)
            embedcontent = ""
            for similar in similaritems:
                embedcontent += f"{similar}\n"
            embedcontent = embedcontent if embedcontent else "No similar matches found."
            embed.add_field(name="No matches found. Did you mean:",
                            value=embedcontent,
                            inline=False)
            await ctx.send(embed=embed)


bot.add_cog(BotOwner())
bot.add_cog(GuildOwner())
bot.add_cog(Administrator())
bot.add_cog(Moderator())
bot.add_cog(Miscellaneous())
bot.add_cog(Seasonal())
bot.add_cog(Genius())
bot.add_cog(KaeRPG())
bot.add_cog(ErrorHandler())
bot.load_extension("jishaku")

bot.run(TOKEN)
