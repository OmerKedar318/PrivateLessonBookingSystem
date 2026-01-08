class SessionError(Exception):
    """Base class for booking related errors"""
    pass


class SlotUnavailableError(SessionError):
    pass


class UserNotFoundError(SessionError):
    pass


class AuthenticationError(SessionError):
    pass


class AuthorizationError(SessionError):
    pass


class InvalidTimeError(SessionError):
    pass


class RegistrationError(SessionError):
    pass


class UserAlreadyExistsError(SessionError):
    pass
