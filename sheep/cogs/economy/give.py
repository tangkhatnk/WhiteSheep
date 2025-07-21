import discord
from discord.ext import commands
from database import get_user_data, update_user_data

class GiveCoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="give", help="Tặng tiền cho người khác. Cú pháp: v.give @user <số tiền>")
    async def give(self, ctx, member: discord.Member = None, amount: int = None):
        giver = ctx.author

        # Kiểm tra người nhận và số tiền
        if member is None or amount is None:
            return await ctx.send("❌ Vui lòng nhập đúng cú pháp: `v.give @user <số tiền>`.")

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

        giver_balance, giver_last_daily, giver_streak, giver_win_rate, giver_luck = giver_data
        receiver_balance, receiver_last_daily, receiver_streak, receiver_win_rate, receiver_luck = receiver_data

        # Kiểm tra đủ tiền
        if giver_balance < amount:
            return await ctx.send("❌ Bạn không đủ tiền để tặng.")

        # Cập nhật dữ liệu
        update_user_data(giver.id, giver_balance - amount, giver_last_daily, giver_streak, giver_win_rate, giver_luck)
        update_user_data(member.id, receiver_balance + amount, receiver_last_daily, receiver_streak, receiver_win_rate, receiver_luck)

        # Gửi phản hồi dạng tin nhắn thường
        await ctx.send(f"🎁 {giver.mention} đã tặng `{amount}` **sheepcoin** cho {member.mention}!")

async def setup(bot):
    await bot.add_cog(GiveCoin(bot))
