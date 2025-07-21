import discord
from discord.ext import commands
import random
from datetime import datetime, timedelta
from database import get_user_data, update_user_data

class Daily(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="daily", description = "Nhận thưởng mỗi ngày")
    async def daily(self, ctx):
        user_id = ctx.author.id
        today = datetime.utcnow().date()

        user_data = get_user_data(user_id)
        if user_data is None:
            await ctx.send("Bạn chưa có tài khoản. Hãy dùng lệnh đăng ký trước!")
            return
        balance, last_daily, streak, win_rate, luck = user_data
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

        # Tính chuỗi đăng nhập liên tiếp
        if last_claim_date == today - timedelta(days=1):
            streak += 1
        else:
            streak = 1

        # Tính thưởng
        reward = random.randint(10, 40) + (streak * 2)
        new_balance = balance + reward

        # Cập nhật DB
        update_user_data(user_id, new_balance, today.strftime("%Y-%m-%d"), streak, win_rate, luck)

        # Tạo embed đẹp
        embed = discord.Embed(
            title="🎁 Quà Daily của bạn nè!",
            description=(
                f"💰 **Bạn nhận được:** `{reward}` xu\n"
                f"🔥 **Chuỗi đăng nhập liên tục:** `{streak} ngày`\n"
                f"💼 **Số dư mới:** `{new_balance} xu`\n\n"
                f"🌟 Hãy quay lại vào ngày mai để nhận thêm quà!"
            ),
            color=discord.Color.gold()
        )
        embed.set_author(name=ctx.author.display_name, icon_url = ctx.author.avatar.url if ctx.author.avatar else None)
        embed.set_thumbnail(url="")
        embed.set_image(url ="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcmZ4cjJlaWU3YWRpa2theXR6djF6OHJiczFhNTd1a291dnhlbTc2OCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/MkvZFvzHIWbRK/giphy.gif")
        embed.set_footer(text="Sheep Bot • Daily Rewards", icon_url="")

        await ctx.send(embed = embed)

async def setup(bot):
    await bot.add_cog(Daily(bot))
