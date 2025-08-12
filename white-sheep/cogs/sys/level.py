import discord
from discord.ext import commands
from database import get_user_data, update_user_data, create_user

class LevelSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        # Chỉ cho phép tăng exp ở 2 kênh nhất định và tin nhắn >= 10 ký tự
        ALLOWED_CHANNELS = [1340709545957396591, 1397963666594467860]
        if message.channel.id not in ALLOWED_CHANNELS:
            return
        if len(message.content) < 10:
            return
        user_id = message.author.id
        user_data = get_user_data(user_id)
        if not user_data:
            create_user(user_id)
            user_data = get_user_data(user_id)
        # Lấy dữ liệu đầy đủ
        _, balance, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite = user_data
        # Tăng exp mỗi lần chat
        exp += 1
        leveled_up = False
        # Kiểm tra lên level
        if exp >= 100 * level:
            exp = 0
            level += 1
            balance += 10000 * level
            leveled_up = True
        update_user_data(user_id, balance, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite)
        if leveled_up:
            try:
                embed = discord.Embed(
                    title="🎉 Level Up!",
                    description=f"{message.author.mention} đã lên level **{level}** và nhận **{10000*level}** coin!",
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url=message.author.avatar.url if message.author.avatar else discord.Embed.Empty)
                await message.channel.send(embed=embed)
            except:
                pass

    @commands.Cog.listener()
    async def on_command(self, ctx):
        user_id = ctx.author.id
        await self.add_exp(user_id, 1, ctx.channel, ctx.author)

    async def add_exp(self, user_id, exp_amount, channel, user):
        user_data = get_user_data(user_id)
        if user_data is None:
            return
        # Thêm _ để bỏ qua user_id
        _, balance, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite = user_data
        exp += exp_amount
        leveled_up = False
        while exp >= 100 * level:
            exp -= 100 * level
            level += 1
            balance += 10000 * level
            leveled_up = True
        update_user_data(user_id, balance, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite)
        if leveled_up and channel and user:
            try:
                embed = discord.Embed(
                    title="🎉 Level Up!",
                    description=f"{user.mention} đã lên level **{level}** và nhận **{10000*level}** coin!",
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url=user.avatar.url if user.avatar else discord.Embed.Empty)
                await channel.send(embed=embed)
            except:
                pass

    @commands.command(name="lvl" or "level", description="Kiểm tra level của bạn")
    async def check_level(self, ctx):
        user_data = get_user_data(ctx.author.id)
        if user_data is None:
            await ctx.send("Bạn chưa có tài khoản!")
            return
        # Thêm _ để bỏ qua user_id 
        _, balance, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite = user_data
        embed = discord.Embed(
            title=f"🌟 Thông tin Level của {ctx.author.display_name}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty)
        embed.add_field(name="Level", value=f"**{level}**", inline=True)
        embed.add_field(name="Exp", value=f"**{exp}** / {100*level}", inline=True)
        embed.add_field(name="Coin", value=f"{balance}", inline=True)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LevelSystem(bot))