import discord
from discord.ext import commands
import aiohttp, json, random, xmltodict


class NSFW(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="rule34",
        brief="Search rule34.xxx for a tag or tags.",
        description="Search rule34.xxx for one or more tags and return a post.\n Aliased to r34.",
        aliases=["r34"],
    )
    @commands.is_nsfw()
    async def rule34(self, ctx, *, tags):
        embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
        embed.set_footer(text=f"{self.bot.KAEBOT_VERSION} | Searched tags: {tags}")
        embed.set_author(name=f"Random result for '{tags}':", icon_url=self.bot.user.avatar_url)
        async with ctx.channel.typing():
            async with aiohttp.ClientSession() as session:
                posturl = (
                    f"https://rule34.xxx/index.php?page=dapi&s=post&q=index&tags={tags.replace(' ', '+')}&limit=100"
                )
                async with session.post(posturl) as response:
                    postdict = json.loads(json.dumps(xmltodict.parse((await response.read()).decode("utf-8"))))
                    try:
                        randompost = random.choice(postdict["posts"]["post"])
                    except KeyError:
                        return await ctx.send("No results found.")
                    embed.set_image(url=randompost["@file_url"])
                    await ctx.send(embed=embed)

    # @commands.command(
    #     name="saucenao",
    #     brief="Search on saucenao.com for an attached image or image url.",
    #     description="Search on saucenao.com for an attached image or image url."
    # )
    # @commands.is_nsfw()
    # async def saucenao(self, ctx):
    #     try:
    #         await ctx.send(ctx.message.attachments[0].url)
    #     except IndexError:
    #         await ctx.send(ctx.message.embeds[0].image.url)

    @commands.group(
        name="nhentai",
        brief="A command group for commands that connect to nhentai's API.",
        description="A command group for commands that connect to nhentai's API.",
    )
    @commands.is_nsfw()
    async def nhentai(self, ctx):
        if not ctx.invoked_subcommand:
            embed = discord.Embed(colour=discord.Color.from_rgb(81, 0, 124))
            embed.set_footer(text=self.bot.KAEBOT_VERSION)
            embed.set_author(name="KaeBot", icon_url="https://i.ibb.co/dBVGPwC/Icon.png")

            subcommands = ""
            for comm in NSFW.nhentai.commands:
                subcommands += comm.name
            embed.add_field(
                name="No command specified.", value=f"Please specify a subcommand: {subcommands}", inline=False
            )
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(NSFW(bot))
