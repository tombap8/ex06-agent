import re
import asyncio
import aiohttp
import streamlit as st
from bs4 import BeautifulSoup
from utils import llm_call, llm_call_async

# Streamlit 페이지 설정
st.set_page_config(page_title="AI 크롤러 에이전트", page_icon="🕸️", layout="wide")

# 커스텀 CSS (결과 카드 UI)
st.markdown("""
<style>
    .result-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        border-left: 5px solid #4CAF50;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .result-card.failed {
        border-left: 5px solid #F44336;
    }
    @media (prefers-color-scheme: dark) {
        .result-card { background-color: #1e1e1e; color: white; }
    }
</style>
""", unsafe_allow_html=True)

#####################################################################
# [1. URL 목록 가져오기] 오케스트레이터 패턴 (Orchestrator)
#####################################################################
def get_target_urls(topic: str, count: int = 5):
    """
    오케스트레이터 역할: 메인 지시(주제)를 받아 크롤링할 URL 목록을 생성/수집합니다.
    실제 환경에서는 구글 검색 API 등을 사용하지만, 여기서는 에이전트 동작 확인을 위해
    LLM을 활용하여 해당 주제의 가상(또는 실제) 뉴스 URL 목록을 생성하도록 합니다.
    (빠른 테스트를 위해 5개로 기본 설정, 요구사항인 50개는 count 매개변수로 조절 가능)
    """
    
    prompt = f"""
    당신은 웹 크롤러 오케스트레이터입니다.
    주제: "{topic}"
    위 주제와 관련된 정보를 얻을 수 있는 실제 존재하는 유효한 웹사이트 또는 뉴스 카테고리 URL {count}개를 생성해주세요.
    반드시 https:// 로 시작하는 URL만 한 줄에 하나씩 출력하고 다른 설명은 절대 적지 마세요.
    """
    response = llm_call(prompt, model="gpt-4o")
    
    # 정규표현식을 사용하여 텍스트에서 URL만 강건하게 추출합니다.
    urls = re.findall(r'https?://[^\s"\'<>]+', response)
    # 중복 제거 및 요청한 개수만큼 자르기
    urls = list(dict.fromkeys(urls))[:count]
    
    # 만약 LLM이 포맷을 안 지켰을 경우를 대비한 안전 장치
    if not urls:
         urls = [
             "https://news.ycombinator.com/",
             "https://techcrunch.com/",
             "https://www.theverge.com/"
         ]
    
    return urls

#####################################################################
# [2-1. 각 URL 접속] 병렬 처리를 위한 비동기 HTML Fetch 함수
#####################################################################
async def fetch_html(session, url):
    """비동기적으로 웹페이지의 HTML을 가져옵니다. (Parallel 패턴을 지원하기 위함)"""
    try:
        # 브라우저인 것처럼 위장 (봇 차단 방지)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        async with session.get(url, headers=headers, timeout=10) as response:
            response.raise_for_status()
            html = await response.text()
            
            # 토큰 절약을 위해 BeautifulSoup으로 기본 텍스트만 1차 추출
            soup = BeautifulSoup(html, 'html.parser')
            for script in soup(["script", "style", "nav", "footer"]):
                script.decompose()
            text = soup.get_text(separator=' ', strip=True)
            return text[:3000] # LLM 컨텍스트 한도를 위해 앞부분 3000자만 사용
            
    except Exception as e:
        return f"Error Fetching URL: {str(e)}"

#####################################################################
# [2-2. 라우팅 패턴 (Routing)] HTML 복잡도에 따른 모델 선택
#####################################################################
def route_model_for_extraction(html_text: str) -> str:
    """
    가져온 텍스트의 복잡도나 길이에 따라 가벼운 모델과 무거운 모델을 라우팅합니다.
    """
    if "Error Fetching" in html_text or len(html_text) < 500:
        # 에러 메시지나 아주 짧은 텍스트는 복잡한 추론이 필요 없으므로 빠른 모델 사용
        return "gpt-4o-mini"
    else:
        # 텍스트가 길고 구조가 복잡하면 성능이 좋은 모델 사용
        return "gpt-4o"

#####################################################################
# [2-3. 기사 제목 추출] 프롬프트 체이닝 패턴 (Prompt Chaining)
#####################################################################
async def extract_title_chain(html_text: str, model: str, previous_feedback: str = "") -> str:
    """
    프롬프트 체이닝을 사용하여 노이즈를 제거하고 제목만 정확히 추출합니다.
    이전 실패(feedback)가 있다면 이를 반영하여 전략을 수정합니다.
    """
    # [단계 1] 본문 정제 및 요약 (노이즈 제거)
    step1_prompt = f"""
    아래는 웹페이지에서 추출한 텍스트입니다. 
    광고나 메뉴 등의 불필요한 내용을 무시하고, 실제 뉴스 기사의 '본문'과 '제목'으로 추정되는 핵심 내용만 정제해 주세요.
    {previous_feedback}
    
    [텍스트 시작]
    {html_text}
    [텍스트 끝]
    """
    cleaned_text = await llm_call_async(step1_prompt, model=model)
    
    # [단계 2] 정제된 텍스트에서 최종 '제목'만 추출
    step2_prompt = f"""
    아래는 정제된 뉴스 텍스트입니다. 이 기사의 '제목(Title)'만 한 줄로 정확히 추출하세요.
    다른 부가적인 설명(예: "제목은 ~입니다")은 절대 포함하지 마세요.
    
    [정제된 텍스트]
    {cleaned_text}
    """
    title = await llm_call_async(step2_prompt, model=model)
    return title.strip()

#####################################################################
# [3. 실패 시 재시도] 평가자-최적화자 패턴 (Evaluator-Optimizer)
#####################################################################
async def process_url_with_retry(session, url, max_retries=3, log_container=None):
    """
    서브 에이전트: 하나의 URL을 담당하며, HTML을 가져오고 추출한 뒤,
    평가자의 기준에 미달하면 전략을 수정하여 재시도(루프)합니다.
    """
    html_text = await fetch_html(session, url)
    
    # 라우팅 (적합한 모델 선택)
    selected_model = route_model_for_extraction(html_text)
    
    feedback = ""
    for attempt in range(1, max_retries + 1):
        # 최적화자(Generator): 체이닝을 통해 제목 추출 (피드백 반영)
        extracted_title = await extract_title_chain(html_text, selected_model, feedback)
        
        # 평가자(Evaluator): 추출된 제목이 유효한지 평가
        eval_prompt = f"""
        추출된 뉴스 제목을 평가하세요.
        
        [추출된 제목]: {extracted_title}
        
        [평가 기준]
        1. "Error", "Access Denied", "403 Forbidden", "Not Found" 등의 에러 메시지가 아닐 것.
        2. 문장이 아니라 기사 제목 형태일 것.
        3. 너무 길지 않을 것 (대략 100자 이내).
        
        위 기준을 모두 만족하면 "PASS"를 출력하고, 
        만족하지 못하면 "FAIL"과 함께 무엇이 문제인지, 다음 추출 시 어떤 부분을 주의해야 하는지 피드백을 작성하세요.
        """
        evaluation = await llm_call_async(eval_prompt, model="gpt-4o-mini")
        
        if "PASS" in evaluation.upper():
            return {"url": url, "title": extracted_title, "status": "Success", "attempts": attempt}
        else:
            if log_container:
                log_container.warning(f"⚠️ [Evaluator] 실패 (시도 {attempt}/{max_retries}) - {url}\n사유: {evaluation.strip()}")
            # 실패 시 피드백을 추가하여 다음 루프에서 Generator가 참고할 수 있게 함
            feedback = f"\n[이전 시도 실패 피드백]: {evaluation}\n위 피드백을 반영하여 HTML 내 다른 위치에서 올바른 제목을 찾아보세요."
            
    # 최대 재시도 횟수 초과
    return {"url": url, "title": extracted_title, "status": "Failed", "attempts": max_retries}

#####################################################################
# 메인 비동기 실행 영역 (Parallel Pattern)
#####################################################################

# UI 사이드바 및 메인 화면 구성
st.title("🕷️ 지능형 AI 웹 크롤러 에이전트")
st.markdown("LLM을 활용한 **오케스트레이터, 병렬 처리, 모델 라우팅, 프롬프트 체이닝, 평가자-최적화자(재시도)** 패턴이 적용된 웹 크롤러입니다.")

with st.sidebar:
    st.header("⚙️ 크롤러 설정")
    target_topic = st.text_input("수집할 뉴스 주제", value="최신 인공지능(AI) 기술 동향")
    url_count = st.number_input("수집할 URL 개수", min_value=1, max_value=50, value=5, step=1)
    start_btn = st.button("🚀 크롤링 시작", use_container_width=True)

if start_btn:
    async def main_async():
        # 1. 오케스트레이터
        st.subheader("1️⃣ URL 목록 수집 (Orchestrator)")
        status_msg = st.empty()
        status_msg.info(f"LLM 오케스트레이터가 '{target_topic}' 관련 URL을 탐색 중입니다...")
        
        urls = get_target_urls(target_topic, count=url_count)
        status_msg.success(f"✅ 대상 URL {len(urls)}개 확보 완료!")
        
        with st.expander("수집된 URL 목록 보기", expanded=False):
            for u in urls:
                st.write(f"- {u}")
                
        # 2. 병렬 처리 (Parallel) & 서브 에이전트
        st.subheader("2️⃣ 병렬 크롤링 및 정보 추출 (Parallel + Subagents)")
        progress_bar = st.progress(0.0)
        
        log_expander = st.expander("에이전트 작업 로그 (실시간)", expanded=True)
        
        async with aiohttp.ClientSession() as session:
            tasks = [asyncio.create_task(process_url_with_retry(session, url, max_retries=3, log_container=log_expander)) for url in urls]
            
            results = []
            completed = 0
            # 완료되는 순서대로 처리하여 프로그레스 바 업데이트
            for task in asyncio.as_completed(tasks):
                res = await task
                results.append(res)
                completed += 1
                progress_bar.progress(completed / len(urls))
                
                status_icon = "✅ 성공" if res['status'] == 'Success' else "❌ 실패"
                log_expander.write(f"**[{status_icon}]** {res['url']} (시도: {res['attempts']}회)")
                
        # 3. 결과 종합 (Aggregation)
        st.subheader("🎯 최종 수집 결과")
        for res in results:
            card_class = "result-card" if res['status'] == 'Success' else "result-card failed"
            icon = "✅" if res['status'] == 'Success' else "❌"
            
            st.markdown(f'''
            <div class="{card_class}">
                <h4 style="margin-top: 0;">{icon} {res['title']}</h4>
                <a href="{res['url']}" target="_blank" style="color: #1E88E5; text-decoration: none;">🔗 {res['url']}</a>
                <p style="margin: 5px 0 0 0; font-size: 0.9em; color: gray;">
                    상태: {res['status']} | 시도 횟수: {res['attempts']}회
                </p>
            </div>
            ''', unsafe_allow_html=True)
            
        st.balloons()

    # 비동기 메인 함수 실행
    asyncio.run(main_async())


# =============================================================================
# [ AI Agent Web Crawler Workflow Diagram ]
# =============================================================================

#                       [ 1. Orchestrator ]
#                 "특정 주제의 뉴스 기사 URL 50개 확보"
#                               │
#               ┌───────────────┼───────────────┐  (Returns List of URLs)
#               ▼               ▼               ▼
#         +-----------+   +-----------+   +-----------+
#         | URL 1     |   | URL 2     |   | URL n     |
#         +-----------+   +-----------+   +-----------+
#               │               │               │
# =============================================================================
# [ 2. Parallel Subagents (asyncio.gather) ]

#     (각 URL마다 독립적으로 아래 프로세스 동시 실행)

#               │
#         +-----------------------------------+
#         |  [ HTML Fetch (aiohttp + BS4) ]   | 
#         +-----------------------------------+
#               │
#               ▼
#         +-----------------------------------+
#         |       [ Routing Pattern ]         |
#         |  HTML 길이에 따라 모델 자동 선택  |
#         | (gpt-4o-mini  vs  gpt-4o)         |
#         +-----------------------------------+
#               │
#               ▼
# +-------------------------------------------------------+
# | [ Evaluator - Optimizer Loop (재시도 패턴) ]          |
# |                                                       |
# |    +---------------------------------------------+    |
# |    | [ Prompt Chaining Pattern ] (Generator)     |    |
# |    | Step 1: 광고 제거 및 텍스트 정제            |    |
# |    | Step 2: 정제된 텍스트에서 '제목'만 추출     |<---+
# |    +---------------------------------------------+    |
# |                          │                            |
# |                          ▼                            |
# |    +---------------------------------------------+    |
# |    | [ Evaluator ]                               |    |
# |    | 추출된 제목이 정상적인 형태인지 평가        |    |
# |    | (에러메시지 여부, 길이 등)                  |    |
# |    +---------------------------------------------+    |
# |             │                       │                 |
# |        [ PASS ]                  [ FAIL ]             |
# |             │                       │                 |
# |             │                       +-----------------+
# |             │                         (피드백 전달 및 재시도)
# |             ▼
# |      [ 최종 제목 반환 ]
# +-------------------------------------------------------+
#               │
#               ▼
#       [ 3. 모든 결과 종합 (Aggregation) ]
# =============================================================================
