import discord
from discord.ext import commands

class HelpPrefix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='help')
    async def help(self, ctx):
        embed = discord.Embed(
            title="**White 🤍 sheep** *help*",
            description="**lệnh của cừu nè<3**\n **prefix** : `v.`",
            color=discord.Color.blue()
        )

        for cog in self.bot.cogs.values():
            commands_list = []
            for command in cog.walk_commands():
                if command.name == "help":
                    continue  
                commands_list.append(f'`{command.name}`: {command.help or "Không có mô tả"}')
            if commands_list:
                embed.add_field(
                    name=f"🤍 **{cog.__cog_name__}**",
                    value='\n'.join(commands_list),
                    inline=False
                )

        embed.set_image(url='https://media.discordapp.net/attachments/1390268596889849938/1392859695781249195/love-live-mei-yoneme_1.gif?ex=6871112d&is=686fbfad&hm=0c133d53b90be5cb38aa8f78c138f4054684cf0e0a62d97f47122f89c31acb00&=&width=550&height=308')
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpPrefix(bot))
