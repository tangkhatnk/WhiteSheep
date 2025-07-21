import discord
from discord.ext import commands
import asyncio
import random
from database import get_user_data, update_user_data

class TaiXiu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="taixiu")
    @commands.cooldown(rate=1, per=8, type=commands.BucketType.user)
    async def taixiu(self, ctx, prize: str = None):
        user_id = ctx.author.id
        user_data = get_user_data(user_id)

        if user_data is None:
            return await ctx.send("⚠️ Bạn chưa có tài khoản. Hãy dùng lệnh đăng ký trước!")
        balance, last_daily, streak, win_rate, luck = user_data

        if prize is None:
            return await ctx.send("Bạn phải nhập số tiền cược!")

        if prize.lower() == "all":
            prize = min(balance, 1000)
        else:
            try:
                prize = int(prize)
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

        emojis = {"🔴": "tài", "🟢": "xỉu"}

        # Bước 1: Gửi thông báo chuẩn bị tung xúc xắc
        msg1 = await ctx.send(embed=discord.Embed(
            description="🎲 Chuẩn bị tung xúc xắc...",
            color=discord.Color.blurple()
        ))
        await asyncio.sleep(1.5)

        # Bước 2: Random 1 mặt xúc xắc và show ra
        dice_preview = random.randint(1, 6)
        dice_str = str(dice_preview)
        msg2 = await ctx.send(embed=discord.Embed(
            description=f"🎲 Xúc xắc xuất hiện: {dice_str}",
            color=discord.Color.blurple()
        ))
        await asyncio.sleep(1.5)

        # Bước 3: Gửi embed chọn tài/xỉu như cũ
        embed = discord.Embed(
            title="🎮 Tài Xỉu - Chọn lựa của bạn",
            description=(
                f"{ctx.author.mention} đã cược **{prize:,}đ**!\n\n"
                "Hãy chọn bằng cách react:\n"
                "🔴 = **Tài**\n"
                "🟢 = **Xỉu**"
            ),
            color=discord.Color.random()
        )
        message = await ctx.send(embed=embed)

        # (Sau khi xong có thể xóa msg1, msg2 nếu muốn)
        

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
        win = random.random() < (win_rate / 100)

        if win:
            result = random.randint(1, 9)
            result = choice if result % 2 == 0 else ("xỉu" if choice == "tài" else "tài")
        else:
            result = "xỉu" if choice == "tài" else "tài"

        def generate_dice_for(result):
            while True:
                dice = [random.randint(1, 6) for _ in range(3)]
                total = sum(dice)
                if ("tài" if 11 <= total <= 17 else "xỉu") == result:
                    return dice

        dice = generate_dice_for(result)
        total = sum(dice)

        win_result = (choice == result)
        new_balance = balance + prize if win_result else balance - prize

        # Cập nhật database
        update_user_data(
            user_id,
            new_balance,
            last_daily,
            streak,
            win_rate,
            luck
        )

        result_embed = discord.Embed(
            title="🎲 Kết quả Tài Xỉu",
            color=discord.Color.green() if win_result else discord.Color.red()
        )
        result_embed.set_thumbnail(url="https://media.tenor.com/i6UYeLKWyCoAAAAd/dice-roll.gif")
        result_embed.add_field(name="🎲 Xúc xắc", value=f"`{' + '.join(map(str, dice))} = {total}`", inline=False)
        result_embed.add_field(name="📢 Kết quả", value=f"**{result.upper()}**", inline=True)
        result_embed.add_field(name="🧑‍💼 Người chơi", value=ctx.author.mention, inline=True)
        result_embed.add_field(
            name="🎉 Trạng thái",
            value="✅ Bạn **THẮNG**!" if win_result else "❌ Bạn **THUA**!",
            inline=False
        )
        result_embed.add_field(name="💰 Số dư mới", value=f"**{new_balance:,}đ**", inline=False)

        await message.edit(embed=result_embed)
        await msg1.delete()
        await msg2.delete()

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
