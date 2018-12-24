import discord
from discord.ext import commands
import re, difflib


class ErrorHandler:
    def __init__(self, bot):
        self.bot = bot

    async def on_command_error(self, ctx, error):
        embed = discord.Embed(title="Fatal Error:", colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=self.bot.KAEBOT_VERSION)
        embed.set_thumbnail(url="https://cdn.pbrd.co/images/HGYlRKR.png")

        if hasattr(ctx.command, "on_error"):
            return

        if isinstance(error, commands.CheckFailure):
            return

        if isinstance(error, commands.CommandNotFound):
            try:
                invalidcommand = re.findall(r"\"([^\"]*)\"", error.args[0])[0]
            except IndexError:
                invalidcommand = None
            similar = difflib.get_close_matches(
                invalidcommand, self.bot.strcommands, n=5, cutoff=0.6
            )  # Get similar words

            similarstr = ""
            if not similar:
                similarstr = "No matches found."
            else:
                for simstr in similar:
                    similarstr += f"{simstr}\n"

            embed.add_field(name="Invalid command. Did you mean:", value=similarstr, inline=False)

        else:
            embed.add_field(name="An unhandled exception occurred.", value=str(error), inline=False)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
