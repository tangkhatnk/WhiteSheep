import discord
from discord.ext import commands
import asyncio

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_command_category(self, command):
        """Xác định category của lệnh dựa vào cog path"""
        if not command.cog:
            return None
        
        cog_name = command.cog.__class__.__module__  # Ví dụ: cogs.eco.daily
        if 'eco' in cog_name:
            return 'Economy'
        elif 'sys' in cog_name:
            return 'System'
        elif 'gamble' in cog_name:
            return 'Gamble'
        return None

    def create_embed_pages(self):
        """Tạo các trang help tự động từ commands"""
        categories = {
            'Economy': {
                'emoji': '💰',
                'color': discord.Color.gold(),
                'desc': 'Các lệnh về Sheep Coin',
                'commands': []
            },
            'System': {
                'emoji': '⚙️',
                'color': discord.Color.blue(),
                'desc': 'Các lệnh hệ thống',
                'commands': []
            },
            'Gamble': {
                'emoji': '🎲',
                'color': discord.Color.red(),
                'desc': 'Các lệnh minigame',
                'commands': []
            }
        }

        # Phân loại lệnh vào categories
        for command in self.bot.commands:
            if command.hidden:
                continue
                
            category = self.get_command_category(command)
            if category in categories:
                categories[category]['commands'].append(command)

        # Tạo embed cho mỗi category
        pages = []
        for idx, (cat_name, cat_data) in enumerate(categories.items(), 1):
            embed = discord.Embed(
                title=f"{cat_data['emoji']} {cat_name} Commands",
                description=cat_data['desc'],
                color=cat_data['color']
            )

            # Thêm các lệnh vào embed
            if cat_data['commands']:
                for cmd in sorted(cat_data['commands'], key=lambda x: x.name):
                    name = f"`v.{cmd.name}` → {(cmd.description or 'Không có mô tả').lower()}"
                    embed.add_field(name=name, value="", inline=False)
            else:
                embed.add_field(
                    name="Không có lệnh",
                    value="Chưa có lệnh nào trong mục này.",
                    inline=False
                )

            embed.set_footer(text=f"Trang {idx}/3 • {cat_name} Commands")
            pages.append(embed)

        return pages

    @commands.command(
        name="help",
        description="Xem danh sách lệnh",
        usage="v.help"
    )
    async def help(self, ctx):
        pages = self.create_embed_pages()
        current_page = 0
        message = await ctx.send(embed=pages[current_page])

        # Thêm reactions để lật trang
        reactions = ["<:lefth:1404710803797442560>", "<:righth:1404710862371033130>"]
        for reaction in reactions:
            await message.add_reaction(reaction)

        def check(reaction, user):
            return (
                user == ctx.author
                and str(reaction.emoji) in reactions
                and reaction.message.id == message.id
            )

        while True:
            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add",
                    check=check
                )

                if str(reaction.emoji) == "<:lefth:1404710803797442560>":
                    current_page = max(0, current_page - 1)
                elif str(reaction.emoji) == "<:righth:1404710862371033130>":
                    current_page = min(len(pages) - 1, current_page + 1)

                await message.edit(embed=pages[current_page])
                await message.remove_reaction(reaction, user)

            except Exception as e:
                print(f"Error in help command: {e}")
                break

async def setup(bot):
    await bot.add_cog(Help(bot))