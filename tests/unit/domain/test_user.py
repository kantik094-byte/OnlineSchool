import pytest

from app.domain.entities.user import UserRole
from app.domain.exceptions import InvalidUserError


def test_user_is_created_with_valid_data(users) -> None:
    user = users.get_student()

    assert user.email == 'student@example.com'
    assert user.role is UserRole.STUDENT


def test_user_raises_error_when_email_is_invalid(users) -> None:
    with pytest.raises(InvalidUserError):
        users.get_student(email='invalid-email')


def test_user_raises_error_when_hashed_password_is_blank(users) -> None:
    with pytest.raises(InvalidUserError):
        users.get_student(hashed_password='    ')


def test_admin_user_can_manage_platform(users) -> None:
    user = users.get_admin()

    assert user.is_admin() is True
    assert user.can_manage_platform() is True
    assert user.can_manage_content() is True


def test_student_can_take_learning_activities_but_cannot_manage_platform(users) -> None:
    user = users.get_student()

    assert user.can_take_learning_activities() is True
    assert user.can_manage_platform() is False