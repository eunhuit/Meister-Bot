import os
import csv
import re
import time
import asyncio
import discord
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import StaleElementReferenceException

# ==========================================
# 봇 및 사용자 설정 영역
# ==========================================
UR_ID = "UR_ID"
UR_PW = "UR_PW"
UR_PASSCODE = "UR_PASSCODE"
TOKEN = "UR_TOKEN"
CHANNEL_ID = 0  # UR_CHANNEL_ID  
UR_ROLE_ID = 0  # UR_ROLE_ID
UR_USER_ID = 0  # UR_USER_ID  

TARGET_COMPET_CODE = "2026P00"  
TARGET_JOB_CODE = "337"         

chrome_driver_path = "./chromedriver-win64/chromedriver.exe"
csv_file = "data.csv"
url = "https://meister.hrdkorea.or.kr/main/main.do"
# ==========================================

options = Options()
# options.add_argument("--headless")

service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=options)

def login_meister(driver):
    driver.get(url)

    element = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[3]/div[1]/div/div/div[1]/ul/li[1]/a"))
    )
    element.click()

    id_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div[4]/div[3]/div[4]/div[2]/fieldset/div/form/dl[1]/dd/input"))
    )
    id_input.send_keys(UR_ID)

    pw_input = driver.find_element(By.XPATH, "/html/body/div[2]/div[4]/div[3]/div[4]/div[2]/fieldset/div/form/dl[2]/dd[1]/input")
    pw_input.send_keys(UR_PW)

    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "#loginFrm > a"))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
    time.sleep(0.5)
    login_button.click()

    extra_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div[4]/div[4]/div/div/div[2]/div[2]/div[1]/input"))
    )
    extra_input.send_keys(UR_PASSCODE)

    confirm_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="myModal"]/div/div/div[2]/div[2]/div[1]/button'))
    )
    confirm_button.click()
    time.sleep(1)

# 초기 스크래핑을 위한 로그인
login_meister(driver)
driver.get("https://meister.hrdkorea.or.kr/sub/3/3/7/skillMatchTournament/taskQuestionsList.do")

# 년도(대회코드) 및 직종 선택
compet_select_elem = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, "competCode"))
)
Select(compet_select_elem).select_by_value(TARGET_COMPET_CODE)

job_select_elem = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, "jobCode"))
)
Select(job_select_elem).select_by_value(TARGET_JOB_CODE)

input_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//input[@value='검색']"))
)
input_button.click()
time.sleep(1)

result = []

def scrape_current_page():
    rows = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "table.table_content01 tbody tr")
        )
    )
    for i, row in enumerate(rows, start=1):
        try:
            tds = row.find_elements(By.TAG_NAME, "td")
            if not tds:
                continue
            texts = [td.get_attribute("innerText").strip() for td in tds]
            
            # <a> 태그에서 게시물의 진짜 URL 접속용 고유 번호 추출
            seq_code = ""
            try:
                a_tag = row.find_element(By.TAG_NAME, "a")
                href = a_tag.get_attribute("href")
                onclick = a_tag.get_attribute("onclick")
                
                if href and "subjPrsntSeq=" in href:
                    match = re.search(r'subjPrsntSeq=(\d+)', href)
                    if match: seq_code = match.group(1)
                elif onclick:
                    match = re.search(r'[\'"](\d+)[\'"]', onclick)
                    if match: seq_code = match.group(1)
            except:
                pass
                
            texts.append(seq_code)
            result.append(texts)
        except StaleElementReferenceException:
            print(f"Row {i} is stale. 건너뜀.")

scrape_current_page()

while True:
    try:
        paging_links = driver.find_elements(By.CSS_SELECTOR, "div.paging a")
        if not paging_links:
            break
            
        active = driver.find_element(By.CSS_SELECTOR, "div.paging a.active")
        current_page = int(active.text) if active.text.isdigit() else 1

        next_page = None
        for link in paging_links:
            if link.text.isdigit() and int(link.text) == current_page + 1:
                next_page = link
                break

        if not next_page:
            for link in paging_links:
                if "다음" in link.text:
                    next_page = link
                    break

        if not next_page:
            break

        driver.execute_script("arguments[0].click();", next_page)
        time.sleep(2)
        scrape_current_page()

    except Exception as e:
        break

time.sleep(1)
driver.quit()

# ==========================================
# 🚀 '식별 번호' 기반 지역 및 과제 맵핑 로직 (식별번호 원본 포함!)
# ==========================================
def determine_region_details(raw_title_text):
    if not raw_title_text: 
        return "미상"
    
    # "IT네트워크시스템-2026-00004" 같은 텍스트에서 맨 끝의 숫자를 뽑아냅니다.
    match = re.search(r'(\d+)$', raw_title_text.strip())
    
    if match:
        num = int(match.group(1)) # "00004" -> 4로 변환
        
        # 주신 맵핑 규칙 적용
        mapping = {
            2: "서울 (1, 2, 3, 4과제)",
            3: "충남 (3과제)",
            4: "충남 (1과제)",
            5: "충북 (1, 2, 3과제)",
            6: "충북 (4과제)",
            7: "광주 (1, 2, 3, 4과제)",
            8: "충남 (4, 4, 4과제)",
            9: "전남 (3과제)",
            10: "대전 (2, 3, 4과제)"
        }
        # 맵핑된 시도(과제) 뒤에 원래 식별번호를 [ ] 안에 넣어서 합쳐줍니다!
        region_str = mapping.get(num, "기타지역")
        return f"{region_str} [{raw_title_text}]"
    
    return raw_title_text

# 데이터 후처리
titles = [row[2] for row in result]
raw_identifiers = [row[2].split()[0] if row[2] else "" for row in result]
seq_codes = [row[-1] for row in result] # URL 접속용 고유 번호 리스트

# 식별 번호를 "지역 (과제) [식별번호]" 포맷으로 변환!
regions = [determine_region_details(idx) for idx in raw_identifiers]

# 댓글 수(보통 "[26]" 형태로 적혀있음) 추출
def extract_number(text):
    match = re.search(r'\[(\d+)\]', text)
    return int(match.group(1)) if match else 0

region_numbers = [extract_number(title) for title in titles]
current_data = list(zip(regions, region_numbers, seq_codes))

prev_data = []
if os.path.exists(csv_file):
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader) 
        for row in reader:
            if len(row) >= 3:
                prev_data.append((row[0], int(row[1]), row[2]))

# 디스코드 전송 설정
MAX_FIELD_LENGTH = 1024

def split_text_into_chunks(text, max_length):
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

class OneTimeBot(discord.Client):
    def __init__(self, target_region, prev_n, curr_n, text_chunk, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_region = target_region
        self.prev_n = prev_n
        self.curr_n = curr_n
        self.text_chunk = text_chunk

    async def on_ready(self):
        print(f'봇 로그인: {self.user} ({self.user.id})')
        channel = self.get_channel(CHANNEL_ID)
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 역할 멘션 적용
        mention = f"<@&{UR_ROLE_ID}>"
        allowed = discord.AllowedMentions(users=True, roles=True)
        user = f"<@!{UR_USER_ID}>"

        if not channel:
            print("채널을 찾을 수 없습니다.")
            await self.close()
            return

        # 알림 메시지 구성 (이제 "충남 (1과제) [IT네트워크시스템-2026-00004]" 형태로 깔끔하게 뜹니다)
        description = f"자동 감지: **{self.target_region}**의 질의 개수가 {self.prev_n}개에서 {self.curr_n}개로 증가했습니다. 질의 내용 확인 부탁드립니다."
        chunks = split_text_into_chunks(self.text_chunk, MAX_FIELD_LENGTH - 10)

        embed = discord.Embed(
            title=f"{user}님, 새로운 질의가 올라왔습니다! ({today})",
            description=description,
            color=0x1abc9c
        )
        embed.add_field(name="새로 달린 질의 내용", value=f"```{chunks[0]}```", inline=False)

        await channel.send(content=f"{mention}", embed=embed, allowed_mentions=allowed)

        for i, chunk in enumerate(chunks[1:], start=2):
            continued_embed = discord.Embed(color=0x1abc9c)
            continued_embed.add_field(name=f"질의 내용 ({i})", value=f"```{chunk}```", inline=False)
            await channel.send(embed=continued_embed)

        await self.close()

message_printed = False

if prev_data:
    # URL 접속용 고유번호(seq_code)를 키값으로 사용해 순서 밀림 완벽 방지
    prev_dict = {row[2]: row[1] for row in prev_data}

    for region, curr_num, seq_code in current_data:
        # 이전에 기록된 댓글 수 가져오기 (없으면 현재 값)
        prev_num = prev_dict.get(seq_code, curr_num)

        if curr_num > prev_num:
            print(f"[{region}] 댓글 수 증가 감지: {prev_num} -> {curr_num}")
            message_printed = True
            
            driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)
            login_meister(driver)
            
            # 진짜 게시물 URL로 이동
            detail_url = f"https://meister.hrdkorea.or.kr/sub/3/3/7/skillMatchTournament/viewTaskQuestion.do?competCode={TARGET_COMPET_CODE}&jobCode={TARGET_JOB_CODE}&subjPrsntSeq={seq_code}"
            driver.get(detail_url)
            
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "comm_view"))
                )
            except Exception as e:
                pass
            
            comments = driver.find_elements(By.CLASS_NAME, "comm_view")
            
            comment_text = "내용을 불러오지 못했습니다."
            if comments:
                # 무조건 마지막에 달린 새 댓글을 긁어옴
                latest_comment = comments[-1]
                comment_text = latest_comment.text.strip()
                print("==================")
                print("추출된 댓글:\n", comment_text)
                print("==================")
            else:
                print("새로운 댓글을 찾지 못했습니다.")
                
            driver.quit()

            # 디스코드 봇 실행
            intents = discord.Intents.default()
            intents.guilds = True
            
            async def run_bot():
                async with OneTimeBot(region, prev_num, curr_num, comment_text, intents=intents) as bot:
                    await bot.start(TOKEN)
            
            asyncio.run(run_bot())

if not message_printed and prev_data:
    print("값의 변화가 없습니다.")

with open(csv_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Region", "Count", "SeqCode"])
    writer.writerows(current_data)