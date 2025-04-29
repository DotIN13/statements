class TooManyRequestsException(Exception):
    "Raised when the api returns with a 429 too many requests"


class BadResponseException(Exception):
    "Raised when the api returns with a bad response"


class CensoredResponseException(Exception):
    "Raised when the api returns with a censored response"
