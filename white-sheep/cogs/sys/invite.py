import discord
from discord.ext import commands
from database import get_user_data, update_user_data, create_user, connect_db
import asyncio
from datetime import datetime, timezone, timedelta

class Invite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invites = {}

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            self.invites[guild.id] = await guild.invites()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await asyncio.sleep(1)
        guild = member.guild
        before = self.invites.get(guild.id, [])
        after = await guild.invites()
        inviter = None

        for invite in after:
            old = next((i for i in before if i.code == invite.code), None)
            if old and invite.uses > old.uses:
                inviter = invite.inviter
                break
            elif not old and invite.uses > 0:
                inviter = invite.inviter
                break

        self.invites[guild.id] = after

        # Kiểm tra tài khoản được mời đã tạo trên 3 tháng
        now = datetime.now(timezone.utc)
        if inviter and (now - member.created_at) >= timedelta(days=90):
            user_data = get_user_data(inviter.id)
            if not user_data:
                create_user(inviter.id)
                user_data = get_user_data(inviter.id)
            # Unpack đủ biến, bỏ qua user_id
            _, balance, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite = user_data
            if invite is None:
                invite = 0
            invite += 1
            exp += 10
            while exp >= 100 * level:
                exp -= 100 * level
                level += 1
                balance += 10000 * level
            update_user_data(inviter.id, balance, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite_count)

    @commands.command(name='myinvite')
    async def my_invite(self, ctx):
        """Xem số lượng invite của bạn"""
        user_data = get_user_data(ctx.author.id)
        if not user_data:
            await ctx.send("Bạn chưa có dữ liệu invite.")
            return
        invite_count = user_data[10] if len(user_data) > 10 else 0
        await ctx.send(f"Bạn đã mời thành công `{invite_count}` người.")

    @commands.command(name='topinvite')
    async def top_invite(self, ctx):
        """Xem top 10 người mời nhiều nhất"""
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, invite FROM users ORDER BY invite DESC LIMIT 10")
            rows = cursor.fetchall()
        if not rows or all(r[1] is None or r[1] == 0 for r in rows):
            await ctx.send("Chưa có ai mời thành công.")
            return
        msg = "**Top 10 người mời nhiều nhất:**\n"
        for idx, (user_id, count) in enumerate(rows, 1):
            user = ctx.guild.get_member(user_id)
            name = user.mention if user else f"ID: {user_id}"
            msg += f"{idx}. {name}: {count or 0} người\n"
        await ctx.send(msg)

async def setup(bot):
    await bot.add_cog(Invite(bot))