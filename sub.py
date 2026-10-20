import discord, random, datetime, json, os, sys, time
from discord import app_commands
from discord.ext import commands, tasks

# 봇 기본 설정
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
start_time = datetime.datetime.utcnow()
regions1 = ["광주", "충남", "전남", "대전", "서울", "충북"]

# ==========================================
# 📅 대회 D-Day
# ==========================================
KST = datetime.timezone(datetime.timedelta(hours=9))
LOCAL_CONTEST = ("2027 충청남도기능경기대회", datetime.date(2027, 4, 6))
NATIONAL_CONTEST = ("제62회 충북전국기능경기대회", datetime.date(2027, 9, 1))
DDAY_CHANNEL_ID = 0   # UR_CHANNEL_ID : 매일 D-Day 알림 채널
DDAY_POST_TIME = datetime.time(9, 0, tzinfo=KST)
DDAY_WINDOW_DAYS = 100                 # 지방대회 D-100 부터 D-DAY 까지 매일 알림

# /status 페이지(status_page/status.py)가 읽는 하트비트 파일
STATUS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_status.json")
last_dday_post = None


def today_kst():
    return datetime.datetime.now(KST).date()


def dday_label(target):
    diff = (target - today_kst()).days
    if diff > 0:
        return f"D-{diff}"
    if diff == 0:
        return "D-DAY"
    return f"D+{abs(diff)}"


def contest_embed(contest, color):
    name, date = contest
    embed = discord.Embed(title=f"📅 {name}", color=color)
    embed.add_field(name="남은 날짜", value=f"**{dday_label(date)}**", inline=True)
    embed.add_field(name="대회일", value=date.isoformat(), inline=True)
    return embed


def daily_dday_embed():
    embed = discord.Embed(title=f"⏰ 오늘의 D-Day ({today_kst().isoformat()})", color=0xF97316)
    for name, date in (LOCAL_CONTEST, NATIONAL_CONTEST):
        embed.add_field(name=name, value=f"**{dday_label(date)}** ({date.isoformat()})", inline=False)
    return embed


async def send_daily_dday():
    global last_dday_post
    channel = bot.get_channel(DDAY_CHANNEL_ID) or await bot.fetch_channel(DDAY_CHANNEL_ID)
    await channel.send(embed=daily_dday_embed())
    last_dday_post = datetime.datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[D-Day] {last_dday_post} 채널 {DDAY_CHANNEL_ID} 에 전송")


@tasks.loop(time=DDAY_POST_TIME)
async def daily_dday():
    days_left = (LOCAL_CONTEST[1] - today_kst()).days
    if 0 <= days_left <= DDAY_WINDOW_DAYS:
        try:
            await send_daily_dday()
        except Exception as e:
            print(f"[D-Day] 전송 실패: {e!r}")


@tasks.loop(seconds=30)
async def heartbeat():
    start = LOCAL_CONTEST[1] - datetime.timedelta(days=DDAY_WINDOW_DAYS)
    info = {
        "pid": os.getpid(),
        "beat": int(time.time()),
        "started": start_time.replace(tzinfo=datetime.timezone.utc).astimezone(KST).strftime("%Y-%m-%d %H:%M:%S"),
        "connected": not bot.is_closed() and bot.is_ready(),
        "latency_ms": None if bot.latency != bot.latency else int(bot.latency * 1000),  # NaN 방지
        "user": str(bot.user) if bot.user else None,
        "guilds": len(bot.guilds),
        "dday": {LOCAL_CONTEST[0]: dday_label(LOCAL_CONTEST[1]),
                 NATIONAL_CONTEST[0]: dday_label(NATIONAL_CONTEST[1])},
        "dday_channel": str(DDAY_CHANNEL_ID),
        "dday_post_from": start.isoformat(),
        "last_dday_post": last_dday_post,
    }
    tmp = STATUS_PATH + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False)
        os.replace(tmp, STATUS_PATH)
    except OSError as e:
        # 상태 페이지가 마침 읽는 중이면 윈도우에선 replace 가 실패한다 — 다음 주기에 다시 쓴다.
        # 예외를 흘리면 tasks.loop 가 멈춰 버린다.
        print(f"[heartbeat] 기록 실패: {e!r}")

@bot.event
async def on_ready():
    synced = await bot.tree.sync()  # 글로벌 동기화
    print(f"{len(synced)}개 동기화됨")
    if not heartbeat.is_running():
        heartbeat.start()
    if not daily_dday.is_running():
        daily_dday.start()
    # python sub.py --test-dday : 기동 직후 D-Day 알림을 한 번 보내 채널 연결을 확인
    if "--test-dday" in sys.argv[1:] and last_dday_post is None:
        try:
            await send_daily_dday()
        except Exception as e:
            print(f"[D-Day] 테스트 전송 실패: {e!r}")

@bot.tree.command(name="안녕", description="봇이 인사해줍니다")
async def hi(interaction: discord.Interaction):
    await interaction.response.send_message(f"안녕하세요, {interaction.user.mention}! 👋")

@bot.tree.command(name="1과제", description="1과제 무작위로 시/도를 뽑아줍니다")
async def task1(interaction: discord.Interaction):
    choice = random.choice(regions1)
    await interaction.response.send_message(f"1과제 뽑힌 지역은 **{choice}** 입니다!")

@bot.tree.command(name="2과제", description="2과제 무작위로 시/도를 뽑아줍니다")
async def task2(interaction: discord.Interaction):
    choice = random.choice(regions1)
    await interaction.response.send_message(f"2과제 뽑힌 지역은 **{choice}** 입니다!")

@bot.tree.command(name="3과제", description="3과제 무작위로 시/도를 뽑아줍니다")
async def task3(interaction: discord.Interaction):
    choice = random.choice(regions1)
    await interaction.response.send_message(f"3과제 뽑힌 지역은 **{choice}** 입니다!")

@bot.tree.command(name="업타임", description="봇이 얼마나 켜져있는지 알려줍니다")
async def uptime(interaction: discord.Interaction):
    now = datetime.datetime.utcnow()
    delta = now - start_time
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    await interaction.response.send_message(f"봇 업타임: {hours}시간 {minutes}분 {seconds}초")


@bot.tree.command(name="디데이", description="다가오는 기능경기대회까지 남은 날짜를 보여줍니다")
async def dday(interaction: discord.Interaction):
    embed = discord.Embed(title="📅 다가오는 대회 D-Day", color=0x34D399)
    for name, date in (LOCAL_CONTEST, NATIONAL_CONTEST):
        embed.add_field(name=name, value=f"**{dday_label(date)}** ({date.isoformat()})", inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="지방대회", description="지방기능경기대회까지 남은 날짜를 보여줍니다")
async def dday_local(interaction: discord.Interaction):
    await interaction.response.send_message(embed=contest_embed(LOCAL_CONTEST, 0x34D399))


@bot.tree.command(name="전국대회", description="전국기능경기대회까지 남은 날짜를 보여줍니다")
async def dday_national(interaction: discord.Interaction):
    await interaction.response.send_message(embed=contest_embed(NATIONAL_CONTEST, 0x6366F1))

# 봇 실행
bot.run("UR_TOKEN")
