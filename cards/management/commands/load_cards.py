import csv
from django.core.management.base import BaseCommand
from cards.models import Card

from django.conf import settings

class Command(BaseCommand):
    help = "카드 고릴라 CSV 데이터를 DB에 저장합니다."

    def handle(self, *args, **options):
        filePath = settings.BASE_DIR / "card_gorilla_cleaned.csv"
        
        try:
            # 1. 기존 데이터 삭제 (중복 방지)
            self.stdout.write("기존 카드 데이터를 삭제 중...")
            Card.objects.all().delete()
            
            with open(filePath, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                cardsToCreate = []
                
                for row in reader:
                    def cleanInt(val):
                        """
                        @name : cleanInt
                        @function: cleanInt - 문자열에서 숫자만 추출
                        @param : val
                        """
                        if not val:
                            return 0
                        num = "".join(filter(str.isdigit, str(val)))
                        return int(num) if num else 0

                    # 사용자님의 models.py 필드명에 정확히 맞춤
                    cardsToCreate.append(Card(
                        card_name=row["카드명"],
                        company=row["카드사"],
                        annual_fee_domestic=cleanInt(row["연회비_국내"]),
                        annual_fee_overseas=cleanInt(row["연회비_해외"]),  # 수정됨
                        baseline_requirements_text=row["전월실적_기준"],   # 전월실적을 텍스트 필드에 저장
                        benefit_cap_summary=row["주요혜택"],            # 주요혜택 요약에 저장
                    ))
                
                # 2. 새로운 데이터 일괄 저장
                if cardsToCreate:
                    Card.objects.bulk_create(cardsToCreate)
                    self.stdout.write(self.style.SUCCESS(f"성공: {len(cardsToCreate)}개의 카드가 저장되었습니다!"))
                else:
                    self.stdout.write(self.style.WARNING("CSV에 저장할 데이터가 없습니다."))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"에러 발생: {e}"))