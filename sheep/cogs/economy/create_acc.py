import discord
from discord.ext import commands
import asyncio  # vì có dùng asyncio.TimeoutError
from database import get_user_data, create_user


class CreateAcc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="start", description = "Tạo tài khoản và thiết lập số dư")
    async def start(self, ctx):
        user_id = ctx.author.id
        user_data = get_user_data(user_id)
        if user_data is not None:
            await ctx.send(f"{ctx.author.name}, bạn đã có tài khoản rồi!")
            return

        try:
            await ctx.send(f"**{ctx.author.name}** vui lòng kiểm tra tin nhắn của cừu")
            dm = await ctx.author.create_dm()  # Tạo DM channel với người dùng
            await dm.send(
                f"""chào `{ctx.author.name} <3` Điều Khoản (**bắt buộc**)
Khi tạo tài khoản **Sheep Coin** 🐑 , bạn cần đồng ý các `điều khoản` như sau:

`Điều khoản 1:` **Sheep Coin** là điểm thưởng nội bộ dùng để tham gia event, minigame và nhận phần quà từ admin. 

`Điều khoản 2:` Những người sở hữu **Sheep Coin** sẽ nhận được phần quà tương ứng, dựa trên bảng xếp hạng

`Điều khoản 3:` **Sheep Coin** không được quy đổi chính thức thành tiền, nhưng một số phần thưởng có thể mang giá trị thực tế.

`Điều khoản 4:` Tất cả phần quà là tự nguyện và có thể thay đổi tùy theo quyết định của admin.

`Điều khoản 5:` Mọi hành vi gian lận, spam, lợi dụng hệ thống sẽ bị thu hồi coin và vô hiệu hóa tài khoản.

📌 **Việc tạo tài khoản đồng nghĩa với việc bạn đã đọc và đồng ý với điều khoản trên.** ❤️
vui lòng gõ `accept` hoặc `decline`
"""
            )

            # Chờ phản hồi từ người dùng
            def check(msg):
                return msg.author == ctx.author and isinstance(msg.channel, discord.DMChannel)

            try:
                msg = await self.bot.wait_for('message', check=check, timeout=60)  # Đợi tin nhắn trong 60 giây

                if msg.content.lower() == 'accept':
                    # Tạo tài khoản mới nếu đồng ý
                    create_user(user_id, 100, None, 0, 40, 0)
                    await dm.send(f"Tạo tài khoản thành công!! Bạn được tặng `100` sheep coin")
                elif msg.content.lower() == 'decline':
                    # Nếu từ chối
                    await dm.send("Bạn đã từ chối điều khoản. Tạo tài khoản bị hủy bỏ.")
                else:
                    # Nếu người dùng nhập sai
                    await dm.send("Phản hồi không hợp lệ. Tạo tài khoản bị hủy bỏ.")
            except asyncio.TimeoutError:
                await dm.send("Bạn phản hồi lâu quá, vui lòng thử lại.")

        except discord.Forbidden:
            await ctx.send("Không thể gửi tin nhắn, vui lòng kiểm tra cài đặt DM của bạn.")

async def setup(bot):
    await bot.add_cog(CreateAcc(bot))
