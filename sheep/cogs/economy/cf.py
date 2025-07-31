import discord
from discord.ext import commands
import random
from database import get_user_data, update_user_data

class CF(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="cf", help="Tung đồng xu cược coin: v.cf <số tiền> <heads/tails>")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def cf(self, ctx, amount: int = None, choice: str = None):
        user_id = ctx.author.id
        user_data = get_user_data(user_id)
        if user_data is None:
            return await ctx.send("Bạn chưa có tài khoản. Hãy dùng lệnh đăng ký trước!")
        balance, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite = user_data
        if amount is None or choice is None:
            return await ctx.send("Cú pháp: v.cf <số tiền> <heads/tails>")
        if amount <= 0:
            return await ctx.send("Số tiền phải lớn hơn 0!")
        if amount > 250_000:
            amount = 250_000
        if amount > balance:
            return await ctx.send(f"Bạn không đủ coin để cược `{amount}`!")

        choice = choice.lower()
        if choice not in ["heads", "tails", "h", "t"]:
            return await ctx.send("Bạn chỉ được chọn heads hoặc tails!")
        user_choice = "heads" if choice in ["heads", "h"] else "tails"

        # Tung đồng xu
        result = random.choice(["heads", "tails"])
        win = (user_choice == result)
        new_balance = balance + amount if win else balance - amount
        update_user_data(user_id, new_balance, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite)

        # Soạn tin nhắn kết quả
        msg = f"{ctx.author.mention} spent 🧾 `{amount:,}` and chose **{user_choice}**\nThe coin spins... "
        msg += "🪙"
        if win:
            msg += f"and you won `{amount * 2:,}`! 🎉"
        else:
            msg += f"and you lost it all.... :c"
        await ctx.send(msg)

    @cf.error
    async def cf_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ Bạn cần chờ {error.retry_after:.1f} giây trước khi dùng lại lệnh này.")

async def setup(bot):
    await bot.add_cog(CF(bot)) 