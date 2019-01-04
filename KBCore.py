import discord
from discord.ext import commands
import logging, os, asyncpg, difflib, re, json

# Made by TSHMN
logging.basicConfig(level=logging.INFO)
discord.opus.load_opus("libopus-0.x64.dll")
os.system("cls")
with open("resources/kaeinfo.json", "r") as f:
    TOKEN = json.load(f)["discordtoken"]


async def prefix(instance, msg):
    async with bot.kaedb.acquire() as conn:
        async with conn.transaction():
            result = await conn.fetch("SELECT prefix FROM server_prefixes WHERE server_id = $1", str(msg.guild.id))
    prefixes = []
    for record in result:
        prefixes.append(dict(record)["prefix"])
    return prefixes


bot = commands.Bot(
    description=f"Made by TSHMN. Version: KaeBot Beta",
    command_prefix=prefix,
    activity=discord.Streaming(name="TSHMN's bot | Default prefix: kae", url="https://twitch.tv/monky"),
)


async def poolinit(con):
    await con.set_builtin_type_codec("hstore", codec_name="pg_contrib.hstore")


@bot.event
async def on_ready():
    bot.KAEBOT_VERSION = "KaeBot Beta"
    with open("resources/kaeinfo.json", "r") as f:
        data = json.load(f)
        bot.TOKEN = TOKEN
        bot.PAFYKEY = data["pafykey"]
        bot.GENIUS_CLIENTID = data["geniusclientid"]
        bot.GENIUS_CLIENTSECRET = data["geniusclientsecret"]
        bot.GENIUS_CLIENTTOKEN = data["geniusclienttoken"]
        bot.PSQLUSER = data["psqluser"]
        bot.PSQLPASS = data["psqlpass"]
        bot.TRAVITIAKEY = data["travitiakey"]
        bot.SAUCENAOKEY = data["saucenaokey"]
    bot.credentials = {"user": bot.PSQLUSER, "password": bot.PSQLPASS, "database": "kaebot", "host": "127.0.0.1"}
    bot.strcommands = []
    for command in bot.commands:
        bot.strcommands.append(str(command))

    print(f"{bot.KAEBOT_VERSION} up and running. Running on {len(bot.guilds)} guilds.")
    print("Initialised strcommands.")
    bot.kaedb = await asyncpg.create_pool(**bot.credentials, max_inactive_connection_lifetime=5, init=poolinit)
    print(f"Connection to database established: {bot.kaedb}")


@bot.check
async def exilecheck(ctx):
    async with bot.kaedb.acquire() as conn:
        async with conn.transaction():
            return not await conn.fetch("SELECT * FROM exiled_users WHERE user_id = $1", str(ctx.author.id))


@bot.event
async def on_guild_join(guild):
    if guild.system_channel:
        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=bot.KAEBOT_VERSION)
        embed.set_thumbnail(url="https://cdn.pbrd.co/images/HGYlRKR.png")
        embed.add_field(
            name="Hey there, I'm KaeBot!",
            value="Hi! I'm KaeBot, a **discord.py** bot written by TSHMN (and aliases).\n"
            f"I currently have {len(bot.commands)} commands available to use; type 'kae help' to see them!\n"
            "If you want to change my prefix, use 'kae prefix add'.\n Have fun!",
            inline=False,
        )
        await guild.system_channel.send(embed=embed)

    async with bot.kaedb.acquire() as conn:
        async with conn.transaction():
            await conn.execute("INSERT INTO server_prefixes VALUES ($1, 'kae ')", str(guild.id))


@bot.event
async def on_guild_remove(guild):
    async with bot.kaedb.acquire() as conn:
        async with conn.transaction():
            conn.execute("DELETE FROM server_prefixes WHERE server_id = $1", guild.id)


cogs = []
for file in os.listdir("cogs"):
    if file.endswith(".py"):
        cogs.append(f"cogs.{file[:-3]}")

for cog in cogs:
    bot.load_extension(cog)
bot.load_extension("jishaku")

bot.run(TOKEN)
