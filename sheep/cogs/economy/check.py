import discord
from discord.ext import commands
from database import setup_database, get_user_data, update_user_data


class CheckCash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @commands.command(name = "cash", description = "Kiểm tra số dư")
    async def cash(self, ctx):
        user_id = ctx.author.id
        user_data = get_user_data(user_id)
        if user_data is None:
            await ctx.send("Bạn chưa có tài khoản. Hãy dùng lệnh đăng ký trước!")
            return
        balance, last_daily, streak, win_rate, luck = user_data

        if balance is not None:
            await ctx.send(f"**{ctx.author.name}**, số dư của bạn là: **{balance} sheep coin**.")
        else:
            await ctx.send(f"**{ctx.author.name}**, bạn chưa có tài khoản. Hãy sử dụng `v.start` để tạo tài khoản.")

async def setup(bot):
    await bot.add_cog(CheckCash(bot))