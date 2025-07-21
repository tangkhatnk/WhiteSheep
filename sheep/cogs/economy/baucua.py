import discord
from discord.ext import commands
import asyncio
import random
from database import get_user_data, update_user_data

BAUCUA_EMOJIS = {
    "bau": "🍆",
    "cua": "🦀",
    "tom": "🦞",
    "ca": "🐟",
    "ga": "🐔",
    "nai": "🐂"
}
BAUCUA_LIST = list(BAUCUA_EMOJIS.keys())

class BauCua(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_baucua = None
        self.baucua_task = self.bot.loop.create_task(self.auto_baucua())

    async def auto_baucua(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await self.start_baucua()
            await asyncio.sleep(300)  # 5 phút

    def build_baucua_embed(self, bets):
        desc = "Hãy chọn con và đặt cược! Bạn có 5 phút để chọn.\n\n"
        for name, emoji in BAUCUA_EMOJIS.items():
            total = 0
            for bet in bets.values():
                total += bet.get(name, 0)
            desc += f"**{name.capitalize()}** ({emoji})\n{total} sheepcoin\n"
        embed = discord.Embed(
            title="Bầu Cua Tôm Cá - Trạng thái cược",
            description=desc,
            color=discord.Color.green()
        )
        return embed

    async def start_baucua(self):
        if self.current_baucua and self.current_baucua["open"]:
            await self.close_baucua()
        self.current_baucua = {
            "open": True,
            "bets": {},
            "message": None
        }
        embed = self.build_baucua_embed(self.current_baucua["bets"])
        channel = self.bot.get_channel(1396859132228927641)
        msg = await channel.send(embed=embed)
        self.current_baucua["message"] = msg
        await asyncio.sleep(300)
        await self.close_baucua()

    async def close_baucua(self):
        if not self.current_baucua or not self.current_baucua["open"]:
            return
        self.current_baucua["open"] = False
        result = [random.choice(list(BAUCUA_EMOJIS.keys())) for _ in range(3)]
        result_str = " ".join([BAUCUA_EMOJIS[x] for x in result])
        channel = self.current_baucua["message"].channel

        # Tính thưởng cho từng user
        summary = ""
        for user_id, bets in self.current_baucua["bets"].items():
            user_data = get_user_data(user_id)
            if user_data is None:
                continue
            balance, last_daily, streak, win_rate, luck = user_data
            total_reward = 0
            for con, bet_amount in bets.items():
                count = result.count(con)
                if count > 0:
                    total_reward += bet_amount * count
            if total_reward > 0:
                update_user_data(user_id, balance + total_reward, last_daily, streak, win_rate, luck)
                member = channel.guild.get_member(user_id)
                name = member.display_name if member else f"ID:{user_id}"
                summary += f"{name} thắng {total_reward} coin!\n"
        if not summary:
            summary = "Không ai thắng lần này!"

        await channel.send(
            embed=discord.Embed(
                title="🎲 Kết quả Bầu Cua",
                description=f"Kết quả: {result_str}\n\n{summary}",
                color=discord.Color.gold()
            )
        )
        self.current_baucua = None

    @commands.command(name="baucua")
    async def baucua(self, ctx, con: str, amount: int):
        if not self.current_baucua or not self.current_baucua["open"]:
            return await ctx.send("Hiện không có phiên Bầu Cua nào đang mở!")
        # Kiểm tra tài khoản, số dư, v.v.
        # Lưu cược vào self.current_baucua["bets"]
    @commands.command(name="bc_choose")
    async def bc_choose(self, ctx, con: str = None, amount: int = None):
        if con is None or amount is None:
            return await ctx.send("Cú pháp: `w.bc_choose <con> <số_tiền>`\nVí dụ: `w.bc_choose bau 100`")
        if not self.current_baucua or not self.current_baucua["open"]:
            return await ctx.send("Hiện không có phiên Bầu Cua nào đang mở!")

        con = con.lower()
        if con not in BAUCUA_EMOJIS:
            return await ctx.send("Bạn phải chọn 1 trong các cửa: bau, cua, tom, ca, ga, nai.")

        if amount <= 0 or amount > 250:
            return await ctx.send("Số tiền cược phải từ 1 đến 250!")

        user_id = ctx.author.id
        user_data = get_user_data(user_id)
        if user_data is None:
            return await ctx.send("Bạn chưa có tài khoản!")

        balance, last_daily, streak, win_rate, luck = user_data
        if amount > balance:
            return await ctx.send("Bạn không đủ coin để cược!")

        # Trừ tiền ngay khi đặt cược
        update_user_data(user_id, balance - amount, last_daily, streak, win_rate, luck)

        # Lưu cược
        if user_id not in self.current_baucua["bets"]:
            self.current_baucua["bets"][user_id] = {k: 0 for k in BAUCUA_EMOJIS}
        self.current_baucua["bets"][user_id][con] += amount
        # Update trạng thái cược
        embed = self.build_baucua_embed(self.current_baucua["bets"])
        await self.current_baucua["message"].edit(embed=embed)
        await ctx.send(f"{ctx.author.mention} đã cược {amount} vào {con.capitalize()} {BAUCUA_EMOJIS[con]}!")

    @bc_choose.error
    async def bc_choose_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Cú pháp: `w.bc_choose <con> <số_tiền>`\nVí dụ: `w.bc_choose bau 100`")
        else:
            await ctx.send("Đã xảy ra lỗi khi đặt cược. Vui lòng thử lại!")

    @commands.command(name="baucua_start")
    @commands.has_permissions(administrator=True)
    async def baucua_start(self, ctx):
        await self.start_baucua()
        await ctx.send("Đã mở phiên Bầu Cua mới!")

    @commands.command(name="baucua_stop")
    @commands.has_permissions(administrator=True)
    async def baucua_stop(self, ctx):
        await self.close_baucua()
        await ctx.send("Đã đóng phiên Bầu Cua!")

async def setup(bot):
    await bot.add_cog(BauCua(bot))
