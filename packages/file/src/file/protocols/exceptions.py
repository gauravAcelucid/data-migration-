class ConnectorError(Exception):
    def __init__(self, message: str, source: str, retryable: bool = False):
        self.source = source
        self.retryable = retryable
        super().__init__(message)


class RetryableError(ConnectorError):
    def __init__(self, message: str, source: str, retry_after: float = 1.0):
        self.retry_after = retry_after
        super().__init__(message, source, retryable=True)


class FatalError(ConnectorError):
    def __init__(self, message: str, source: str):
        super().__init__(message, source, retryable=False)


class ConfigurationError(FatalError):
    pass


class AuthenticationError(FatalError):
    pass


class ConnectionError(RetryableError):
    pass
