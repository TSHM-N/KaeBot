import discord
from discord.ext import commands


def ctx_admin_or_botowner():
    def predicate(ctx):
        pass
    return commands.check(predicate)
