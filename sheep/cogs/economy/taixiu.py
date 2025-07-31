import discord
from discord.ext import commands
import asyncio
import random
from database import get_user_data, update_user_data

class TaiXiu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lose_streak = {}  # user_id: số trận thua liên tiếp

    @commands.command(name="taixiu")
    @commands.cooldown(rate=1, per=8, type=commands.BucketType.user)
    async def taixiu(self, ctx, prize: str = None):
        user_id = ctx.author.id
        user_data = get_user_data(user_id)

        if user_data is None:
            return await ctx.send("⚠️ Bạn chưa có tài khoản. Hãy dùng lệnh đăng ký trước!")
        balance, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite = user_data

        if prize is None:
            return await ctx.send("Bạn phải nhập số tiền cược!")

        original_prize = prize
        if prize.lower() == "all":
            prize = min(balance, 250000)
            win_rate = max(0, win_rate - 10)  # Giảm 10% tỉ lệ thắng, không nhỏ hơn 0
        else:
            try:
                prize = int(prize)
                if prize > 250000:
                    prize = 250000
            except ValueError:
                return await ctx.send("Số tiền cược không hợp lệ!")

        if prize <= 0:
            return await ctx.send(embed=discord.Embed(
                description="⚠️ Số tiền cược phải lớn hơn 0!",
                color=discord.Color.orange()
            ))

        if prize > balance:
            return await ctx.send(embed=discord.Embed(
                description=f"❌ Bạn không đủ xu để cược **{prize:,}đ**. Số dư hiện tại: **{balance:,}đ**.",
                color=discord.Color.red()
            ))

        emojis = {"🔴": "xỉu", "🟢": "tài"}

        # Bước 1: Random 1 con preview
        dice_preview = random.randint(1, 6)
        msg1 = await ctx.send(embed=discord.Embed(
            description=f"🎲 Xúc xắc xuất hiện: {dice_preview}",
            color=discord.Color.blurple()
        ))
        await asyncio.sleep(1.5)

        # Bước 2: Gửi embed chọn tài/xỉu như cũ
        embed = discord.Embed(
            title="🎮 Tài Xỉu - Chọn lựa của bạn",
            description=(
                f"{ctx.author.mention} đã cược **{prize:,}đ**!\n\n"
                "Hãy chọn bằng cách react:\n"
                "🔴 = **Xỉu**\n"
                "🟢 = **Tài**"
            ),
            color=discord.Color.random()
        )
        message = await ctx.send(embed=embed)

        for emoji in emojis:
            await message.add_reaction(emoji)

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in emojis and reaction.message.id == message.id

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
        except asyncio.TimeoutError:
            return await ctx.send(embed=discord.Embed(
                description="⏰ Hết thời gian chọn! Vui lòng thử lại sau.",
                color=discord.Color.red()
            ))

        choice = emojis[str(reaction.emoji)]

        # Lấy số trận thua liên tiếp
        lose_streak = self.lose_streak.get(user_id, 0)
        # Nếu thua >= 3 ván thì tăng win_rate dần theo cấp: 3 ván = 70%, 4 ván = 80%, >=5 ván = 90%
        custom_win_rate = win_rate
        if lose_streak == 3:
            custom_win_rate = 70
        elif lose_streak == 4:
            custom_win_rate = 80
        elif lose_streak >= 5:
            custom_win_rate = 90
        # Nếu đánh all in thì giảm 10% tỉ lệ thắng cuối cùng

        # Quyết định thắng/thua
        win = random.random() < (custom_win_rate / 100)
        if win:
            result = choice
        else:
            result = "tài" if choice == "xỉu" else "xỉu"

        def generate_dice_with_preview(preview, result):
            # Random 2 con còn lại sao cho tổng 3 con đúng tài/xỉu
            while True:
                dice2 = [random.randint(1, 6) for _ in range(2)]
                dice = [preview] + dice2
                total = sum(dice)
                if (result == "tài" and total > 10) or (result == "xỉu" and total <= 10):
                    return dice

        dice = generate_dice_with_preview(dice_preview, result)
        total = sum(dice)
        result_real = "xỉu" if total <= 10 else "tài"
        win_result = (choice == result_real)
        new_balance = balance + prize if win_result else balance - prize

        # Cập nhật lose_streak
        if win_result:
            self.lose_streak[user_id] = 0
        else:
            self.lose_streak[user_id] = lose_streak + 1

        # Cập nhật database
        update_user_data(
            user_id,
            new_balance,
            last_daily,
            streak,
            win_rate,
            luck,
            so_ve,
            hsd,
            level,
            exp,
            invite
        )

        result_embed = discord.Embed(
            title="🎲 Kết quả Tài Xỉu",
            color=discord.Color.green() if win_result else discord.Color.red()
        )
        result_embed.set_thumbnail(url="https://media.tenor.com/i6UYeLKWyCoAAAAd/dice-roll.gif")
        result_embed.add_field(name="🎲 Xúc xắc", value=f"`{' + '.join(map(str, dice))} = {total}`", inline=False)
        result_embed.add_field(name="📢 Kết quả", value=f"**{result.upper()}**", inline=True)
        result_embed.add_field(name="🧑‍💼 Người chơi", value=ctx.author.mention, inline=True)
        result_embed.add_field(name="🔎 Bạn chọn", value=f"**{choice.upper()}**", inline=True)
        result_embed.add_field(
            name="🎉 Trạng thái",
            value="✅ Bạn **THẮNG**!" if win_result else "❌ Bạn **THUA**!",
            inline=False
        )
        result_embed.add_field(name="💰 Số dư mới", value=f"**{new_balance:,}đ**", inline=False)

        await message.edit(embed=result_embed)
        await msg1.delete()

    @taixiu.error
    async def taixiu_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                description=f"⏳ Bạn cần chờ **{error.retry_after:.1f} giây** trước khi dùng lại lệnh này.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed, delete_after=5)

async def setup(bot):
    await bot.add_cog(TaiXiu(bot))
