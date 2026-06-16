import streamlit as st
import random

# 페이지 설정
st.set_page_config(
    page_title="스펙타클 업다운 게임",
    page_icon="🎮",
    layout="centered"
)

# 커스텀 CSS로 화려하게
st.markdown("""
<style>
    .big-title {
        font-size: 3rem;
        color: #ff4b4b;
        text-align: center;
        font-weight: 900;
        text-shadow: 2px 2px 4px #00000055;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 1.2rem;
        color: #fca311;
        text-align: center;
        margin-bottom: 20px;
    }
    .range-box {
        background: linear-gradient(90deg, #1cb5e0 0%, #000851 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .history-card {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
        margin-top: 10px;
        border-left: 5px solid #ff4b4b;
        color: black;
    }
    @media (prefers-color-scheme: dark) {
        .history-card {
            background-color: #2b2b2b;
            color: white;
        }
    }
    
    /* 입력창 글자 크기 키우기 */
    div[data-testid="stNumberInput"] input {
        font-size: 3rem !important;
        font-weight: 900;
        text-align: center;
        padding: 20px !important;
    }
    div[data-testid="stNumberInput"] label p {
        font-size: 1.2rem !important;
        font-weight: bold;
    }
    
    /* 제출 버튼 크기 키우기 */
    div[data-testid="stFormSubmitButton"] button {
        font-size: 1.5rem !important;
        font-weight: bold;
        padding: 15px !important;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'answer' not in st.session_state:
    st.session_state.answer = random.randint(1, 100)
    st.session_state.attempts = 0
    st.session_state.max_attempts = 5
    st.session_state.min_range = 1
    st.session_state.max_range = 100
    st.session_state.game_over = False
    st.session_state.history = []
    st.session_state.best_score = None

def reset_game():
    st.session_state.answer = random.randint(1, 100)
    st.session_state.attempts = 0
    st.session_state.min_range = 1
    st.session_state.max_range = 100
    st.session_state.game_over = False
    st.session_state.history = []

# 헤더
st.markdown('<div class="big-title">🚀 업다운 게임 🚀</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">1부터 100 사이의 숫자를 맞춰보세요! 기회는 단 5번!</div>', unsafe_allow_html=True)

# 현재 UP/DOWN 상태 표시 (상단 하이라이트)
if st.session_state.history and not st.session_state.game_over:
    last_guess, last_result = st.session_state.history[-1]
    if "UP" in last_result:
        bg_color = "linear-gradient(135deg, #ff9a9e 0%, #fecfef 99%, #fecfef 100%)"
        text_color = "#d32f2f"
    else:
        bg_color = "linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%)"
        text_color = "#1976d2"
        
    st.markdown(f'''
    <div style="background: {bg_color}; border-radius: 15px; padding: 20px; text-align: center; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
        <h2 style="color: {text_color}; margin: 0; font-size: 3.5rem; font-weight: 900; text-shadow: 1px 1px 2px rgba(255,255,255,0.8);">{last_guess} ➔ {last_result}</h2>
    </div>
    ''', unsafe_allow_html=True)

# 메트릭스 패널
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("🏆 최고 기록", f"{st.session_state.best_score}회" if st.session_state.best_score else "없음")
with col2:
    st.metric("🎯 남은 기회", f"{st.session_state.max_attempts - st.session_state.attempts}회")
with col3:
    st.metric("📈 현재 범위", f"{st.session_state.min_range} ~ {st.session_state.max_range}")

# 진행률 바
progress = st.session_state.attempts / st.session_state.max_attempts
st.progress(progress, text=f"진행 상황: {st.session_state.attempts} / {st.session_state.max_attempts}")

st.markdown('<div class="range-box">🔍 탐색 범위: {} ~ {} </div>'.format(st.session_state.min_range, st.session_state.max_range), unsafe_allow_html=True)
st.write("")

# 입력 폼
if not st.session_state.game_over:
    with st.form("guess_form", clear_on_submit=True):
        guess = st.number_input("숫자를 입력하세요 (1~100):", min_value=1, max_value=100, step=1, value=None, placeholder="숫자 입력")
        submitted = st.form_submit_button("도전! 🎯", use_container_width=True)
        
        if submitted:
            if guess is None:
                st.warning("⚠️ 숫자를 입력해주세요!")
            else:
                if guess < st.session_state.min_range or guess > st.session_state.max_range:
                    st.warning("⚠️ 현재 범위 안의 숫자를 입력하는 것이 좋습니다!")
                    
                st.session_state.attempts += 1
                
                if guess == st.session_state.answer:
                    st.session_state.history.append((guess, "🎉 정답!"))
                    st.session_state.game_over = True
                    
                    # 최고 기록 갱신
                    if st.session_state.best_score is None or st.session_state.attempts < st.session_state.best_score:
                        st.session_state.best_score = st.session_state.attempts
                        
                elif guess < st.session_state.answer:
                    st.session_state.history.append((guess, "🔺 UP!"))
                    st.session_state.min_range = max(st.session_state.min_range, guess + 1)
                else:
                    st.session_state.history.append((guess, "🔻 DOWN!"))
                    st.session_state.max_range = min(st.session_state.max_range, guess - 1)
                    
                if st.session_state.attempts >= st.session_state.max_attempts and not st.session_state.game_over:
                    st.session_state.game_over = True
                    
                st.rerun()

# 게임 종료 후 메시지
if st.session_state.game_over:
    if st.session_state.history[-1][1] == "🎉 정답!":
        st.success(f"축하합니다! 🎉 {st.session_state.attempts}번째 시도만에 정답({st.session_state.answer})을 맞췄습니다!")
        st.balloons()
    else:
        st.error(f"게임 오버! 😭 정답은 {st.session_state.answer}였습니다.")
        st.snow()
        
    if st.button("🔄 다시 플레이하기", use_container_width=True):
        reset_game()
        st.rerun()

# 히스토리 출력
if st.session_state.history:
    st.markdown("### 📝 기록")
    for i, (g, result) in enumerate(reversed(st.session_state.history)):
        idx = len(st.session_state.history) - i
        color = "#2e7d32" if "정답" in result else ("#c62828" if "UP" in result else "#1565c0")
        st.markdown(f'<div class="history-card"><strong>{idx}회차:</strong> 입력한 숫자 <b>{g}</b> ➔ <span style="color:{color}; font-weight:bold;">{result}</span></div>', unsafe_allow_html=True)