from fastapi import HTTPException, status

from src.auth.constants import ErrorCode


class InvalidCredentials(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_401_UNAUTHORIZED, ErrorCode.INVALID_CREDENTIALS)

class InvalidToken(HTTPException):
    def __init__(self):
        super().__init__(
            status.HTTP_401_UNAUTHORIZED,
            ErrorCode.INVALID_TOKEN,
            headers={"WWW-Authenticate": "Bearer"},
        )

class UsernameTaken(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_409_CONFLICT, ErrorCode.USERNAME_TAKEN)

class InactiveUser(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_403_FORBIDDEN, ErrorCode.INACTIVE_USER)

class TokenExpired(HTTPException):
    def __init__(self):
        super().__init__(
            status.HTTP_401_UNAUTHORIZED,
            ErrorCode.TOKEN_EXPIRED,
            headers={"WWW-Authenticate": "Bearer"},
        )