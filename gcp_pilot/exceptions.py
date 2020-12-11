class UnsupportedFormatException(Exception):
    pass


class ValidationError(Exception):
    pass


class UnboundException(Exception):
    pass


class NotFoundError(Exception):
    pass


class BigQueryJobError(Exception):
    def __init__(self, job):
        message = ' | '.join([error['message'] for error in job.errors])
        super().__init__(message)


class AlreadyExistsError(Exception):
    pass
