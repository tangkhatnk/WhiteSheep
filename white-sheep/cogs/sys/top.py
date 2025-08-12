import discord
from discord.ext import commands
import math
import sqlite3
import asyncio

DB_PATH = 'white-sheep.db'

def get_top_users(offset=0, limit=10):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        return cursor.fetchall()

def get_total_users():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        return cursor.fetchone()[0]

def make_embed(ctx, top_users, page, total_pages, per_page, offset):
    embed = discord.Embed(
        title=f"🏆 Top {per_page} Sheep Coin (Trang {page}/{total_pages})",
        color=discord.Color.gold()
    )
    for idx, (user_id, balance) in enumerate(top_users, start=offset + 1):
        member = ctx.guild.get_member(user_id)
        name = member.display_name if member else f"User ID {user_id}"
        embed.add_field(
            name=f"{idx}. {name}",
            value=f"<a:rsheep:1404711843997552780> {balance} xu",
            inline=False
        )
    embed.set_footer(text="Sheep Bot • Top sheepcoin", icon_url="")
    return embed

class Top(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="top", description="Xem top Sheep Coin")
    async def top(self, ctx, mode: str = "cash"):
        if mode != "cash":
            await ctx.send("Hiện chỉ hỗ trợ: `v.top cash`")
            return

        per_page = 10
        total_users = get_total_users()
        total_pages = max(math.ceil(total_users / per_page), 1)
        page = 1
        offset = (page - 1) * per_page
        top_users = get_top_users(offset, per_page)

        if not top_users:
            await ctx.send("Không có dữ liệu!")
            return

        embed = make_embed(ctx, top_users, page, total_pages, per_page, offset)
        message = await ctx.send(embed=embed)

        LEFT = "<:lefth:1404710803797442560>"
        RIGHT = "<:righth:1404710862371033130>"

        if total_pages > 1:
            await message.add_reaction(LEFT)
            await message.add_reaction(RIGHT)

            def check(reaction, user):
                return (
                    user == ctx.author
                    and str(reaction.emoji) in [LEFT, RIGHT]
                    and reaction.message.id == message.id
                )

            while True:
                try:
                    reaction, user = await ctx.bot.wait_for("reaction_add", check=check)
                except Exception:
                    break

                if str(reaction.emoji) == LEFT and page > 1:
                    page -= 1
                elif str(reaction.emoji) == RIGHT and page < total_pages:
                    page += 1
                else:
                    await message.remove_reaction(reaction, user)
                    continue

                offset = (page - 1) * per_page
                top_users = get_top_users(offset, per_page)
                embed = make_embed(ctx, top_users, page, total_pages, per_page, offset)
                await message.edit(embed=embed)
                await message.remove_reaction(reaction, user)

async def setup(bot):
    await bot.add_cog(Top(bot))