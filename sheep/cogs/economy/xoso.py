import discord
from discord.ext import commands
import random
import datetime
from database import get_user_data, update_user_data
import json
import os
import asyncio
from datetime import datetime, timedelta, timezone
VN_TZ = timezone(timedelta(hours=7))

TICKET_PRICE = 100

# Random số trúng cho từng giải
def random_unique_numbers(count, length):
    numbers = set()
    while len(numbers) < count:
        n = str(random.randint(10**(length-1), 10**length-1)).zfill(length)
        numbers.add(n)
    return list(numbers)

def get_all_today_tickets(today):
    # Lấy tất cả số vé đã phát trong ngày hôm nay
    import sqlite3
    from database import DB_PATH
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT so_ve FROM users WHERE hsd = ?", (today,))
        return set(str(row[0]).zfill(6) for row in cursor.fetchall() if row[0])

class XoSo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.xoso_task = self.bot.loop.create_task(self.auto_xoso())

    async def auto_xoso(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                now = datetime.now(VN_TZ)
                next_run = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                wait_seconds = (next_run - now).total_seconds()
                await asyncio.sleep(wait_seconds)
                await self.run_xoso_daily()
            except Exception as e:
                print(f"[auto_xoso] Lỗi: {e}")
                await asyncio.sleep(60)  # Đợi 1 phút rồi thử lại nếu có lỗi

    async def run_xoso_daily(self):
        today = datetime.now(VN_TZ).date()
        today_str = str(today)
        ketqua_path = "xoso_ketqua.json"
        if os.path.exists(ketqua_path):
            with open(ketqua_path, "r", encoding="utf-8") as f:
                all_kq = json.load(f)
        else:
            all_kq = {}
        if today_str in all_kq:
            return  # Đã random rồi, không random lại
        # Random số trúng cho từng giải
        giai_config = [
            ("Đặc biệt", 1, 6, 1000, "🎉"),
            ("Nhất", 1, 5, 500, "🥈"),
            ("Nhì", 3, 4, 400, "🥉"),
            ("Ba", 5, 3, 300, "🏅"),
            ("Bốn", 10, 2, 200, "🏅"),
        ]
        giai_so = []
        for name, count, length, prize, emoji in giai_config:
            so_trung = random_unique_numbers(count, length)
            giai_so.append([name, so_trung, length, prize, emoji])
        all_kq[today_str] = giai_so
        with open(ketqua_path, "w", encoding="utf-8") as f:
            json.dump(all_kq, f, ensure_ascii=False)
        # Gửi log kết quả xổ số cho admin
        try:
            log_channel_id = 1398452904700153866
            log_channel = self.bot.get_channel(log_channel_id)
            if log_channel:
                await log_channel.send(f"🎉 Đã quay xổ số ngày {today_str}")
                print(f"[xoso] Đã gửi log xổ số {today_str} vào channel {log_channel_id}")
            else:
                print(f"[xoso] Không tìm thấy log channel {log_channel_id}")
        except Exception as e:
            print(f"[xoso] Lỗi gửi log kết quả xổ số: {e}")
        # Gửi DM cho user trúng thưởng
        import sqlite3
        from database import DB_PATH
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, so_ve FROM users WHERE hsd = ?", (today_str,))
            tickets = cursor.fetchall()
        print(f"[xoso] Tìm thấy {len(tickets)} vé cho ngày {today_str}")
        for user_id, so_ve in tickets:
            so_ve = str(so_ve).zfill(6)
            print(f"[xoso] Xử lý vé {so_ve} của user {user_id}")
            trung = False
            for name, so_trung, length, prize, emoji in giai_so:
                if so_ve[-length:] in so_trung:
                    message = f"{emoji} Bạn đã trúng **Giải {name}** với số vé {so_ve[-length:]}! Nhận {prize} sheepcoin!"
                    user_data = get_user_data(user_id)
                    if user_data:
                        balance, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite = user_data
                        print(f"[xoso] User {user_id} trúng giải {name}, cộng {prize} coin (từ {balance} -> {balance + prize})")
                        update_user_data(user_id, balance + prize, last_daily, streak, win_rate, luck, 0, None, level, exp, invite)
                    member = None
                    try:
                        # Thử tìm member trong tất cả guild mà bot có
                        member = None
                        for guild in self.bot.guilds:
                            member = guild.get_member(int(user_id))
                            if member:
                                break
                        if member:
                            print(f"[xoso] Tìm thấy member {user_id} trong guild {member.guild.name}")
                            await member.send(message)
                            print(f"[xoso] Đã gửi DM thành công cho user {user_id}")
                        else:
                            print(f"[xoso] Không tìm thấy member {user_id} trong bất kỳ guild nào, thử gửi qua bot.get_user")
                            # Thử gửi qua bot.get_user nếu có
                            try:
                                user = self.bot.get_user(int(user_id))
                                if user:
                                    await user.send(message)
                                    print(f"[xoso] Đã gửi DM qua bot.get_user cho user {user_id}")
                                else:
                                    print(f"[xoso] Không tìm thấy user {user_id} qua bot.get_user")
                            except Exception as e2:
                                print(f"[xoso] Không thể gửi DM qua bot.get_user cho user {user_id}: {e2}")
                    except Exception as e:
                        print(f"[xoso] Lỗi gửi DM cho user {user_id}: {e}")
                    trung = True
                    break  # Ưu tiên giải cao nhất
            if not trung:
                print(f"[xoso] User {user_id} không trúng giải nào")
                member = None
                try:
                    # Thử tìm member trong tất cả guild mà bot có
                    member = None
                    for guild in self.bot.guilds:
                        member = guild.get_member(int(user_id))
                        if member:
                            break
                    if member:
                        print(f"[xoso] Tìm thấy member {user_id} trong guild {member.guild.name}")
                        await member.send("😢 Rất tiếc, bạn không trúng giải nào hôm nay. Chúc may mắn lần sau!")
                        print(f"[xoso] Đã gửi DM thông báo không trúng cho user {user_id}")
                    else:
                        print(f"[xoso] Không tìm thấy member {user_id} trong bất kỳ guild nào để gửi thông báo không trúng")
                except Exception as e:
                    print(f"[xoso] Lỗi gửi DM cho user {user_id}: {e}")

    @commands.command(name="xoso")
    async def xoso(self, ctx, so_ve_chon: str = None):
        user_id = ctx.author.id
        # Ngày hiệu lực là ngày mai
        today = datetime.now(VN_TZ).date()
        hieu_luc = str(today + timedelta(days=1))
        user_data = get_user_data(user_id)
        if user_data is None:
            return await ctx.send("Bạn chưa có tài khoản!")
        balance, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite = user_data
        # Nếu đã có vé cho ngày mai thì không cho mua nữa
        if hsd == hieu_luc:
            return await ctx.send(f"Bạn đã mua vé cho ngày {hieu_luc} rồi!, vé của bạn là {so_ve}")
        if balance < TICKET_PRICE:
            return await ctx.send("Bạn không đủ tiền để mua vé!")
        # Lấy tất cả vé đã phát cho ngày mai
        all_tomorrow_tickets = get_all_today_tickets(hieu_luc)
        # Nếu user chọn số
        if so_ve_chon:
            if not (so_ve_chon.isdigit() and len(so_ve_chon) == 6):
                return await ctx.send("Số vé phải gồm đúng 6 chữ số!")
            if so_ve_chon in all_tomorrow_tickets:
                return await ctx.send("Số vé này đã có người chọn cho ngày mai, hãy chọn số khác!")
            so_ve_new = so_ve_chon
        else:
            # Random số vé không trùng
            while True:
                so_ve_new = str(random.randint(100000, 999999)).zfill(6)
                if so_ve_new not in all_tomorrow_tickets:
                    break
        # Lưu vé vào user, hsd là ngày mai
        update_user_data(user_id, balance - TICKET_PRICE, last_daily, streak, win_rate, luck, so_ve_new, hieu_luc, level, exp, invite)
        await ctx.send(f"Bạn đã mua vé số {so_ve_new} cho ngày {hieu_luc} với giá {TICKET_PRICE} coin. Kết quả sẽ được công bố vào ngày đó!")

    @commands.command(name="xoso_quay")
    async def xoso_quay(self, ctx):
        today = str(datetime.now(VN_TZ).date())
        ketqua_path = "xoso_ketqua.json"
        # Nếu đã có kết quả hôm nay thì chỉ hiển thị lại
        if os.path.exists(ketqua_path):
            with open(ketqua_path, "r", encoding="utf-8") as f:
                all_kq = json.load(f)
        else:
            all_kq = {}
        if today in all_kq:
            giai_so = all_kq[today]
            await ctx.send("🔔 Kết quả xổ số hôm nay:")
        else:
            # Nếu chưa có kết quả hôm nay, tự động quay và lưu kết quả
            giai_config = [
                ("Đặc biệt", 1, 6, 1000, "🎉"),
                ("Nhất", 1, 5, 500, "🥈"),
                ("Nhì", 3, 4, 400, "🥉"),
                ("Ba", 5, 3, 300, "🏅"),
                ("Bốn", 10, 2, 200, "🏅"),
            ]
            giai_so = []
            for name, count, length, prize, emoji in giai_config:
                so_trung = random_unique_numbers(count, length)
                giai_so.append([name, so_trung, length, prize, emoji])
            all_kq[today] = giai_so
            with open(ketqua_path, "w", encoding="utf-8") as f:
                json.dump(all_kq, f, ensure_ascii=False)
            # Gửi log kết quả xổ số cho admin sau khi quay
            try:
                log_channel_id = 1398452904700153866
                log_channel = self.bot.get_channel(log_channel_id)
                if log_channel:
                    await log_channel.send(f"🎉 Đã quay xổ số ngày {today}")
                    print(f"[xoso] Đã gửi log xổ số {today} vào channel {log_channel_id}")
                else:
                    print(f"[xoso] Không tìm thấy log channel {log_channel_id}")
            except Exception as e:
                print(f"[xoso] Lỗi gửi log kết quả xổ số: {e}")
            await ctx.send("🔔 Đã quay số và công bố kết quả xổ số hôm nay!")
        # Hiển thị kết quả
        embed = discord.Embed(
            title=f"🎉 Kết quả xổ số {today}",
            color=discord.Color.gold()
        )
        for name, so_trung, length, prize, emoji in giai_so:
            embed.add_field(name=f"{name} ({length} số, {len(so_trung)} giải)", value=", ".join(so_trung), inline=False)
        await ctx.send(embed=embed)
        # Thông báo thời gian còn lại đến 0h ngày mới
        now = datetime.now(VN_TZ)
        next_open = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        delta = next_open - now
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{hours} giờ {minutes} phút {seconds} giây"
        await ctx.send(f"⏰ Thời gian đến ngày mới: {time_str}")

async def setup(bot):
    cog = XoSo(bot)
    await bot.add_cog(cog)
    cog.xoso_task = bot.loop.create_task(cog.auto_xoso())
