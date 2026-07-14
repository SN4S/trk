from fastapi import HTTPException, status


class FolderNotFound(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_404_NOT_FOUND, "folder_not_found")


class GroupAlreadyInFolder(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_409_CONFLICT, "group_already_in_folder")


class GroupNotInFolder(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_404_NOT_FOUND, "group_not_in_folder")
