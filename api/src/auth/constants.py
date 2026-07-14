from enum import StrEnum

class ErrorCode(StrEnum):
    INVALID_CREDENTIALS = "invalid_credentials"
    INACTIVE_USER = "inactive_user"
    INVALID_TOKEN = "invalid_token"
    TOKEN_EXPIRED = "token_expired"
    REFRESH_TOKEN_REUSED = "refresh_token_reused"
    USERNAME_TAKEN = "username_taken"