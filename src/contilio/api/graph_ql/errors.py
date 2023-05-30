class TrainStationCodesLengthError(Exception):
    """
    Raised when a route queried is lesser than a length of two.
    """

    pass


class DateTimeInThePastError(Exception):
    """
    Raised when the date time on the route queried is in the past.
    """

    pass


class NotThatPatientError(Exception):
    """
    Raised when departure time from source destination is longer than allotted waiting time.
    """

    pass
