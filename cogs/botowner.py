import discord
from discord.ext import commands
import os, random


class BotOwner:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="kill", brief="Shuts KaeBot down.", description="Forces Kaebot to shutdown. Only usable by Bot Owner."
    )
    async def kill(self, ctx):
        if await self.bot.is_owner(ctx.author):
            await ctx.send("KaeBot signing out.")
            await self.bot.kaedb.close()
            await self.bot.logout()
        else:
            await ctx.send("You lack the following permissions to do this:\n```css\nBot Owner\n```")

    @commands.command(
        name="restart", brief="Restarts KaeBot.", description="Restarts KaeBot. Only usable by Bot Owner."
    )
    async def restart(self, ctx):
        if await self.bot.is_owner(ctx.author):
            await ctx.send("Restarting...")
            # hacky af BUT it works
            os.system("py .\KBRestartHax.py")
            await self.bot.kaedb.close()
            await self.bot.logout()
        else:
            await ctx.send("You lack the following permissions to do this:\n```css\nBot Owner\n```")

    @commands.command(name="forceerror", brief="...", description="For testing. Bot Owner only.", hidden=True)
    async def error(self, ctx):
        if await self.bot.is_owner(ctx.author):
            errortype = random.choice([ValueError(), IndexError(), KeyError(), AttributeError()])
            raise errortype
        else:
            await ctx.send("You lack the following permissions to do this:\n```css\nBot Owner\n```")

    @commands.command(name="exile", brief="Stop bad users from accessing KaeBot.",
                      description="Stop bad users from accessing KaeBot.")
    async def exile(self, ctx, user: discord.User):
        if await self.bot.is_owner(ctx.author):
            async with self.bot.kaedb.acquire() as conn:
                async with conn.transaction():
                    if not await conn.fetchrow("SELECT * FROM exiled_users WHERE user_id = $1", str(user.id)):
                        await conn.execute("INSERT INTO exiled_users (user_id) VALUES ($1)", str(user.id))
                        await ctx.send(f"{user.mention} has been exiled...")
                    else:
                        await ctx.send(f"{user.mention} has already been exiled.")
        else:
            await ctx.send("You lack the following permissions to do this:\n```css\nBot Owner\n```")

    @commands.command(name="unexile", brief="Allow exiles to use KaeBot again.",
                      description="Allow exiled users to use KaeBot again.")
    async def unexile(self, ctx, user: discord.User):
        if await self.bot.is_owner(ctx.author):
            async with self.bot.kaedb.acquire() as conn:
                async with conn.transaction():
                    if await conn.fetchrow("SELECT * FROM exiled_users WHERE user_id = $1", str(user.id)):
                        await conn.execute("DELETE FROM exiled_users WHERE user_id = $1", str(user.id))
                        await ctx.send(f"{user.mention} has been welcomed back.")
                    else:
                        await ctx.send("This user is not exiled.")
        else:
            await ctx.send("You lack the following permissions to do this:\n```css\nBot Owner\n```")

    @commands.command(name="exilelist", brief="View all exiled users.",
                      description="View all exiled users. Any user can use this command.")
    async def exilelist(self, ctx):
        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=self.bot.KAEBOT_VERSION)
        async with self.bot.kaedb.acquire() as conn:
            async with conn.transaction():
                exiles = await conn.fetch("SELECT * FROM exiled_users")

        embedcontent = ""
        if not exiles:
            embedcontent = "No exiled users."
        else:
            for exile in exiles:
                embedcontent += f"{self.bot.get_user(int(exile['user_id'])).name}\n"
        embed.add_field(name="Exiled users:",
                        value=embedcontent,
                        inline=False)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(BotOwner(bot))
