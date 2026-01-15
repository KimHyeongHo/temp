from django.test import TestCase

# Create your tests here.
# cards/tests.py 예시
import requests
import json
import os

class CodefApiTest(TestCase):
    def test_get_approval_list(self):
        # 테스트에 필요한 정보
        url = "https://sandbox.codef.io/v1/kr/card/p/account/approval-list"
        access_token = os.getenv('DB_ACCESS_TOKEN')
        connected_id = os.getenv('DB_CONNECTED_ID')

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "connectedId": connected_id,
            "organization": "0301",
            "startDate": "20251201",
            "endDate": "20260113",
            "inquiryType": "1"
        }

        # 실행
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        result = response.json()

        # 검증 (성공 코드가 왔는지 확인)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(result['result']['code'], 'CF-00000')
        
        # 결과 확인을 위해 출력 (옵션)
        print(json.dumps(result, indent=4, ensure_ascii=False))