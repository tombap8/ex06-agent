import random
# from utils import llm_call  # (선택) AI 에이전트의 추가 피드백이 필요할 경우 사용할 수 있습니다.

# [FR-01] 정답 생성 기능
def generate_answer() -> int:
    """1~100 사이의 임의의 숫자를 생성하여 반환합니다."""
    return random.randint(1, 100)

# [FR-02] 입력 검증 기능
def validate_input(user_input: str) -> tuple[bool, int]:
    """
    사용자 입력을 검증합니다.
    (유효성 여부, 파싱된 숫자)를 반환합니다.
    """
    try:
        num = int(user_input)
        if 1 <= num <= 100:
            return True, num
        else:
            return False, -1
    except ValueError:
        return False, -1

# [FR-03] 업/다운 판정 기능
def judge_guess(guess: int, answer: int) -> str:
    """입력값과 정답을 비교하여 힌트 메시지를 반환합니다."""
    if guess < answer:
        return "UP!\n더 큰 숫자입니다."
    elif guess > answer:
        return "DOWN!\n더 작은 숫자입니다."
    else:
        return "정답입니다!"

# [FR-06] 게임 종료 판정 기능
def check_game_over(attempts: int, max_attempts: int, is_correct: bool) -> bool:
    """게임 종료 여부를 확인합니다. (정답 맞춤 또는 기회 소진)"""
    return is_correct or attempts >= max_attempts

def play_game(best_score: int | None = None) -> int | None:
    """
    단일 게임 세션을 실행합니다.
    정답을 맞힌 시도 횟수를 반환하며, 실패하면 None을 반환합니다.
    """
    print("\n===== 업다운 게임 =====")
    print("1~100 사이 숫자를 맞혀보세요.")
    max_attempts = 5
    print(f"기회는 총 {max_attempts}번입니다.")
    
    # [선택 기능 C] 최고 기록 표시
    if best_score is not None:
        print(f"최고 기록 : {best_score}회 만에 성공")
    
    answer = generate_answer()
    attempts = 0
    
    # [선택 기능 A] 범위 표시를 위한 변수
    min_range = 1
    max_range = 100

    while not check_game_over(attempts, max_attempts, False):
        print(f"\n현재 범위 : {min_range} ~ {max_range}")
        user_input = input("숫자 입력 : ")
        
        is_valid, guess = validate_input(user_input)
        
        # [FR-02] 잘못된 입력 시 기회 차감 없음
        if not is_valid:
            print("1~100 사이의 정수를 정확히 입력해주세요. (기회 차감 없음)")
            continue
            
        attempts += 1
        hint = judge_guess(guess, answer)
        print(hint)
        
        # [FR-05] 게임 승리 처리
        if guess == answer:
            print("축하합니다!")
            print(f"{attempts}번째 시도 만에 정답을 맞혔습니다.")
            return attempts
            
        # [선택 기능 A] 범위 업데이트 로직
        if guess < answer:
            min_range = max(min_range, guess + 1)
        elif guess > answer:
            max_range = min(max_range, guess - 1)
            
        # [FR-04] 남은 기회 안내
        print(f"남은 기회 : {max_attempts - attempts}회")
        
        # [FR-06] 게임 패배 처리
        if check_game_over(attempts, max_attempts, False):
            print("\n게임 오버!")
            print(f"정답은 {answer}였습니다.")
            return None

def main():
    best_score = None
    
    while True:
        score = play_game(best_score)
        
        # [선택 기능 C] 최고 기록 갱신
        if score is not None:
            if best_score is None or score < best_score:
                best_score = score
        
        # [선택 기능 B] 재시작 기능
        while True:
            restart = input("\n다시 플레이하시겠습니까? (Y/N) : ").strip().upper()
            if restart in ['Y', 'N']:
                break
            print("Y 또는 N만 입력해주세요.")
            
        if restart == 'N':
            print("게임을 종료합니다. 감사합니다!")
            break

if __name__ == "__main__":
    main()
