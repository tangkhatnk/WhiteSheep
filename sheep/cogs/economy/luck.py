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
        balance, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite = user_data

        if luck >= 0:
            luck += 1
            win_rate += 0.01
        else:
            luck += 1
            win_rate += 0.1

        update_user_data(target.id, balance, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite)
        await ctx.send(f"🙏 {ctx.author.mention} đã cầu may và nhận được **+1 luck** cho {target.mention}! (Luck hiện tại: {luck})")

    @commands.command(name="curse", help="Nguyền rủa bản thân hoặc người khác, giảm luck (cooldown 1h)")
    @commands.cooldown(rate=1, per=3600, type=commands.BucketType.user)
    async def curse(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        user_data = get_user_data(target.id)
        if user_data is None:
            return await ctx.send("Người này chưa có tài khoản!")
        balance, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite = user_data

        if luck > 0:
            luck -= 1
            win_rate -= 0.01
        else:
            luck -= 1
            win_rate -= 0.1

        update_user_data(target.id, balance, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite)
        await ctx.send(f"💀 {ctx.author.mention} đã nguyền rủa {target.mention} và lấy đi **1 luck**! (Luck hiện tại: {luck})")

    @pray.error
    @curse.error
    async def luck_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            seconds = int(error.retry_after)
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            time_str = []
            if hours > 0:
                time_str.append(f"{hours} giờ")
            if minutes > 0:
                time_str.append(f"{minutes} phút")
            if secs > 0 or not time_str:
                time_str.append(f"{secs} giây")
            time_str = " ".join(time_str)
            embed = discord.Embed(
                description=f"⏳ Bạn cần chờ **{time_str}** trước khi dùng lại lệnh này.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed, delete_after=5)

async def setup(bot):
    await bot.add_cog(Luck(bot))