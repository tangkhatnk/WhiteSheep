import discord
from discord.ext import commands
import random
from database import get_user_data, update_user_data

class Luck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="pray", help="Cầu may, tăng luck cho bản thân hoặc người khác (cooldown 2h)")
    @commands.cooldown(rate=1, per=7200, type=commands.BucketType.user)
    async def pray(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        user_data = get_user_data(target.id)
        if user_data is None:
            return await ctx.send("Người này chưa có tài khoản!")
        balance, last_daily, streak, win_rate, luck = user_data

        if luck >= 0:
            luck += 1
            win_rate += 0.01
        else:
            luck += 1
            win_rate += 0.1

        update_user_data(target.id, balance, last_daily, streak, win_rate, luck)
        await ctx.send(f"🙏 {ctx.author.mention} đã cầu may và nhận được **+1 luck** cho {target.mention}! (Luck hiện tại: {luck})")

    @commands.command(name="curse", help="Nguyền rủa bản thân hoặc người khác, giảm luck (cooldown 1h)")
    @commands.cooldown(rate=1, per=7200, type=commands.BucketType.user)
    async def curse(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        user_data = get_user_data(target.id)
        if user_data is None:
            return await ctx.send("Người này chưa có tài khoản!")
        balance, last_daily, streak, win_rate, luck = user_data

        # Logic giảm luck như bạn muốn
        if luck > 0:
            luck -= 1
            win_rate -= 0.01
        else:
            luck -= 1
            win_rate -= 0.1

        update_user_data(target.id, balance, last_daily, streak, win_rate, luck)
        await ctx.send(f"💀 {ctx.author.mention} đã nguyền rủa {target.mention} và lấy đi **1 luck**! (Luck hiện tại: {luck})")

    @pray.error
    @curse.error
    async def luck_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            hours = error.retry_after / 3600
            await ctx.send(f"⏳ Bạn cần chờ {hours:.2f} giờ trước khi dùng lại lệnh này.")

async def setup(bot):
    await bot.add_cog(Luck(bot))