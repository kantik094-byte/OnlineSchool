class ApplicationError(Exception):
    """Base exception for application-layer errors."""


class CourseNotFoundError(ApplicationError):
    pass


class LectureNotFoundError(ApplicationError):
    pass


class ModuleNotFoundError(ApplicationError):
    pass


class SectionNotFoundError(ApplicationError):
    pass


class UserAlreadyExistsError(ApplicationError):
    pass


class InvalidCredentialsError(ApplicationError):
    pass


class UserNotFoundError(ApplicationError):
    pass

class AuthenticationError(ApplicationError):
    """Нет учётных данных, токен невалиден или пользователь не найден."""


class AccessDeniedError(ApplicationError):
    """Пользователь аутентифицирован, но прав на операцию нет."""


class InvalidTokenError(ApplicationError):
    """Контракт TokenService: токен не удалось проверить."""
