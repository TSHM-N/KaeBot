import discord
from discord.ext import commands
import asyncio


class Administrator:
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="prefix", brief="Server-specific prefix commands. Run to view prefixes.",
                    description="This command group contains 'add' and 'remove' commands for prefix adjustment.\n"
                                "Prefixes can be viewed by anyone, but only changed by admins.")
    async def prefix(self, ctx):
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
            embed.set_footer(text=f"{self.bot.KAEBOT_VERSION} | Subcommands: add, remove")
            embedcontent = ""

            async with self.bot.kaedb.acquire() as conn:
                async with conn.transaction():
                    result = await conn.fetch("SELECT prefix FROM server_prefixes WHERE server_id = $1", str(ctx.guild.id))
            for record in result:
                embedcontent += f"{dict(record)['prefix']}command\n"

            embed.add_field(name=f"Prefixes for {ctx.guild.name}:",
                            value=embedcontent,
                            inline=False)
            await ctx.send(embed=embed)

    @prefix.command(name="add", brief="Add a prefix to the server. Enclose prefix in ' '.",
                    description="Add a server-specific prefix to Kaeself.bot.\n Enclose prefix in ' '.")
    async def add(self, ctx, *, newprefix: str):
        if ctx.author.guild_permissions.administrator:
            if newprefix.startswith("'") and newprefix.endswith("'"):
                newprefix = newprefix[1: -1]
                async with self.bot.kaedb.acquire() as conn:
                    async with conn.transaction():
                        await conn.execute("INSERT INTO server_prefixes VALUES ($1, $2)", str(ctx.guild.id), newprefix)
                await ctx.send(f"Added '{newprefix}' as a prefix.")
            else:
                await ctx.send("Bad input! Make sure you enclose your new prefix in single quotes like so: `'kae '`.")
        else:
            await ctx.send("You lack the following permissions to do this:\n```css\nAdministrator\n```")

    @prefix.command(name="remove", brief="Remove a prefix from the server.",
                    description="Remove a server-specific prefix from Kaeself.bot.")
    async def remove(self, ctx, *, todelete):
        if ctx.author.guild_permissions.administrator:
            if todelete.startswith("'") and todelete.endswith("'"):
                todelete = todelete[1: -1]
                async with self.bot.kaedb.acquire() as conn:
                    async with conn.transaction():
                        await conn.execute("DELETE FROM server_prefixes WHERE server_id = $1 AND prefix = $2", str(ctx.guild.id), todelete)
                await ctx.send(f"Deleted the '{todelete}' prefix.")
            else:
                await ctx.send("Bad input! Make sure you enclose the prefix in single quotes like so: `'kae '`.")
        else:
            await ctx.send("You lack the following permissions to do this:\n```css\nAdministrator\n```")

    @commands.command(name="prune", brief="Prunes members from the server.",
                      description="Prune members from the server who have been inactive for a specified number of days"
                                  " (default: 5) and who have no roles.")
    async def prune(self, ctx, daysinactive: int=5):
        if ctx.author.guild_permissions.administrator:
            estimate = await ctx.guild.estimate_pruned_members(days=daysinactive)
            if not estimate == 0:
                await ctx.send(f"\U00002757This opeation will prune **{estimate}** from the server who have been inactive"
                               f" for the past **{daysinactive}** days and who have no roles. Proceed? (y\\n)")
            else:
                return await ctx.send("No eligible, prunable members of this server who have been inactive for the past"
                                      f" {daysinactive} days.")
            message = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            if message.content == "y":
                await ctx.guild.prune_members(days=daysinactive, reason="Pruned due to inactivity.")
                await ctx.send(f"Purged {estimate} members.")
            elif message.content == "n":
                await ctx.send("Prune cancelled.")
            else:
                await ctx.send("Invalid input. Presuming `n` response; cancelling prune.")
        else:
            await ctx.send("You lack the following permissions to do this:\n```css\nAdministrator\n```")

    @commands.command(name="allkick", brief="Kicks everyone in the server. Use this wisely.",
                      description="Kicks everyone in the server. Skips kickable members.\n"
                                  "Restricted to Administrator.")
    @commands.bot_has_permissions(kick_members=True)
    @commands.has_permissions(kick_members=True)
    async def allkick(self, ctx):
        message = await ctx.send("\U00002757WARNING\U00002757 This command will **kick everyone** in the server "
                                 "except unkickable members. Are you sure you want to proceed?")
        await message.add_reaction("\U00002705")
        await message.add_reaction("\U0000274e")
        try:
            reaction, user = await self.bot.wait_for("reaction_add",
                                                     check=lambda r, u: r.message.id == message.id and u == ctx.author and str(r.emoji) in ["✅", "❎"],
                                                     timeout=10)
        except asyncio.TimeoutError:
            return await ctx.send("Operation cancelled due to lack of response.")
        if str(reaction.emoji) == "✅":
            await ctx.send("\U00002699Processing...\U00002699")
            for member in ctx.guild.members:
                try:
                    await ctx.guild.kick(member)
                except discord.Forbidden:
                    await ctx.send(f"Skipping member {member} due to discord.Forbidden exception.")
            await ctx.send("Allkick complete.")
        elif str(reaction.emoji) == "❎":
            return await ctx.send("Allkick cancelled.")

    @commands.command(name="allban", brief="Bans everyone in the server. Use this wisely.",
                      description="Bans everyone in the server. Skips unbannable members.\n"
                                  "Restricted to Administrator.")
    @commands.bot_has_permissions(ban_members=True)
    @commands.has_permissions(ban_members=True)
    async def allban(self, ctx):
        message = await ctx.send("\U00002757WARNING\U00002757 This command will **ban everyone** in the server "
                                 "except unbannable members. Are you sure you want to proceed?")
        await message.add_reaction("\U00002705")
        await message.add_reaction("\U0000274e")
        try:
            reaction, user = await self.bot.wait_for("reaction_add",
                                                     check=lambda r, u: r.message.id == message.id and u == ctx.author and str(r.emoji) in ["✅", "❎"],
                                                     timeout=10)
        except asyncio.TimeoutError:
            return await ctx.send("Operation cancelled due to lack of response.")
        if str(reaction.emoji) == "✅":
            await ctx.send("\U00002699Processing...\U00002699")
            for member in ctx.guild.members:
                try:
                    await ctx.guild.ban(member)
                except discord.Forbidden:
                    await ctx.send(f"Skipping member {member} due to discord.Forbidden exception.")
            await ctx.send("Allban complete.")
        elif str(reaction.emoji) == "❎":
            return await ctx.send("Allban cancelled.")

    @commands.command(name="allunban", brief="Unbans everyone who has been banned from the server.",
                      description="Unbans everyone who is currently banned from the server.\n"
                                  "Restricted to Administrator.")
    @commands.bot_has_permissions(ban_members=True)
    @commands.has_permissions(ban_members=True)
    async def allunban(self, ctx):
        message = await ctx.send("\U00002757WARNING\U00002757 This command will **unban everyone** in the server "
                                 ". Are you sure you want to proceed?")
        await message.add_reaction("\U00002705")
        await message.add_reaction("\U0000274e")
        try:
            reaction, user = await self.bot.wait_for("reaction_add",
                                                     check=lambda r, u: r.message.id == message.id and u == ctx.author and str(r.emoji) in ["✅", "❎"],
                                                     timeout=10)
        except asyncio.TimeoutError:
            return await ctx.send("Operation cancelled due to lack of response.")
        if str(reaction.emoji) == "✅":
            await ctx.send("\U00002699Processing...\U00002699")
            banlist = await ctx.guild.bans()
            for banned in banlist:
                await ctx.guild.unban(banned[1])
            await ctx.send("Allunban complete.")
        elif str(reaction.emoji) == "❎":
            return await ctx.send("Allunban cancelled.")


def setup(bot):
    bot.add_cog(Administrator(bot))
