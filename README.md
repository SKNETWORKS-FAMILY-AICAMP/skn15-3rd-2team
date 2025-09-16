# 🧠 skn15-3rd-2team

## 👥 1. 팀 소개

<table>
  <tr>
    <td align="center" width="150">
      <a href="https://github.com/juyeonkwon">
        <img src="https://github.com/juyeonkwon.png" width="80" style="border-radius:50%;" alt="권주연 아바타"/><br/>
        <strong>권주연</strong><br/><sub>[팀장]</sub><br/><code>@juyeonkwon</code><br/>
      </a>
    </td>
    <td align="center" width="150">
      <a href="https://github.com/solchna">
        <img src="https://github.com/solchna.png" width="80" style="border-radius:50%;" alt="조솔찬 아바타"/><br/>
        <strong>조솔찬</strong><br/><code>@solchna</code><br/>
      </a>
    </td>
    <td align="center" width="150">
      <a href="https://github.com/asdg441">
        <img src="https://github.com/asdg441.png" width="80" style="border-radius:50%;" alt="노건우 아바타"/><br/>
        <strong>노건우</strong><br/><code>@asdg441</code><br/>
      </a>
    </td>
    <td align="center" width="150">
      <a href="https://github.com/dahyun11">
        <img src="https://github.com/dahyun11.png" width="80" style="border-radius:50%;" alt="하다현 아바타"/><br/>
        <strong>하다현</strong><br/><code>@dahyun11</code><br/>
      </a>
    </td>
    <td align="center" width="150">
      <a href="https://github.com/jeong-mincheol">
        <img src="https://github.com/jeong-mincheol.png" width="80" style="border-radius:50%;" alt="정민철 아바타"/><br/>
        <strong>정민철</strong><br/><code>@jeong-mincheol</code><br/>
      </a>
    </td>
    <td align="center" width="150">
      <a href="https://github.com/AQUAQUA5">
        <img src="https://github.com/AQUAQUA5.png" width="80" style="border-radius:50%;" alt="오원장 아바타"/><br/>
        <strong>오원장</strong><br/><code>@AQUAQUA5</code><br/>
      </a>
    </td>
  </tr>
</table>

---

## 🗓️ 2. 프로젝트 기간

<div align="center">
  <strong>📅 2025년 8월 22일(금) ~ 8월 25일(월)</strong>
</div>

---

## 🧩 3. 프로젝트 개요

### 📕 프로젝트명
**취업하Job – 당신의 AI 취업 도우미**

### ✅ 배경 및 목적

취업 준비 시 수많은 공고 중 나에게 맞는 것을 찾는 데 **많은 시간**이 소요됩니다.  
**취업하Job** 은 사용자의 희망 조건(직무, 지역, 급여, 근무형태 등)과 역량(자격증, 기술, 경험 등)을 받아  
**조건에 부합하는 공고만 필터링**해주고,  
**기업 인재상과 자소서 DB**를 바탕으로 **자기소개서를 자동 생성 및 첨삭**해줍니다.

### 🖐️ 시스템 요약

**Streamlit 기반 통합 시스템**으로 다음 기능을 제공합니다:

#### 🔗 공고 검색
- 사용자의 조건 및 역량을 입력받아
- LLM을 통해 직무 키워드 추론
- **잡코리아에서 역할별 공고 Top-N 자동 수집**

#### ✍️ 자소서 생성 및 첨삭
- 합격자 자소서 패턴 + 기업 인재상 기반
- 입력 스펙 기반 자소서 초안 작성
- 기존 자소서는 **톤/분량/적합도**를 고려해 **자동 첨삭**

---

## 🏗️ 4. 아키텍처

### 🔍 채용 공고 검색 시스템

- 사용자 입력 → LLM 기반 스펙 구조화
- 키워드 확장 → Playwright 크롤링
- 역할별 공고 리스트를 Streamlit UI에 출력

<img width="2187" height="903" alt="Image" src="https://github.com/user-attachments/assets/4c782f7d-fc6d-4a71-9fd3-79137ec2daf7" />

### ✍️ 자기소개서 생성 시스템

- 회사명·직무·스펙 → 기업 DB 조회
- 자소서 작성용 프롬프트 생성 → LLM 호출
- 생성된 자소서에 대해 자동 피드백 생성
- Streamlit UI에 최종 결과 출력

<p align="center">
  <img width="3366" height="678" alt="jasoseo" src="https://github.com/user-attachments/assets/0d986c8c-32b7-4e3b-b9bf-254019f9f73e" />
</p>

---

## 🎯 5. 기대효과

### ⏱ 시간 절약 & 효율적인 지원
- 공고 탐색, 자소서 작성·첨삭 시간 절감  
- 본질적인 준비(면접 등)에 집중 가능  
- **취업 준비의 전반적인 생산성 향상**

---

## ⚙️ 6. 기술 스택

### 🖥️ Frontend  
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)

### 🧠 Backend / LLM  
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)  
![LangChain](https://img.shields.io/badge/LangChain-4B8BBE?style=for-the-badge)  
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)  
![Pydantic](https://img.shields.io/badge/Pydantic-008000?style=for-the-badge)

### 📊 Embedding / Ranking  
![sentence-transformers](https://img.shields.io/badge/sentence--transformers-00599C?style=for-the-badge)  
![scikit-learn](https://img.shields.io/badge/Scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)

### 🕸️ Crawling / Async  
![Playwright](https://img.shields.io/badge/Playwright-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)  
![asyncio](https://img.shields.io/badge/asyncio-005571?style=for-the-badge)
