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
        self.update_bet_message_task = self.bot.loop.create_task(self.auto_update_bet_message())
        self.bet_message_lock = asyncio.Lock()

    async def auto_baucua(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await self.start_baucua()
            await asyncio.sleep(1800)  # 30 phút

    async def auto_update_bet_message(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            if self.current_baucua and self.current_baucua["open"]:
                channel = self.bot.get_channel(1397080445656633375)
                try:
                    last_message = [msg async for msg in channel.history(limit=1)]
                    if last_message and last_message[0].id == self.current_baucua["message"].id:
                        # Đã là mới nhất, không cần làm gì
                        pass
                    else:
                        # Xóa và gửi lại
                        try:
                            if self.current_baucua["message"]:
                                await self.current_baucua["message"].delete()
                        except Exception:
                            pass
                        embed = self.build_baucua_embed(self.current_baucua["bets"])
                        msg = await channel.send(embed=embed)
                        self.current_baucua["message"] = msg
                except Exception:
                    pass
            await asyncio.sleep(60)  # 1 phút

    def build_baucua_embed(self, bets):
        desc = "Hãy chọn con và đặt cược! Bạn có 30 phút để chọn.\n\n"
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
            # Xóa message ván cũ nếu còn
            try:
                if self.current_baucua["message"]:
                    await self.current_baucua["message"].delete()
            except Exception:
                pass
            await self.close_baucua()
        self.current_baucua = {
            "open": True,
            "bets": {},
            "message": None
        }
        embed = self.build_baucua_embed(self.current_baucua["bets"])
        channel = self.bot.get_channel(1397080445656633375)
        msg = await channel.send(embed=embed)
        self.current_baucua["message"] = msg
        await asyncio.sleep(1800)  # 30 phút
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
            balance, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite = user_data
            total_reward = 0
            for con, bet_amount in bets.items():
                count = result.count(con)
                if count > 0:
                    total_reward += bet_amount * count
            if total_reward > 0:
                update_user_data(user_id, balance + total_reward, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite)
                member = channel.guild.get_member(user_id)
                name = member.display_name if member else f"ID:{user_id}"
                summary += f"{name} thắng {total_reward} coin!\n"
        if not summary:
            summary = "Không ai thắng lần này!"

        # Gom 3 cửa 1 dòng
        items = list(BAUCUA_EMOJIS.items())
        line1 = ""
        line2 = ""
        for i in range(3):
            name, emoji = items[i]
            total = sum(bet.get(name, 0) for bet in self.current_baucua["bets"].values())
            line1 += f"{emoji} {name.capitalize()}({total})   "
        for i in range(3, 6):
            name, emoji = items[i]
            total = sum(bet.get(name, 0) for bet in self.current_baucua["bets"].values())
            line2 += f"{emoji} {name.capitalize()}({total})   "

        # Kết quả 3 con xúc xắc
        result_str = "  ".join([BAUCUA_EMOJIS[x] for x in result])  # 2 khoảng trắng giữa các emoji

        # Tổng kết
        desc = f"🎲 Kết quả: {result_str}\n\n{summary}"

        embed = discord.Embed(
                title="🎲 Kết quả Bầu Cua",
            description=desc,
                color=discord.Color.gold()
        )
        await channel.send(embed=embed)
        # Xóa bảng cược cũ
        try:
            if self.current_baucua and self.current_baucua["message"]:
                await self.current_baucua["message"].delete()
        except Exception:
            pass
        self.current_baucua = None

    @commands.command(name="baucua")
    @commands.cooldown(rate=1, per=1800, type=commands.BucketType.user)
    async def baucua(self, ctx, con: str, amount: int):
        if not self.current_baucua or not self.current_baucua["open"]:
            return await ctx.send("Hiện không có phiên Bầu Cua nào đang mở!")
        # Kiểm tra tài khoản, số dư, v.v.
        # Lưu cược vào self.current_baucua["bets"]
    @commands.command(name="bc")
    async def bc(self, ctx, con: str = None, amount: int = None):
        if con is None or amount is None:
            return await ctx.send("Cú pháp: `v.bc <con> <số_tiền>`\nVí dụ: `v.bc bau 100`")
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
        balance, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite = user_data
        if amount > balance:
            return await ctx.send("Bạn không đủ coin để cược!")

        # Trừ tiền ngay khi đặt cược
        update_user_data(user_id, balance - amount, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite)

        # Lưu cược
        if user_id not in self.current_baucua["bets"]:
            self.current_baucua["bets"][user_id] = {k: 0 for k in BAUCUA_EMOJIS}
        self.current_baucua["bets"][user_id][con] += amount
        # Update trạng thái cược
        # Xóa bảng cược cũ nếu còn
        async with self.bet_message_lock:
            # Xóa bảng cược cũ nếu còn
            try:
                if self.current_baucua["message"]:
                    await self.current_baucua["message"].delete()
            except Exception:
                pass

            # Gửi bảng cược mới
            embed = self.build_baucua_embed(self.current_baucua["bets"])
            new_msg = await ctx.send(embed=embed)
            self.current_baucua["message"] = new_msg
        msg = await ctx.send(f"{ctx.author.mention} đã cược {amount} vào {con.capitalize()} {BAUCUA_EMOJIS[con]}!")
        await asyncio.sleep(3)
        await msg.delete()

    @bc.error
    async def bc_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Cú pháp: `v.bc <con> <số_tiền>`\nVí dụ: `v.bc bau 100`")
        else:
            await ctx.send(f"Đã xảy ra lỗi khi đặt cược: {error}")

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
