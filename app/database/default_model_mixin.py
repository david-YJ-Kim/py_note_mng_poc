import uuid

from sqlalchemy import Column, String, DateTime, func, Enum as SqlEnum
from sqlalchemy.orm import DeclarativeBase

from app.spec.constant.ModelEnums import UseStatEnum


class Base(DeclarativeBase):
    """
    SQLAlchemy 2.0 Base 클래스
    모든 Entity가 이 클래스를 상속받습니다.
    """
    # SQLAlchemy 2.0 호환성: 기존 타입 힌팅 방식 허용
    __allow_unmapped__ = True


class ObjIdMixin:
    """obj_id Mixin 클래스"""
    # obj_id: Optional[str]  # 타입 힌팅 제거 (SQLAlchemy 2.0 호환성)
    obj_id = Column(
        "obj_id",
        String(100),
        primary_key=True,
        default=lambda: uuid.uuid4().hex,  # 32자리 hex 문자열
        nullable=False,
        comment="레코드 ID"
    )


class AuditMixin:
    """
    감사(Audit) 정보 Mixin 클래스
    생성자, 수정자 정보를 포함합니다.

    사용 예시:
        class User(Base, AuditMixin):
            ...
    """
    # crt_user_id: Optional[str]  # 타입 힌팅 제거
    crt_user_id = Column(
        "crt_user_id",
        String(40),
        nullable=True,
        comment="생성자 ID"
    )
    # mdfy_user_id: Optional[str]  # 타입 힌팅 제거
    mdfy_user_id = Column(
        "mdfy_user_id",
        String(40),
        nullable=True,
        comment="수정자 ID"
    )

    # tid: Optional[str]  # 타입 힌팅 제거
    tid = Column(
        "tid",
        String(100),
        nullable=True,
        comment="트랜잭션 ID"
    )


class UseMixin:
    """
    사용 상태 Mixin 클래스
    UseStatus Enum을 사용합니다.

    사용 예시:
        class User(Base, UseMixin):
            ...
        # 사용
        user.use_stat_cd = UseStatus.USABLE
    """
    # use_stat_cd: Optional[UseStatus]  # 타입 힌팅 제거
    use_stat_cd = Column(
        SqlEnum(UseStatEnum, native_enum=False, length=40),
        nullable=True,
        default=UseStatEnum.USABLE,
        comment="사용 상태 코드"
    )


class RecordNoteMixin:
    """레코드 노트 Mixin 클래스"""
    # rsn_cd: Optional[str]  # 타입 힌팅 제거
    rsn_cd = Column(
        "rsn_cd",
        String(100),
        nullable=True,
        comment="사유 코드"
    )

    # trns_cm: Optional[str]  # 타입 힌팅 제거
    trns_cm = Column(
        "trns_cm",
        String(100),
        nullable=True,
        comment="변환 코드"
    )


class TimestampMixin:
    """
    생성일시, 수정일시 Mixin 클래스
    Spring Boot의 @CreatedDate, @LastModifiedDate와 유사

    사용 예시:
        class User(Base, TimestampMixin):
            ...
    """
    # crt_dt: datetime  # 타입 힌팅 제거
    crt_dt = Column(
        DateTime,
        default=func.current_timestamp(),
        nullable=True,
        comment="생성일시"
    )
    # mdfy_dt: datetime  # 타입 힌팅 제거
    mdfy_dt = Column(
        DateTime,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=True,
        comment="수정일시"
    )
