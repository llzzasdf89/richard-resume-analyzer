class AppError(Exception):
    def __init__(self, message: str, data: dict | None = None):
        super().__init__(message)
        self.message = message
        self.data = data
