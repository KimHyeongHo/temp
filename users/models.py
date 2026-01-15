from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

# 사용자 매니저 커스텀
class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None):
        if not email:
            raise ValueError('이메일은 필수입니다.')
        user = self.model(email=self.normalize_email(email), name=name)
        user.set_password(password) # 비밀번호 암호화 저장
        user.save(using=self._db)
        return user

    
#사용자 속성
class User(AbstractBaseUser): 
    user_id = models.BigAutoField(primary_key=True)
    email = models.EmailField(max_length=100, unique=True)
    #password = models.CharField(max_length=255) 장고가 내부적으로 처리해서 이거 있으면 중복됨
    name = models.CharField(max_length=50)
    age_group = models.CharField(max_length=10, null=True, blank=True)
    # False는 0(남성), True는 1(여성)로 매핑됩니다.
    gender = models.BooleanField(null=True, blank=True, help_text="0: 남성(False), 1: 여성(True)")
    password_reset_token = models.CharField(max_length=255, null=True, blank=True)
    password_reset_expires = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # 활성 유저 판단
    is_active = models.BooleanField(default=True)

    objects = UserManager() # 커스텀 매니저 연결

    USERNAME_FIELD = 'email'  # 로그인의 아이디로 사용할 필드
    REQUIRED_FIELDS = ['name'] # 유저 생성 시 필수 입력 필드

    class Meta:
        db_table = 'users'

# 사용자 카드 정보
class UserCard(models.Model):
    card_number = models.CharField(max_length=20, null=True, blank=True)  # [설명] 카드 번호 (사용자 등록 시 입력)
    user_card_id = models.BigAutoField(primary_key=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    card = models.ForeignKey('cards.Card', on_delete=models.CASCADE, db_column='card_id')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'user_cards'

# 월별 통계 정보
class MonthlyStat(models.Model):
    stat_id = models.BigAutoField(primary_key=True)
    target_month = models.CharField(max_length=45)
    total_spent = models.BigIntegerField(default=0)
    total_benefit = models.BigIntegerField(default=0)
    avg_group_spent = models.BigIntegerField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'monthly_stats'