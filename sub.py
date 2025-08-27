import discord, random, datetime
from discord import app_commands
from discord.ext import commands

# 봇 기본 설정
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
start_time = datetime.datetime.utcnow()
regions1 = ["광주", "충남", "전남", "대전", "서울", "충북"]

@bot.event
async def on_ready():
    synced = await bot.tree.sync()  # 글로벌 동기화
    print(f"{len(synced)}개 동기화됨")

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

# 봇 실행
bot.run("UR_TOKEN")
