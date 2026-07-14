from fastapi import HTTPException, status


class ThemeNotFound(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_404_NOT_FOUND, "theme_not_found")
