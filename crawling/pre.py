import pandas as pd
import re

def cleanCardData(inputFile, outputFile):
    # CSV 파일 읽기
    df = pd.read_csv(inputFile, encoding='utf-8-sig')

    # 1. 연회비 정제 함수
    def parseAnnualFee(feeStr):
        # 기본값 0
        domestic = 0
        overseas = 0
        
        if pd.isna(feeStr) or '없음' in feeStr and '/' not in feeStr:
            return 0, 0

        # 금액 추출 (숫자와 콤마만 추출 후 정수 변환)
        parts = feeStr.split('/')
        for part in parts:
            # 숫자만 추출 (예: 20,000 -> 20000)
            amountMatch = re.search(r'([\d,]+)', part)
            amount = 0
            if amountMatch:
                amount = int(amountMatch.group(1).replace(',', ''))
            
            if '국내' in part:
                domestic = amount
            elif '해외' in part:
                overseas = amount
            elif len(parts) == 1: # '해외겸용 15,000원' 처럼 하나만 적힌 경우
                overseas = amount
                
        return domestic, overseas

    # 2. 전월실적 정제 함수
    def parsePerformance(perfStr):
        if pd.isna(perfStr) or '없음' in perfStr:
            return 0
        
        # 숫자 추출
        numMatch = re.search(r'(\d+)', perfStr)
        if numMatch:
            num = int(numMatch.group(1))
            # '만원' 단위 처리
            if '만원' in perfStr or '만 원' in perfStr:
                return num * 10000
            return num
        return 0

    # 데이터 적용
    # 연회비 분리 적용
    fees = df['연회비'].apply(parseAnnualFee)
    df['연회비_국내'] = [f[0] for f in fees]
    df['연회비_해외'] = [f[1] for f in fees]

    # 전월실적 변환 적용
    df['전월실적_기준'] = df['전월실적'].apply(parsePerformance)

    # 기존 컬럼 제거 또는 순서 재배치
    cols = ['카드명', '카드사', '연회비_국내', '연회비_해외', '전월실적_기준', '주요혜택']
    dfFinal = df[cols]

    # 결과 저장
    dfFinal.to_csv(outputFile, index=False, encoding='utf-8-sig')
    print(f"전처리 완료! 저장된 파일: {outputFile}")
    
    # 상위 5개 데이터 확인용 출력
    print(dfFinal.head())

if __name__ == "__main__":
    cleanCardData('card_gorilla_list.csv', 'card_gorilla_cleaned.csv')