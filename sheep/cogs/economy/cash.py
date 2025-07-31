import discord
from discord.ext import commands
import sqlite3
from database import get_user_data, update_user_data

DB_PATH = 'sheep.db'

class Cash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="`topcoin`", help="Xem top những người có coin cao nhất server")
    async def topcash(self, ctx):
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

    @commands.command(name="cash", description="Kiểm tra số dư")
    async def cash(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        user_data = get_user_data(target.id)
        if user_data is None:
            await ctx.send(f"{target.mention} chưa có tài khoản. Hãy dùng lệnh đăng ký trước!")
            return
        balance, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite = user_data
        await ctx.send(f"**{target.display_name}**, số dư là: **{balance:,} sheep coin**.")

    @commands.command(name="give", help="Tặng tiền cho người khác. Cú pháp: v.give @user <số tiền>")
    async def give(self, ctx, member: discord.Member = None, amount: int = None):
        giver = ctx.author
        # Kiểm tra người nhận và số tiền
        if member is None or amount is None:
            return await ctx.send("❌ Vui lòng nhập đúng cú pháp: `v.give @user <số tiền>`. ")
        if member.id == giver.id:
            return await ctx.send("❌ Bạn không thể tự tặng tiền cho chính mình.")
        if amount <= 0:
            return await ctx.send("❌ Số tiền phải lớn hơn 0.")
        # Kiểm tra tài khoản tồn tại
        giver_data = get_user_data(giver.id)
        if giver_data is None:
            return await ctx.send("❌ Bạn chưa có tài khoản. Hãy dùng lệnh đăng ký trước!")
        receiver_data = get_user_data(member.id)
        if receiver_data is None:
            return await ctx.send(f"❌ {member.name} chưa có tài khoản. Hãy bảo họ đăng ký trước!")
        giver_balance, giver_last_daily, giver_streak, giver_win_rate, giver_luck, giver_so_ve, giver_hsd, giver_level, giver_exp, giver_invite = giver_data
        receiver_balance, receiver_last_daily, receiver_streak, receiver_win_rate, receiver_luck, receiver_so_ve, receiver_hsd, receiver_level, receiver_exp, receiver_invite = receiver_data
        # Kiểm tra đủ tiền
        if giver_balance < amount:
            return await ctx.send("❌ Bạn không đủ tiền để tặng.")
        # Cập nhật dữ liệu
        update_user_data(giver.id, giver_balance - amount, giver_last_daily, giver_streak, giver_win_rate, giver_luck, giver_so_ve, giver_hsd, giver_level, giver_exp, giver_invite)
        update_user_data(member.id, receiver_balance + amount, receiver_last_daily, receiver_streak, receiver_win_rate, receiver_luck, receiver_so_ve, receiver_hsd, receiver_level, receiver_exp, receiver_invite)
        await ctx.send(f"🎁 {giver.mention} đã tặng `{amount}` **sheepcoin** cho {member.mention}!")

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

async def setup(bot):
    await bot.add_cog(Cash(bot)) 