import discord
from discord.ext import commands


class Moderator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="kick",
        brief="Kicks a user.",
        description="Kicks a specified user. Only usable by users with the Kick Members permission.",
    )
    async def kick(self, ctx, user: discord.Member, *, reason=""):
        print(f"Attempted kick by {ctx.message.author}. Target: {user}")
        if ctx.message.author.guild_permissions.kick_members:
            await user.send(content=f"You have been kicked from {ctx.message.guild} by {ctx.message.author}.")
            if not reason == "":
                await user.send(content=f"Reason: '{reason}'")
            await user.kick(reason=reason)
            await ctx.send(f"{user} has been kicked.")
            print("Kick successful.")
        else:
            await ctx.send("You lack the following permissions to do this:\n```css\nKick Members\n```")
            print("Kick denied due to bad perms.")

    @commands.command(
        name="ban",
        brief="Bans a user.",
        description="Bans a specified user. Only usable by users with the Ban Members permission.",
    )
    async def ban(self, ctx, user: discord.Member, *, reason=""):
        print(f"Attempted ban by {ctx.message.author}. Target: {user}")
        if ctx.message.author.guild_permissions.ban_members:
            await user.send(content=f"You have been banned from {ctx.message.guild} by {ctx.message.author}.")
            if not reason == "":
                await user.send(content=f"Reason: '{reason}'")
            await user.ban(reason=reason, delete_message_days=0)
            await ctx.send(f"{user} has been banned. Their ID: {user.id}")
            print("Ban successful.")
        else:
            await ctx.send("You lack the following permissions to do this:\n```css\nBan Members\n```")
            print("Ban denied due to bad perms.")

    @commands.command(
        name="unban",
        brief="Unbans a user through their ID.",
        description="Unbans a specified user through their ID. Only usable by users with the Ban Members"
        " permission.",
    )
    async def unban(self, ctx, user: discord.User):
        print(f"Attempted unban by {ctx.message.author}. Target: {user}")
        if ctx.message.author.guild_permissions.ban_members:
            await ctx.message.guild.unban(user)
            await ctx.send(f"{user} unbanned.")
            print("Unban successful.")
        else:
            await ctx.send("You lack the following permissions to do this:\n```css\nBan Members\n```")
            print("Unban denied due to bad perms.")

    @commands.command(
        name="purge",
        brief="Purge the last specified messages.",
        description="Purge the last specified amount of messages.",
    )
    async def purge(self, ctx, limit: int):
        if limit <= 0 or limit > 100:
            return await ctx.send("Invalid range: must be between 0 - 100 messages.")
        await ctx.message.delete()
        await ctx.channel.purge(limit=limit)


def setup(bot):
    bot.add_cog(Moderator(bot))
