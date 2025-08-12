import discord
from discord.ext import commands
import random
from datetime import datetime, timedelta, timezone
from database import get_user_data, update_user_data

# Lấy ngày theo múi giờ Việt Nam
VN_TZ = timezone(timedelta(hours=7))
today = datetime.now(VN_TZ).date()

class Daily(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="daily", description="Nhận thưởng mỗi ngày")
    async def daily(self, ctx):
        user_id = ctx.author.id
        # Sau đó dùng biến `today` này để so sánh và lưu ngày nhận daily.

        user_data = get_user_data(user_id)
        if user_data is None:
            await ctx.send("Bạn chưa có tài khoản. Hãy dùng lệnh `v.start` để tạo tài khoản!!")
            return
        _, balance, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite = user_data
        # Nếu chưa từng nhận hoặc lỗi định dạng thì reset
        try:
            last_claim_date = datetime.strptime(last_daily, "%Y-%m-%d").date() if last_daily else None
        except:
            last_claim_date = None

        if last_claim_date == today:
            embed = discord.Embed(
                title="❌ Đã nhận hôm nay rồi!",
                description="Bạn đã nhận quà **daily** hôm nay rồi. Quay lại vào ngày mai nhé!",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcmZ4cjJlaWU3YWRpa2theXR6djF6OHJiczFhNTd1a291dnhlbTc2OCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/EoDAU6MpWt2Xm/giphy.gif")
            await ctx.send(embed=embed)
            return

        # Tính chuỗi streak
        if last_claim_date == today - timedelta(days=1):
            streak = min(streak + 1, 20)
        else:
            streak = 1

        # Tính thưởng đúng yêu cầu
        reward = random.randint(50 + 2*streak, 100 + 2*streak)
        new_balance = balance + reward

        # Cập nhật DB
        update_user_data(user_id, new_balance, today.strftime("%Y-%m-%d"), streak, win_rate, luck, so_ve, hsd, level, exp, invite)

        # Tạo embed đẹp
        embed = discord.Embed(
            title="<:gold:1404709251628273716> Quà Daily của bạn nè!",
            description=(
                f"<a:money:1404706665508503582> **Bạn nhận được:** `{reward}` xu\n"
                f"<a:streak:1404706786543669329> **Chuỗi đăng nhập liên tục:** `{streak} ngày`\n"
                f"<:bag:1404706944786108466> **Số dư mới:** `{new_balance} xu`\n\n"
                f"<a:star:1404707038340059206> Hãy quay lại vào ngày mai để nhận thêm quà!"
            ),
            color=discord.Color.gold()
        )
        embed.set_author(name=ctx.author.display_name, icon_url = ctx.author.avatar.url if ctx.author.avatar else None)
        embed.set_thumbnail(url="")
        embed.set_image(url ="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcmZ4cjJlaWU3YWRpa2theXR6djF6OHJiczFhNTd1a291dnhlbTc2OCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/MkvZFvzHIWbRK/giphy.gif")
        embed.set_footer(text="Sheep Bot • Daily Rewards", icon_url="")

        await ctx.send(embed = embed)

    @daily.error
    async def daily_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            hours = int(error.retry_after / 3600)
            minutes = int((error.retry_after % 3600) / 60)
            seconds = int(error.retry_after % 60)
            await ctx.send(f"⏱ | {ctx.author.name}! You need to wait {hours}H {minutes}M {seconds}S")

async def setup(bot):
    await bot.add_cog(Daily(bot))