"""Exchange 클라이언트 사용 예제

이 스크립트는 .env 파일에서 설정을 읽어 Exchange 서버에 연결하고
최근 메일을 가져오는 예제를 보여줍니다.

사용 방법:
1. .env.example을 .env로 복사
2. .env 파일에 실제 Exchange 서버 정보 입력
3. python examples/example_usage.py 실행
"""

from src.exchange_client import ExchangeClient
from src.utils.config import Config
from src.utils.logger import setup_logger


def main():
    """메인 함수"""
    logger = setup_logger()

    # 설정 검증
    if not Config.validate():
        logger.error("환경 변수 설정이 올바르지 않습니다.")
        logger.error(
            "필수 환경 변수: EXCHANGE_SERVER, EXCHANGE_DOMAIN, "
            "EXCHANGE_USERNAME, EXCHANGE_PASSWORD"
        )
        return

    # Exchange 클라이언트 생성
    client = ExchangeClient()

    try:
        # 서버 연결
        if client.connect():
            logger.info("Exchange 서버에 성공적으로 연결되었습니다.")

            # 최근 메일 가져오기
            messages = client.get_inbox_messages(limit=10, days_back=7)
            logger.info(f"가져온 메일: {len(messages)}개")

            # 메일 정보 출력
            for i, msg in enumerate(messages, 1):
                print(f"\n{i}. {msg['subject']}")
                print(f"   발신자: {msg['sender_name']} <{msg['sender']}>")
                print(f"   수신일: {msg['datetime_received']}")
                print(f"   첨부파일: {msg['attachment_count']}개")

            # 폴더 목록 가져오기
            folders = client.get_folder_list()
            logger.info(f"메일함 개수: {len(folders)}개")
            print(f"\n사용 가능한 폴더: {', '.join(folders[:5])}...")

    except Exception as e:
        logger.error(f"오류 발생: {e}")

    finally:
        # 연결 종료
        client.disconnect()
        logger.info("연결이 종료되었습니다.")


if __name__ == "__main__":
    main()
