afrom tabulate import tabulate
from discord.ext import commands
import re
import os
import csv
import requests
import discord
import asyncio
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

chrome_driver_path = "./chromedriver-win64/chromedriver.exe"

options = Options()
# options.add_argument("--headless")  # 이 줄을 주석 처리하거나 삭제하세요

service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=options)

url = "https://meister.hrdkorea.or.kr/main/main.do"
driver.get(url)

# 마이스터넷 로그인 창
element = driver.find_element(By.XPATH, "/html/body/div[2]/div[3]/div[1]/div/div/div[1]/ul/li[1]/a")
element.click()

# ID 입력
id_input = driver.find_element(By.XPATH, "/html/body/div[2]/div[4]/div[3]/div[4]/div[2]/fieldset/div/form/dl[1]/dd/input")
id_input.send_keys("UR_ID")

# PW 입력
pw_input = driver.find_element(By.XPATH, "/html/body/div[2]/div[4]/div[3]/div[4]/div[2]/fieldset/div/form/dl[2]/dd[1]/input")
pw_input.send_keys("UR_PW")

time.sleep(1)

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

#로그인 버튼 클릭
login_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "#loginFrm > a"))
)
driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
time.sleep(0.5)
login_button.click()

time.sleep(1)
#2차인증 생년월일 입력
extra_input = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div[4]/div[4]/div/div/div[2]/div[2]/div[1]/input"))
)
extra_input.send_keys("UR_PASSCODE")

confirm_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="myModal"]/div/div/div[2]/div[2]/div[1]/button'))
)
confirm_button.click()

time.sleep(1)

driver.get("https://meister.hrdkorea.or.kr/sub/3/3/7/skillMatchTournament/taskQuestionsList.do")

#직종 선택란 클릭
select_element = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div[4]/div[3]/form/div[1]/div/select[2]"))
)
#IT네트워크시스템
option = select_element.find_elements(By.TAG_NAME, "option")[51]
option.click()

#검색 버튼 클릭
input_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[4]/div[3]/form/div[1]/div/div/input[2]"))
)
input_button.click()

result = []

# 현재 페이지 데이터 긁기 함수
def scrape_current_page():
    rows = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located(
            (By.XPATH, "/html/body/div[2]/div[4]/div[3]/form/div[1]/table/tbody/tr")
        )
    )
    for i, row in enumerate(rows, start=1):
        try:
            tds = row.find_elements(By.TAG_NAME, "td")
            if not tds:
                continue
            texts = [td.get_attribute("innerText").strip() for td in tds]
            result.append(texts)
        except StaleElementReferenceException:
            print(f"Row {i} is stale. 건너뜀.")

# 첫 페이지 긁기
scrape_current_page()

# 페이지네이션 순회
while True:
    try:
        paging_links = driver.find_elements(By.CSS_SELECTOR, "div.paging a")
        active = driver.find_element(By.CSS_SELECTOR, "div.paging a.active")
        current_page = int(active.text) if active.text.isdigit() else 1

        next_page = None
        # 다음 번호 찾기
        for link in paging_links:
            if link.text.isdigit() and int(link.text) == current_page + 1:
                next_page = link
                break

        # 없으면 "다음" 버튼
        if not next_page:
            for link in paging_links:
                if "다음" in link.text:
                    next_page = link
                    break

        if not next_page:
            print("마지막 페이지 도달")
            break

        driver.execute_script("arguments[0].click();", next_page)
        time.sleep(2)
        scrape_current_page()

    except Exception as e:
        print("페이지 이동 실패:", e)
        break

time.sleep(3)
driver.quit()

print("#####")
print(result)
print("#####")

# 데이터 후처리
result = result[1:]  # 첫 번째 헤더 제거
titles = [row[3] for row in result]
regions = [row[2] for row in result]

def extract_number(region):
    match = re.search(r'\[(\d+)\]', region)
    return int(match.group(1)) if match else 0

region_numbers = [extract_number(title) for title in titles]

csv_file = "data.csv"
current_data = list(zip(regions, region_numbers))

print(current_data)


# 이전 데이터 불러오기
prev_data = []
if os.path.exists(csv_file):
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            prev_data.append((row[0], int(row[1])))

# 값이 올라가 있는지 확인
message_printed = False
if prev_data:
    for (region, prev_num), (_, curr_num) in zip(prev_data, current_data):
        if curr_num > prev_num:
            print(f"{region}의 값이 {prev_num}에서 {curr_num}로 증가했습니다.")

            service = Service(chrome_driver_path)
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(url)

            # 마이스터넷 로그인 창
            element = driver.find_element(By.XPATH, "/html/body/div[2]/div[3]/div[1]/div/div/div[1]/ul/li[1]/a")
            element.click()

            # ID 입력
            id_input = driver.find_element(By.XPATH, "/html/body/div[2]/div[4]/div[3]/div[4]/div[2]/fieldset/div/form/dl[1]/dd/input")
            id_input.send_keys("UR_ID")

            # PW 입력
            pw_input = driver.find_element(By.XPATH, "/html/body/div[2]/div[4]/div[3]/div[4]/div[2]/fieldset/div/form/dl[2]/dd[1]/input")
            pw_input.send_keys("UR_PW")

            time.sleep(1)


            #로그인 버튼 클릭
            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#loginFrm > a"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
            time.sleep(0.5)
            login_button.click()

            time.sleep(1)
            #2차인증 생년월일 입력
            extra_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div[4]/div[4]/div/div/div[2]/div[2]/div[1]/input"))
            )
            extra_input.send_keys("UR_PASSCODE")

            confirm_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="myModal"]/div/div/div[2]/div[2]/div[1]/button'))
            )
            confirm_button.click()

            time.sleep(1)

            driver.get("https://meister.hrdkorea.or.kr/sub/3/3/7/skillMatchTournament/taskQuestionsList.do")

            #직종 선택란 클릭
            select_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div[4]/div[3]/form/div[1]/div/select[2]"))
            )
            #IT네트워크시스템
            option = select_element.find_elements(By.TAG_NAME, "option")[51]
            option.click()

            #검색 버튼 클릭
            input_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[4]/div[3]/form/div[1]/div/div/input[2]"))
            )
            input_button.click()
            
            time.sleep(1)

            if region == "서울":
                code = "14047"
            elif region == "대전":
                code = "14045"
            elif region == "충남":
                code = "14032"
            elif region == "광주":
                code = "14018"
            elif region == "전남":
                code = "13875"
            elif region == "경기":
                code = "13800"
            elif region == "충북":
                code = "13759"
            driver.get(f"https://meister.hrdkorea.or.kr/sub/3/3/7/skillMatchTournament/viewTaskQuestion.do?competCode=2025P00&jobCode=337&subjPrsntSeq={code}")

            comments = driver.find_elements(By.CLASS_NAME, "comm_view")

            n = curr_num
            if len(comments) >= n:
                nth_comment = comments[n - 1]
                print(nth_comment.text.strip())
            else:
                print(f"{n}번쨰 답 X, 총 댓글 수: {len(comments)}")

            TOKEN='UR_TOKEN'
            CHANNEL_ID = UR_CHANNEL_ID

MAX_FIELD_LENGTH = 1024

def split_text_into_chunks(text, max_length):
    """지정된 길이로 텍스트를 나눔"""
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

class OneTimeBot(discord.Client):
    async def on_ready(self):
        print(f'봇 로그인: {self.user} ({self.user.id})')
        channel = self.get_channel(CHANNEL_ID)
        today = datetime.now().strftime("%Y-%m-%d")
        role_id = UR_ROLE_ID
        mention = f"<@&{role_id}>"
        allowed = discord.AllowedMentions(users=True, roles=True)
        user_id = UR_ID
        user = f"<@!{user_id}>"

        if not channel:
            print("채널을 찾을 수 없습니다.")
            await self.close()
            return

        # 메시지 본문 구성
        description = f"자동 감지: {region}의 값이 {prev_num}에서 {curr_num}로 증가했습니다. 질의 내용 확인 부탁드립니다."
        chunks = split_text_into_chunks(nth_comment.text.strip(), MAX_FIELD_LENGTH - 10)  # 여유공간 고려

        # 첫 번째 Embed 생성
        embed = discord.Embed(
            title=f"{user}님, {region}에 새로운 질의가 올라왔습니다. ({today})",
            description=description,
            color=0x1abc9c
        )
        embed.add_field(name="질의 내용 (1)", value=f"```{chunks[0]}```", inline=False)

        await channel.send(content=f"{mention}", embed=embed, allowed_mentions=allowed)

        # 나머지 부분 추가 전송
        for i, chunk in enumerate(chunks[1:], start=2):
            continued_embed = discord.Embed(color=0x1abc9c)
            continued_embed.add_field(name=f"질의 내용 ({i})", value=f"```{chunk}```", inline=False)
            await channel.send(embed=continued_embed)

        await self.close()

# 아래는 그대로 유지
intents = discord.Intents.default()
intents.guilds = True

async def main():
    async with OneTimeBot(intents=intents) as bot:
        await bot.start(TOKEN)

asyncio.run(main())
if not message_printed and prev_data:
    print("값의 변화가 없습니다.")

# 현재 데이터 CSV로 저장
with open(csv_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Region", "Count"])
    writer.writerows(current_data)
