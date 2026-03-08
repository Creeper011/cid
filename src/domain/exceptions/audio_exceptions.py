
class SessionAlreadyActiveException(Exception):
    """Raised when trying to start a new audio session while one is already active in the guild"""
    pass