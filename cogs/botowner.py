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
        if ctx.message.author.id == 283858617973604352:
            await ctx.send("KaeBot signing out.")
            await self.bot.kaedb.close()
            await self.bot.logout()
        else:
            await ctx.send("You lack the following permissions to do this:\n```css\nBot Owner\n```")

    @commands.command(
        name="restart", brief="Restarts KaeBot.", description="Restarts KaeBot. Only usable by Bot Owner."
    )
    async def restart(self, ctx):
        if ctx.message.author.id == 283858617973604352:
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
        if ctx.message.author.id == 283858617973604352:
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
        if ctx.message.author.id == 283858617973604352:
            async with self.bot.kaedb.acquire() as conn:
                async with conn.transaction():
                    if await conn.fetchrow("SELECT * FROM exiled_users WHERE user_id = $1", str(user.id)):
                        await conn.execute("DELETE FROM exiled_users WHERE user_id = $1", str(user.id))
                        await ctx.send(f"{user.mention} has been welcomed back.")
                    else:
                        await ctx.send("This user is not exiled.")
        else:
            await ctx.send("You lack the following permissions to do this:\n```css\nBot Owner\n```")


def setup(bot):
    bot.add_cog(BotOwner(bot))
