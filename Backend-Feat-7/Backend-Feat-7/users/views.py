from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiExample
from .models import User

class SignUpView(APIView):
    @extend_schema(
        summary="회원가입",
        description="테스트를 위해 비밀번호를 암호화하지 않고 저장합니다.",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "example": "test@example.com"},
                    "password": {"type": "string", "example": "password123"},
                    "name": {"type": "string", "example": "테스터"},
                },
                "required": ["email", "password", "name"],
            }
        },
        responses={201: OpenApiExample('회원가입 성공', value={"message": "회원가입 성공", "user_id": 1})},
        tags=['User']
    )
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        name = request.data.get('name')

        if not email or not password or not name:
            return Response({'error': '모든 정보를 채워주세요.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(email=email).exists():
            return Response({'error': '이미 존재하는 이메일입니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # [테스트용] 평문 저장
        user = User.objects.create(
            email=email,
            password=password, # 암호화 없이 그대로 저장
            name=name
        )

        """
        # [배포용] 암호화 저장 코드
        user = User.objects.create_user(
            email=email,
            password=password,
            name=name
        )
        """

        return Response({"message": "회원가입 성공", "result": {"user_id": user.user_id}}, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    @extend_schema(
        summary="로그인",
        description="평문 비밀번호로 인증을 진행합니다.",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "example": "test@example.com"},
                    "password": {"type": "string", "example": "password123"},
                },
            }
        },
        responses={200: OpenApiExample('로그인 성공', value={"token": {"access": "...", "refresh": "..."}})},
        tags=['User']
    )
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'error': '이메일과 비밀번호를 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': '존재하지 않는 이메일입니다.'}, status=status.HTTP_404_NOT_FOUND)
        
        # [테스트용] 평문 비교
        if user.password != password:
            return Response({'error': '비밀번호가 일치하지 않습니다.'}, status=status.HTTP_401_UNAUTHORIZED)

        """
        # [배포용] 암호화 비밀번호 검증 코드
        if not user.check_password(password):
            return Response({'error': '비밀번호가 일치하지 않습니다.'}, status=status.HTTP_401_UNAUTHORIZED)
        """
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': '로그인 성공',
            'user_id': str(user.user_id),
            'token': {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
        }, status=status.HTTP_200_OK)
