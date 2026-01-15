import csv
import re
from cards.models import Card, CardBenefit
from category.models import Category
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = '카드 주요혜택 텍스트를 분석하여 카테고리별 혜택 데이터를 생성합니다.'

    def handle(self, *args, **options):
        category_map = {
            '식비': ['식음료', '식당', '푸드', '베이커리', '외식', '음식점'],
            '카페/디저트': ['카페', '커피', '스타벅스', '디저트', '제과'],
            '대중교통': ['대중교통', '버스', '지하철', '택시', '철도'],
            '편의점': ['편의점', 'GS25', 'CU', '세븐일레븐', '생활 편의'], # '생활 편의' 추가
            '온라인쇼핑': ['온라인 쇼핑', '온라인쇼핑', '쿠팡', '11번가', 'G마켓', '쇼핑'],
            '대형마트': ['마트', '이마트', '홈플러스', '롯데마트'],
            '주유/차량': ['주유', '충전', '주차', '정비', 'LPG'],
            '통신/공과금': ['통신', '공과금', '핸드폰', '전기', '수도'],
            '디지털구독': ['디지털콘텐츠', '멤버십', '넷플릭스', '유튜브', '구독', 'OTT'], # '디지털콘텐츠' 추가
            '문화/여가': ['영화', '테마파크', '놀이공원', '공연', '스포츠'],
            '의료/건강': ['병원', '약국', '건강검진'],
            '교육': ['학원', '교육', '도서', '서점'],
            '뷰티/잡화': ['뷰티', '화장품', '올리브영'],
            '여행/숙박': ['여행', '항공', '숙박', '호텔', '면세점'],
        }

        # 기존 혜택 연결 데이터 삭제 후 재설정
        CardBenefit.objects.all().delete()
        cards = Card.objects.all()
        benefit_count = 0

        for card in cards:
            text = card.benefit_cap_summary
            if not text: continue

            for cat_name, keywords in category_map.items():
                # 키워드가 텍스트에 포함되어 있는지 확인
                if any(kw in text for kw in keywords):
                    try:
                        category = Category.objects.get(category_name=cat_name)
                        
                        # 텍스트에서 해당 카테고리 근처의 숫자(%) 추출 시도
                        # 예: "디지털콘텐츠: 50%할인" 에서 50 추출
                        rate = 5.0 # 기본값
                        pattern = rf"({cat_name}|{'|'.join(keywords)}).*?(\d+)%"
                        match = re.search(pattern, text)
                        if match:
                            rate = float(match.group(2))
                        
                        CardBenefit.objects.get_or_create(
                            card=card,
                            category=category,
                            defaults={'benefit_rate': rate, 'benefit_limit': 10000}
                        )
                        benefit_count += 1
                    except Category.DoesNotExist:
                        continue

        self.stdout.write(self.style.SUCCESS(f'✅ 총 {benefit_count}건의 카테고리 혜택 연동 완료!'))