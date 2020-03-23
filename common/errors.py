from requests import Response
import re


class RequestError(Exception):
    def __init__(self, response: Response):
        self.statusCode = response.status_code
        self.message = _extractResponseMessage(response)

    def __str__(self):
        errorStr = 'HTTP ' + str(self.statusCode)
        if self.message is not None:
            errorStr = errorStr + ' ' + self.message
        return errorStr

# classes only for the common errors in Alfresco Public ReST API


class BadRequest(RequestError):
    def __init__(self, response: Response):
        super().__init__(response)


class Unauthorized(RequestError):
    def __init__(self, response: Response):
        super().__init__(response)


class Forbidden(RequestError):
    def __init__(self, response: Response):
        super().__init__(response)


class NotFound(RequestError):
    def __init__(self, response: Response):
        super().__init__(response)


class Conflict(RequestError):
    def __init__(self, response: Response):
        super().__init__(response)


class InternalServerError(RequestError):
    def __init__(self, response: Response):
        super().__init__(response)


class ServiceUnavailable(RequestError):
    def __init__(self, response: Response):
        super().__init__(response)


_errorSwitcher = {
    400: BadRequest,
    401: Unauthorized,
    403: Forbidden,
    404: NotFound,
    409: Conflict,
    500: InternalServerError,
    503: ServiceUnavailable
}


def _extractResponseMessage(response: Response):
    if re.search('^application/json(;charset=.+)?$', response.headers['Content-type']):
        jsonResponse = response.json()
        if 'error' in jsonResponse and 'briefSummary' in jsonResponse['error']:
            return jsonResponse['error']['briefSummary']
    return response.text


def handleErrorResponse(response: Response):
    errorCls = _errorSwitcher.get(response.status_code, RequestError)
    error = errorCls(response)
    return error
