import discord
from discord.ext import commands
import aiohttp


class Travitia:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="chat", brief="Chat with KaeBot using the Travitia API.",
                      description="Chat with KaeBot using the Travitia API.")
    async def chat(self, ctx):
        chatcontext = []
        await ctx.send("You started chatting with KaeBot! Type `.close.` to stop chatting.")
        while True:
            message = await self.bot.wait_for("message",
                                              check=lambda m: m.author == ctx.author and m.channel == ctx.channel)

            if not 3 <= len(message.content) <= 60:
                await ctx.send("Your message must be between 3 and 60 characters.")
            elif message.content == ".close.":
                return await ctx.send("Chat closed. Have a nice day!")
            else:
                async with ctx.channel.typing():
                    async with aiohttp.ClientSession() as session:
                        response = await session.post("https://public-api.travitia.xyz/talk",
                                                      json={"text": message.content, "context": chatcontext},
                                                      headers={"authorization": self.bot.TRAVITIAKEY})
                        responsetext = (await response.json())["response"]
                        await ctx.send(responsetext)

                chatcontext.clear()
                chatcontext.append(message.content)
                chatcontext.append(responsetext)


def setup(bot):
    bot.add_cog(Travitia(bot))
