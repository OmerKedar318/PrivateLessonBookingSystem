class BookingError(Exception):
    """Base class for booking related errors"""
    pass


class SlotUnavailableError(BookingError):
    pass


class UserNotFoundError(BookingError):
    pass


class AuthenticationError(BookingError):
    pass


class AuthorizationError(BookingError):
    pass


class InvalidTimeError(BookingError):
    pass


class RegistrationError(BookingError):
    pass
