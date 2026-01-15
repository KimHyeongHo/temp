import csv
from django.core.management.base import BaseCommand
from django.db import transaction
from cards.models import Card

class Command(BaseCommand):
    help = 'CSV 파일을 읽어 기존 카드 데이터의 이미지 URL과 상세 정보를 업데이트합니다.'

    def handle(self, *args, **options):
        # 업로드된 파일 경로
        file_path = '/app/card_gorilla_list.csv'
        
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                updated_count = 0
                skipped_count = 0

                # 효율적인 업데이트를 위해 트랜잭션 사용
                with transaction.atomic():
                    for row in reader:
                        card_name = row['카드명']
                        company = row['카드사']
                        
                        # 카드명과 카드사가 동시에 일치하는 기존 데이터를 찾음
                        card = Card.objects.filter(card_name=card_name, company=company).first()
                        
                        if card:
                            # 필요한 필드(이미지 URL, 혜택 요약 등)만 선택적으로 업데이트
                            card.card_image_url = row.get('이미지URL', card.card_image_url)
                            card.benefit_cap_summary = row.get('주요혜택', card.benefit_cap_summary)
                            card.baseline_requirements_text = row.get('전월실적', card.baseline_requirements_text)
                            card.save()
                            updated_count += 1
                        else:
                            skipped_count += 1

                self.stdout.write(self.style.SUCCESS(
                    f'업데이트 완료: {updated_count}건 / 일치하는 데이터 없음: {skipped_count}건'
                ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"에러 발생: {e}"))