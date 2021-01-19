class UnsupportedFormatException(Exception):
    pass


class ValidationError(Exception):
    pass


class UnboundException(Exception):
    pass


class NotFound(Exception):
    pass


class DeletedRecently(Exception):
    def __init__(self, resource, blocked_period='1 week'):
        message = f"{resource} was probably deleted recently. Cannot reuse name for {blocked_period}."
        super().__init__(message)


class BigQueryJobError(Exception):
    def __init__(self, job):
        message = ' | '.join([error['message'] for error in job.errors])
        super().__init__(message)


class AlreadyExists(Exception):
    pass


class AlreadyDeleted(Exception):
    pass


class NotAllowed(Exception):
    pass
