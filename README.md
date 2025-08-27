# MeisterNet Discord Bot

이 프로젝트는 **마이스터넷(https://meister.hrdkorea.or.kr) 사이트에서 IT 네트워크 시스템 직종의 질의 데이터를 자동으로 크롤링하여 Discord 서버에 알림을 보내주는 봇**입니다.  
또한 간단한 **슬래시 명령어(Slash Command)** 기능도 제공하여, 무작위 지역 추첨이나 봇의 업타임 확인이 가능합니다.

---

## 기능

### 1. 데이터 크롤링
- `selenium`을 이용해 마이스터넷 사이트에 자동 로그인
- 특정 직종(IT 네트워크 시스템) 질의 게시판에서 데이터를 수집
- 이전 데이터(`data.csv`)와 비교하여 값 증가 감지
- 값이 증가하면 해당 질의 내용을 Discord 채널로 전송

### 2. Discord 알림
- 값 증가 시, 자동으로 **Discord Embed 메시지** 전송
- 역할 멘션(@Role) 포함
- 긴 메시지는 1024자 기준으로 분할 전송

### 3. 슬래시 명령어
- `/안녕` → 봇이 인사
- `/1과제`, `/2과제`, `/3과제` → 무작위 시/도 추첨
- `/업타임` → 봇이 켜져 있는 시간 표시

---

## 📦 설치 및 실행 방법

### 1. 저장소 클론
```bash
git clone https://github.com/your-repo/meisternet-discord-bot.git
cd meisternet-discord-bot
```

### 2. 
