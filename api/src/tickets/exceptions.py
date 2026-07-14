from fastapi import HTTPException, status


class TicketNotFound(HTTPException):
    def __init__(self):
        super().__init__(status.HTTP_404_NOT_FOUND, "ticket_not_found")
