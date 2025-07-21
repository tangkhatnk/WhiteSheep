import discord
from discord.ext import commands
import sqlite3

DB_PATH = 'sheep.db'

class TopCoinView(discord.ui.View):
    def __init__(self, bot, ctx, per_page=10, max_page=5):
        super().__init__(timeout = None)
        self.bot = bot
        self.ctx = ctx
        self.per_page = per_page
        self.max_page = max_page
        self.page = 1

    async def update_embed(self, interaction):
        offset = (self.page - 1) * self.per_page
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT ? OFFSET ?",
                (self.per_page, offset)
            )
            top_users = cursor.fetchall()

        desc = ""
        for idx, (user_id, balance) in enumerate(top_users, 1 + offset):
            member = self.ctx.guild.get_member(user_id)
            name = member.display_name if member else f"ID: {user_id}"
            desc += f"**{idx}.** {name} - `{balance:,} coin`\n"

        embed = discord.Embed(
            title=f"🏆 Top Coin Server (Trang {self.page}/{self.max_page})",
            description=desc or "Không có dữ liệu!",
            color=discord.Color.gold()
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 1:
            self.page -= 1
            await self.update_embed(interaction)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.max_page:
            self.page += 1
            await self.update_embed(interaction)
        else:
            await interaction.response.defer()

class TopCoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="topcoin", help="Xem top những người có coin cao nhất server")
    async def topcoin(self, ctx):
        view = TopCoinView(self.bot, ctx)
        # Lấy trang đầu tiên
        offset = 0
        per_page = view.per_page
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT ? OFFSET ?",
                (per_page, offset)
            )
            top_users = cursor.fetchall()

        desc = ""
        for idx, (user_id, balance) in enumerate(top_users, 1):
            member = ctx.guild.get_member(user_id)
            name = member.display_name if member else f"ID: {user_id}"
            desc += f"**{idx}.** {name} - `{balance:,} coin`\n"

        embed = discord.Embed(
            title=f"🏆 Top Coin Server (Trang 1/{view.max_page})",
            description=desc or "Không có dữ liệu!",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(TopCoin(bot)) 