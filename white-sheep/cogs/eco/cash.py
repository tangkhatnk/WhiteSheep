import discord
from discord.ext import commands
from database import get_user_data, update_user_data

class Cash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="cash", description="Kiểm tra số dư Sheep Coin của bạn")
    async def cash(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user_data = get_user_data(member.id)
        if user_data is None:
            await ctx.send(f"{member.display_name} chưa có tài khoản")
            return
        _, balance, *_ = user_data
        await ctx.send(f"💰 Số dư Sheep Coin của **{member.display_name}**: `{balance}` xu")

    @commands.command(name="give", description="Chuyển Sheep Coin cho người khác.")
    async def give(self, ctx, member: discord.Member, amount: int):
        if member is None:
            await ctx.send("Vui lòng tag người nhận. Ví dụ: v.give @tennguoi 100")
            return
        if member.bot:
            await ctx.send("Không thể chuyển coin cho bot.")
            return
        if amount is None or amount <= 0:
            await ctx.send("Số tiền phải là số dương.")
            return
        if member.id == ctx.author.id:
            await ctx.send("Bạn không thể tự chuyển cho chính mình.")
            return

        sender_row = get_user_data(ctx.author.id)
        if sender_row is None:
            await ctx.send("Bạn chưa có tài khoản. Dùng `v.start` để tạo tài khoản!")
            return
        receiver_row = get_user_data(member.id)
        if receiver_row is None:
            await ctx.send(f"{member.display_name} chưa có tài khoản. Yêu cầu họ dùng `v.start` trước!")
            return

        s_user_id, s_balance, s_last_daily, s_streak, s_win_rate, s_luck, s_so_ve, s_hsd, s_level, s_exp, s_invite = sender_row
        r_user_id, r_balance, r_last_daily, r_streak, r_win_rate, r_luck, r_so_ve, r_hsd, r_level, r_exp, r_invite = receiver_row

        if (s_balance or 0) < amount:
            await ctx.send("Số dư của bạn không đủ để chuyển.")
            return

        new_sender_balance = (s_balance or 0) - amount
        new_receiver_balance = (r_balance or 0) + amount

        update_user_data(s_user_id, new_sender_balance, s_last_daily, s_streak, s_win_rate, s_luck, s_so_ve, s_hsd, s_level, s_exp, s_invite)
        update_user_data(r_user_id, new_receiver_balance, r_last_daily, r_streak, r_win_rate, r_luck, r_so_ve, r_hsd, r_level, r_exp, r_invite)

        await ctx.send(f"✅ {ctx.author.mention} đã chuyển `{amount}` xu cho {member.mention}. Số dư mới của bạn: `{new_sender_balance}` xu.")

async def setup(bot):
    await bot.add_cog(Cash(bot))