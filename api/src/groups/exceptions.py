from fastapi import HTTPException, status


class GroupNotFound(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_404_NOT_FOUND, "group_not_found")
