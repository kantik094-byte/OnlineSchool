from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, status

from app.application.use_cases.auth.get_current_user import GetCurrentUserUseCase
from app.application.use_cases.auth.login_user import LoginUserCommand, LoginUserUseCase
from app.application.use_cases.auth.register_user import (
    RegisterUserCommand,
    RegisterUserUseCase,
)
from app.presentation.api.schemas import (
    CurrentUserResponse,
    ErrorResponse,
    LoginRequest,
    RegisteredUserResponse,
    RegisterUserRequest,
    TokenResponse,
)
from app.presentation.api.security import AUTH_REQUIRED, AUTH_RESPONSES

router = APIRouter(prefix='/auth', tags=['Auth'], route_class=DishkaRoute)


@router.post('/register', response_model=RegisteredUserResponse, status_code=status.HTTP_201_CREATED,
             summary='Register new user',
             description=(
                     'Creates a new user account in the system. '
                     'A public registration always creates a user with the student role.'
             ),
             responses={
                 400: {
                     'description': 'Domain or application validation error.',
                     'model': ErrorResponse,
                 },
             },
             )
async def register_user(request: RegisterUserRequest, use_case: FromDishka[RegisterUserUseCase]) -> RegisteredUserResponse:
    result = await use_case.execute(
        RegisterUserCommand(
            email=request.email,
            password=request.password,
        )
    )
    return RegisteredUserResponse.model_validate(result)


@router.post('/login', response_model=TokenResponse,
             summary='Login user',
             description=(
                     'Authenticates a user by email and password and returns a JWT access token.'
             ),
             responses={
                 400: {
                     'description': 'Invalid email or password.',
                     'model': ErrorResponse,
                 },
             },
             )
async def login_user(request: LoginRequest, use_case: FromDishka[LoginUserUseCase]) -> TokenResponse:
    result = await use_case.execute(
        LoginUserCommand(
            email=request.email,
            password=request.password,
        )
    )
    return TokenResponse(
        access_token=result.access_token,
        token_type=result.token_type,
    )

@router.get('/me', response_model=CurrentUserResponse,
            summary='Get current user',
            description='Returns the currently authenticated user resolved from Bearer token.',
            dependencies=AUTH_REQUIRED,
            responses=AUTH_RESPONSES,
            )
async def get_me(use_case: FromDishka[GetCurrentUserUseCase]) -> CurrentUserResponse:
    user = await use_case.execute()
    return CurrentUserResponse.model_validate(user)
