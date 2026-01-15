"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application  # [설명] WSGI 애플리케이션 팩토리 함수

# [설명] Django 설정 모듈을 환경 변수로 지정 (WSGI 서버가 참조)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# [설명] WSGI 서버(gunicorn, uWSGI 등)가 사용할 애플리케이션 객체
application = get_wsgi_application()
