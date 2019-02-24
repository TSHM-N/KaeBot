import discord
from discord.ext import commands


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="help",
        brief="Shows this message.",
        description="Shows a list of commands. If a command argument is specified, attempts to show a description for "
                    "that command."
    )
    async def help(self, ctx, *, command=None):
        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=self.bot.KAEBOT_VERSION)
        embed.set_author(name="KaeBot Help", icon_url="https://i.ibb.co/dBVGPwC/Icon.png")

        if command is None or self.bot.get_command(command) is None:
            for cog in self.bot.cogs:
                embedstr = ""
                if self.bot.cogs[cog].get_commands():  # Make sure commandless cogs aren't included
                    for com in self.bot.cogs[cog].get_commands():
                        if com.hidden:
                            continue

                        if isinstance(com, commands.Group):  # If command has subcommands
                            embedstr += f"__{com.name}__ - {com.brief}\n"
                            for subcom in com.commands:
                                embedstr += f"⎣ __{subcom.name}__ - {subcom.brief}\n"
                        else:
                            embedstr += f"__{com.name}__ - {com.brief}\n"
                    if embedstr:  # Used to pass over cogs that might have only hidden commands, like jishaku
                        embed.add_field(name=cog, value=embedstr, inline=False)

        else:
            command = self.bot.get_command(command)
            embedstr = ""
            embedstr += f"*Belongs to cog '{command.cog_name}'*\n"
            if command.full_parent_name:
                embedstr += f"*Subcommand of command '{command.full_parent_name}'*\n"
            if command.aliases:
                embedstr += "*Aliased to "
                for alias in command.aliases:
                    embedstr += f"'{alias}', "
                embedstr = embedstr[:-2] + "*\n"

            embedstr += f"\n{command.description}\n"
            if isinstance(command, commands.Group):  # If has subcommands
                embedstr += "**Subcommands: **\n"
                for subcom in command.commands:
                    embedstr += f"__{subcom.name}__ - {subcom.brief}\n"

            embed.add_field(name=f"Help for command '__{command.name}__'", value=embedstr, inline=False)

        if self.bot.pm_help:
            try:
                await ctx.author.send(embed=embed)
            except discord.errors.Forbidden:
                embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
                embed.set_footer(text=self.bot.KAEBOT_VERSION)
                embed.set_author(name="KaeBot Help", icon_url="https://i.ibb.co/dBVGPwC/Icon.png")
                embed.set_thumbnail(url="https://i.ibb.co/dBVGPwC/Icon.png")
                embed.add_field(name="Fatal Error:",
                                value="Unable to DM user.\nTry enabling DMs from server members and then using `help` "
                                      "again.")
                await ctx.send(embed=embed)
        else:
            await ctx.send(embed=embed)


def setup(bot):
    bot.remove_command("help")
    bot.add_cog(Help(bot))
