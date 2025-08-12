import discord
from discord.ext import commands
from discord.ui import View, Button
import asyncio
import random
from database import get_user_data, update_user_data

# Danh sách các emoji bài
CARD_EMOJIS = [
    "<a:2_b:1403762489102958733>",
    "<a:3_b:1403762581038170315>",
    "<a:4_c:1403762746729955461>",
    "<a:5_c:1403762935842603059>",
    "<a:6_r:1403763013370118255>",
    "<a:7_c:1403763141745316012>",
    "<a:8_c:1403763198871470181>",
    "<a:9_c:1403763262687805646>",
    "<a:10_b:1403763347572265123>",
    "<a:j_b:1403763538069291059>",
    "<a:Q_r:1403763645489479720>",
    "<a:k_c:1403763728159342615>",
    "<a:a_c:1403763811722465292>",
]

CARD_VALUES = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 1]  # Giá trị tương ứng

# Bản đồ nhanh từ emoji -> giá trị cơ bản (A=1, J/Q/K=10)
EMOJI_TO_VALUE = {emoji: value for emoji, value in zip(CARD_EMOJIS, CARD_VALUES)}

def calculate_hand_value_from_emojis(card_emojis: list[str]) -> int:
    # Quy tắc Át linh hoạt: có thể là 1, 10 hoặc 11. Chọn tổng tốt nhất ≤ 21 nếu có.
    values = [EMOJI_TO_VALUE.get(e, 0) for e in card_emojis]
    non_aces_sum = sum(v for v in values if v != 1)
    ace_count = sum(1 for v in values if v == 1)

    if ace_count == 0:
        return non_aces_sum

    best_valid = None
    min_total = None
    # Thử mọi phân bố số Át lấy 11, 10, 1
    for elevens in range(ace_count, -1, -1):
        for tens in range(ace_count - elevens, -1, -1):
            ones = ace_count - elevens - tens
            total = non_aces_sum + elevens * 11 + tens * 10 + ones * 1
            if total <= 21:
                if best_valid is None or total > best_valid:
                    best_valid = total
            if min_total is None or total < min_total:
                min_total = total
    return best_valid if best_valid is not None else min_total

def detect_special_badge(card_emojis: list[str], current_score: int | None = None) -> str:
    # XÌ BÀN: 2 Át
    if len(card_emojis) == 2 and all(c == CARD_EMOJIS[12] for c in card_emojis):
        return "(XÌ BÀN)"
    # XÌ DÁCH: 2 lá, 1 Át + 1 lá 10/J/Q/K
    if len(card_emojis) == 2:
        has_ace = any(c == CARD_EMOJIS[12] for c in card_emojis)
        has_ten_value = any(EMOJI_TO_VALUE.get(c, 0) == 10 for c in card_emojis)
        if has_ace and has_ten_value:
            return "(XÌ DÁCH)"
    # NGŨ LINH: >=5 lá và <= 21 điểm
    score = current_score if current_score is not None else calculate_hand_value_from_emojis(card_emojis)
    if len(card_emojis) >= 5 and score <= 21:
        return "(NGŨ LINH)"
    return ""

def get_hand_rank_tuple(card_emojis: list[str], score: int) -> tuple[int, int]:
    """Trả về (rank, points) để so sánh:
    - rank: -1=BUST, 1=NORMAL, 2=NGŨ LINH, 3=XÌ DÁCH, 4=XÌ BÀN
    - points: dùng để phân định khi cùng hạng (không áp dụng cho XÌ BÀN/XÌ DÁCH → coi ngang nhau)
    """
    if score > 21:
        return (-1, 0)
    badge = detect_special_badge(card_emojis, score)
    if badge == "(XÌ BÀN)":
        return (4, 21)
    if badge == "(XÌ DÁCH)":
        return (3, 21)
    if badge == "(NGŨ LINH)":
        return (2, score)
    return (1, score)

class TaobanView(View):
    def __init__(self, bot, host_id, channel, bet_amount: int = 0):
        super().__init__(timeout=None)
        self.bot = bot
        self.host_id = host_id
        self.channel = channel
        self.bet_amount = max(0, int(bet_amount))
        self.players = [host_id]
        self.started = False
        self.scores = {host_id: 0}
        self.player_cards = {host_id: []}
        self.dealer_cards = []
        self.dealer_score = 0
        self.current_player_index = 0
        self.original_message = None
        self.finished_players: set[int] = set()
        self.draw_counts: dict[int, int] = {host_id: 0}
        self.latest_controls_message: discord.Message | None = None
        self.refresh_task: asyncio.Task | None = None
        self.game_deadline_ts: float | None = None
        self.active_view: View | None = None
        self.results_sent: bool = False

    def build_lobby_embed(self) -> discord.Embed:
        current_player_count = len(self.players)
        embed = discord.Embed(
            title="Chào mừng đến với bàn Xì Dách!",
            description="🟥♦️ Cờ bạc là bác thằng bần ♠️🖤\n\n",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Host", value=f"<@{self.host_id}>", inline=False)
        embed.add_field(name="Thời gian", value="in 5 seconds", inline=False)
        embed.add_field(name="Cược", value=f"{self.bet_amount} xu", inline=False)
        embed.add_field(name="Tối đa người chơi", value=f"{current_player_count}/10", inline=False)
        embed.add_field(
            name="Luật chơi theo Wikipedia",
            value="[Wikipedia](https://vi.wikipedia.org/wiki/X%C3%AC_d%C3%A1ch)",
            inline=False,
        )
        embed.add_field(
            name="Dành cho người mới không biết tính điểm",
            value="[Xem tại đây](https://blackjack-calc.vercel.app/)",
            inline=False,
        )
        embed.set_footer(text="Nhấn 'Tham gia' để vào bàn • Chủ bàn bấm 'Bắt đầu' khi sẵn sàng")
        return embed

    @discord.ui.button(label="Tham gia", style=discord.ButtonStyle.green)
    async def join_button(self, interaction: discord.Interaction, button: Button):
        user = interaction.user
        if self.started:
            await interaction.response.send_message("Ván chơi đã bắt đầu, bạn không thể tham gia nữa!", ephemeral=True)
            return
        if len(self.players) >= 10:
            await interaction.response.send_message("Bàn đã đủ người (10/10)!", ephemeral=True)
            return

        if user.id not in self.players:
            # Kiểm tra tài khoản và số dư trước khi cho tham gia
            user_row = get_user_data(user.id)
            if user_row is None:
                await interaction.response.send_message("Bạn chưa có tài khoản SheepCoin. Dùng `v.start` để tạo!", ephemeral=True)
                return
            _, balance, *rest = user_row
            if balance is None or balance < self.bet_amount:
                await interaction.response.send_message(f"Bạn cần tối thiểu `{self.bet_amount}` xu để tham gia!", ephemeral=True)
                return
            self.players.append(user.id)
            self.scores[user.id] = 0
            self.player_cards[user.id] = []
            self.draw_counts[user.id] = 0
            # Gửi thông báo công khai và cập nhật embed của bàn chơi
            await interaction.response.send_message(
                f"{user.mention} đã tham gia trò chơi! ({len(self.players)}/10)", ephemeral=True
            )
            if self.original_message is None:
                self.original_message = interaction.message
            try:
                await self.original_message.edit(embed=self.build_lobby_embed(), view=self)
            except Exception:
                # Bỏ qua lỗi chỉnh sửa embed nếu có
                pass
        else:
            await interaction.response.send_message("Bạn đã tham gia rồi!", ephemeral=True)

    @discord.ui.button(label="Bắt đầu", style=discord.ButtonStyle.red)
    async def start_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.host_id:
            await interaction.response.send_message("Chỉ chủ bàn mới được bắt đầu!", ephemeral=True)
            return
        if self.started:
            await interaction.response.send_message("Bàn đã bắt đầu rồi!", ephemeral=True)
            return
        if len(self.players) <= 1:
            await interaction.response.send_message("Cần ít nhất 2 người chơi để bắt đầu (1 host, 1 người chơi)!", ephemeral=True)
            return
        self.started = True
        await interaction.response.send_message("Trận đấu bắt đầu!", ephemeral=False)
        self.original_message = interaction.message
            
        for item in self.children:
            item.disabled = True
        await self.original_message.edit(view=self)

        await self.start_game_flow()

    async def start_game_flow(self):
        self.dealer_cards, self.dealer_score = self.deal_initial_cards()
        # Không hiển thị bài của Dealer khi bắt đầu; Dealer cũng rút trong 50 giây như mọi người
        await self.channel.send(
            f"Bàn chơi bắt đầu! Mọi người có 50 giây để 'Rút bài' và 'Xem bài'."
        )

        for player_id in self.players:
            if player_id != self.host_id:
                self.player_cards[player_id], self.scores[player_id] = self.deal_initial_cards()

        # Gửi view cho toàn bộ người chơi, mọi người có 50 giây để thao tác
        game_view = GameView(self.players, self, timeout=50)
        msg = await self.channel.send(
            "Mỗi người chơi đã được chia 2 lá. Bạn có 50 giây để 'Xem bài' và 'Rút bài'. Hết thời gian sẽ chốt kết quả.",
            view=game_view,
        )
        game_view.message = msg
        self.latest_controls_message = msg
        loop = asyncio.get_running_loop()
        self.game_deadline_ts = loop.time() + 50
        self.active_view = game_view
        # Bắt đầu auto-reload để message luôn ở cuối kênh
        self.refresh_task = asyncio.create_task(self._auto_refresh_controls())

    async def _auto_refresh_controls(self):
        try:
            loop = asyncio.get_running_loop()
            while self.game_deadline_ts:
                remaining = self.game_deadline_ts - loop.time()
                if remaining <= 0:
                    break
                # Làm mới trước khi hết giờ vài giây, hoặc mỗi ~12s
                sleep_for = 12 if remaining > 15 else max(1, int(remaining - 2))
                await asyncio.sleep(sleep_for)
                remaining = self.game_deadline_ts - loop.time()
                if remaining <= 0:
                    break
                # Tạo view mới với timeout còn lại để tránh kéo dài thời gian chơi
                new_view = GameView(self.players, self, timeout=int(max(1, remaining)))
                sent = await self.channel.send(
                    "Mỗi người chơi đã được chia 2 lá. Bạn có 50 giây để 'Xem bài' và 'Rút bài'. Hết thời gian sẽ chốt kết quả.",
                    view=new_view,
                )
                new_view.message = sent
                # Xóa message cũ để tránh spam, chỉ giữ lại message mới nhất
                old_msg = self.latest_controls_message
                self.latest_controls_message = sent
                self.active_view = new_view
                if old_msg:
                    try:
                        await old_msg.delete()
                    except Exception:
                        pass
        except asyncio.CancelledError:
            return

    def deal_initial_cards(self):
        cards = []
        for _ in range(2):
            card_index = random.randint(0, len(CARD_EMOJIS) - 1)
            card_emoji = CARD_EMOJIS[card_index]
            cards.append(card_emoji)
        # Tính điểm lại theo quy tắc Át linh hoạt sau khi có đủ lá
        score = calculate_hand_value_from_emojis(cards)
        return cards, score

    async def send_turn_message(self):
        # Không còn dùng theo lượt; giữ hàm để tương thích nếu nơi khác gọi.
        pass

    async def next_turn(self):
        # Không dùng nữa trong cơ chế 50 giây toàn bàn.
        pass

    async def announce_results(self):
        # So sánh theo thứ hạng đặc biệt: XÌ BÀN > XÌ DÁCH > NGŨ LINH > điểm thường; BUST thua
        non_host_players = [p for p in self.players if p != self.host_id]
        dealer_bust = self.dealer_score > 21

        dealer_rank = get_hand_rank_tuple(self.dealer_cards, self.dealer_score)
        winners = []
        best_tuple = None
        for pid in non_host_players:
            score = self.scores.get(pid, 0)
            cards = self.player_cards.get(pid, [])
            player_tuple = get_hand_rank_tuple(cards, score)
            # Người thắng là người có tuple > dealer_tuple theo thứ tự từ trái sang phải
            if player_tuple > dealer_rank:
                if best_tuple is None or player_tuple > best_tuple:
                    best_tuple = player_tuple
                    winners = [pid]
                elif player_tuple == best_tuple:
                    winners.append(pid)

        # Xây dựng mô tả kết quả từng người chơi
        lines = []
        # Dealer dòng đầu
        dealer_cards_display = " ".join(self.dealer_cards) if self.dealer_cards else ""
        dealer_badge = detect_special_badge(self.dealer_cards, self.dealer_score)
        dealer_status_text = "(QUÁC)" if dealer_bust else dealer_badge
        lines.append(f"**Dealer** (<@{self.host_id}>) {dealer_status_text}\n{dealer_cards_display}    =>  ({self.dealer_score} điểm)\n")

        def spaced_label(text: str) -> str:
            return " ".join(list(text))

        # Tạo dữ liệu và sắp xếp: WIN -> DRAW -> LOSE; trong mỗi nhóm, hạng cao hơn trước
        players_view = []
        dealer_tuple = get_hand_rank_tuple(self.dealer_cards, self.dealer_score)
        for pid in non_host_players:
            score = self.scores.get(pid, 0)
            cards = self.player_cards.get(pid, [])
            player_tuple = get_hand_rank_tuple(cards, score)
            if score > 21:
                result = "LOSE"
                status_suffix = "(QUẮC)"
            else:
                if player_tuple > dealer_tuple:
                    result = "WIN"
                    status_suffix = ""
                elif player_tuple == dealer_tuple:
                    result = "DRAW"
                    status_suffix = ""
                else:
                    result = "LOSE"
                    status_suffix = ""
            players_view.append({
                "pid": pid,
                "score": score,
                "cards": cards,
                "player_tuple": player_tuple,
                "result": result,
                "status_suffix": status_suffix,
            })

        def order_key(p):
            result_order = {"WIN": 0, "DRAW": 1, "LOSE": 2}
            rank, points = p["player_tuple"]
            return (result_order[p["result"]], -rank, -points)

        players_view.sort(key=order_key)

        for idx, p in enumerate(players_view, start=1):
            pid = p["pid"]
            score = p["score"]
            cards = p["cards"]
            card_display = " ".join(cards)
            badge = detect_special_badge(cards, score)
            status = spaced_label(p["result"])
            status_suffix = p["status_suffix"]
            trophy = " 🏆" if pid in winners and len(winners) == 1 else ""
            user_mention = f"<@{pid}>"
            lines.append(
                f"{idx}. {user_mention} {badge} {status_suffix}{trophy}\n({status})\n{card_display}    =>  ({score} điểm)\n"
            )

        # Cập nhật số dư theo kết quả với hệ số: XÌ BÀN x4, XÌ DÁCH x3, NGŨ LINH x2, thường x1
        def multiplier(badge: str) -> int:
            if badge == "(XÌ BÀN)":
                return 4
            if badge == "(XÌ DÁCH)":
                return 3
            if badge == "(NGŨ LINH)":
                return 2
            return 1

        dealer_delta = 0
        deltas: dict[int, int] = {}
        dealer_badge_for_pay = detect_special_badge(self.dealer_cards, self.dealer_score)
        dealer_tuple = get_hand_rank_tuple(self.dealer_cards, self.dealer_score)

        for pid in non_host_players:
            score = self.scores.get(pid, 0)
            cards = self.player_cards.get(pid, [])
            player_badge_for_pay = detect_special_badge(cards, score)
            player_tuple = get_hand_rank_tuple(cards, score)

            bet = self.bet_amount
            if bet <= 0:
                deltas[pid] = 0
                continue

            # Nếu cả hai cùng bust coi như hòa
            if score > 21 and self.dealer_score > 21:
                deltas[pid] = 0
                continue

            if score > 21:
                lose = bet * multiplier(dealer_badge_for_pay)
                deltas[pid] = -lose
                dealer_delta += lose
            elif self.dealer_score > 21 or player_tuple > dealer_tuple:
                win = bet * multiplier(player_badge_for_pay)
                deltas[pid] = +win
                dealer_delta -= win
            elif player_tuple == dealer_tuple:
                deltas[pid] = 0
            else:
                lose = bet * multiplier(dealer_badge_for_pay)
                deltas[pid] = -lose
                dealer_delta += lose

        # Áp dụng vào DB
        def apply_delta(uid: int, delta: int):
            row = get_user_data(uid)
            if row is None:
                return
            user_id, balance, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite = row
            new_balance = (balance or 0) + delta
            update_user_data(user_id, new_balance, last_daily, streak, win_rate, luck, so_ve, hsd, level, exp, invite)

        for pid, delta in deltas.items():
            apply_delta(pid, delta)
        apply_delta(self.host_id, dealer_delta)

        # Tiêu đề và lời chúc mừng
        title = "♠️ ♦️ KẾT QUẢ CUỐI CÙNG ♣️ ❤️"
        embed = discord.Embed(title=title, color=discord.Color.green())

        if winners:
            winners_text = ", ".join(f"<@{pid}>" for pid in winners)
            congrats = f"Chúc mừng {winners_text} đã chiến thắng!"
            embed.add_field(name="", value=f"**{congrats}**", inline=False)

        embed.description = "\n".join(lines)
        embed.set_footer(text="Game đã kết thúc. Nếu có lỗi hãy báo cho quản trị viên.")

        # Không chỉnh sửa message gốc của bàn; gửi message mới để không bị ghi đè khi tạo bàn mới
        await self.channel.send(embed=embed)


class GameView(View):
    def __init__(self, players, taoban_view: TaobanView, timeout: int | None = None):
        super().__init__(timeout=timeout)
        self.players = players
        self.taoban_view = taoban_view
        self.game_ended = False
        self.message: discord.Message | None = None

    @discord.ui.button(label="Xem bài", style=discord.ButtonStyle.primary)
    async def xembai(self, interaction: discord.Interaction, button: Button):
        if self.game_ended:
            await interaction.response.send_message("Ván chơi đã kết thúc!", ephemeral=True)
            return
            
        user_id = interaction.user.id
        # Chặn người ngoài bàn
        if user_id not in self.players:
            await interaction.response.send_message("Bạn không ở trong bàn này!", ephemeral=True)
            return

        # Dealer xem bài của Dealer, người chơi xem bài của mình
        if user_id == self.taoban_view.host_id:
            cards = self.taoban_view.dealer_cards
        else:
            cards = self.taoban_view.player_cards.get(user_id, [])
        score = self.taoban_view.scores.get(user_id, 0)
            
        cards_display = " ".join(cards)
        # Chỉ hiển thị emoji bài, không kèm điểm hay văn bản
        await interaction.response.send_message(cards_display, ephemeral=True)

    @discord.ui.button(label="Rút bài", style=discord.ButtonStyle.secondary)
    async def rutbai(self, interaction: discord.Interaction, button: Button):
        if self.game_ended:
            await interaction.response.send_message("Ván chơi đã kết thúc!", ephemeral=True)
            return
            
        user_id = interaction.user.id
        # Chặn người ngoài bàn
        if user_id not in self.players:
            await interaction.response.send_message("Bạn không ở trong bàn này!", ephemeral=True)
            return

        card_index = random.randint(0, len(CARD_EMOJIS) - 1)
        card_emoji = CARD_EMOJIS[card_index]
        card_value = CARD_VALUES[card_index]

        if user_id == self.taoban_view.host_id:
            # Dealer rút
            self.taoban_view.dealer_cards.append(card_emoji)
            self.taoban_view.dealer_score = calculate_hand_value_from_emojis(
                self.taoban_view.dealer_cards
            )
            self.taoban_view.draw_counts[user_id] = self.taoban_view.draw_counts.get(user_id, 0) + 1
        else:
            # Người chơi rút
            self.taoban_view.player_cards[user_id].append(card_emoji)
            self.taoban_view.scores[user_id] = calculate_hand_value_from_emojis(
                self.taoban_view.player_cards[user_id]
            )
            self.taoban_view.draw_counts[user_id] = self.taoban_view.draw_counts.get(user_id, 0) + 1
        
        # Chỉ hiển thị emoji bài của người rút (ephemeral), không hiển thị điểm
        if user_id == self.taoban_view.host_id:
            cards_display = " ".join(self.taoban_view.dealer_cards)
        else:
            cards_display = " ".join(self.taoban_view.player_cards[user_id])

        await interaction.response.send_message(cards_display, ephemeral=True)

    async def on_timeout(self):
        if self.game_ended:
            return
        # Tránh chạy nhiều lần khi có nhiều view do auto-reload
        if self.taoban_view.results_sent:
            return
        self.taoban_view.results_sent = True
        # Khóa nút khi hết thời gian và chốt kết quả
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass
        # Gửi tổng kết số lần rút của tất cả người chơi (bao gồm host/dealer)
        await self.taoban_view.channel.send("⏱️ Hết thời gian 50 giây.")
        # Không có lượt Dealer riêng; Dealer đã rút trong 50 giây.
        # Dừng auto-refresh (nếu đang chạy)
        if self.taoban_view.refresh_task and not self.taoban_view.refresh_task.done():
            self.taoban_view.refresh_task.cancel()
        self.taoban_view.game_deadline_ts = None
        # Xóa message controls cuối cùng để tránh rác kênh
        if self.taoban_view.latest_controls_message:
            try:
                await self.taoban_view.latest_controls_message.delete()
            except Exception:
                pass
        try:
            await self.taoban_view.announce_results()
        except Exception as exc:
            # Fallback hiện lỗi để dễ debug khi có sự cố tính điểm
            await self.taoban_view.channel.send(f"❗ Lỗi khi tính kết quả: {type(exc).__name__}: {exc}")


class BlackjackCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def taoban(self, ctx, bet: int = 0):
        """Tạo bàn chơi Xì Dách. Dùng: v.taoban <số_tiền>"""
        # Cảnh báo quyền nếu thiếu quyền dùng emoji ngoài server
        me = ctx.guild.me if getattr(ctx, "guild", None) else None
        if me:
            perms = ctx.channel.permissions_for(me)
            if not getattr(perms, "use_external_emojis", False):
                await ctx.send("⚠️ Bot đang thiếu quyền 'Use External Emojis' tại kênh này. Emoji tùy chỉnh có thể không hiển thị.")
        # Kiểm tra số dư của host với tiền cược
        row = get_user_data(ctx.author.id)
        if row is None:
            await ctx.send("Bạn chưa có tài khoản SheepCoin. Dùng `v.start` để tạo!")
            return
        _, balance, *_ = row
        bet_amount = max(0, int(bet))
        if balance is None or balance < bet_amount:
            await ctx.send(f"Bạn cần tối thiểu `{bet_amount}` xu để tạo bàn!")
            return

        view = TaobanView(bot=self.bot, host_id=ctx.author.id, channel=ctx.channel, bet_amount=bet_amount)
        embed = view.build_lobby_embed()
        sent = await ctx.send(embed=embed, view=view)
        # Lưu message gốc để còn cập nhật số người chơi
        view.original_message = sent
        
    @taoban.error
    async def taoban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Bạn cần quyền Administrator để sử dụng lệnh này!")

async def setup(bot):
    await bot.add_cog(BlackjackCog(bot))