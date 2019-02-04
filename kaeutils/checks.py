import discord
from discord.ext import commands


def ctx_admin_or_botowner():
    async def predicate(ctx):
        return await ctx.bot.is_owner(ctx.author) or ctx.author.guild_permissions.administrator
    return commands.check(predicate)
