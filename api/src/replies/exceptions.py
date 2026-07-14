from fastapi import HTTPException, status


class ReplyNotFound(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_404_NOT_FOUND, "reply_not_found")
