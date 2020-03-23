from alfpyclient.common.errors import handleErrorResponse
from collections import OrderedDict
from base64 import b64encode
from requests import Session, Response
from re import search
from typing import Dict, Callable, Any


class Client:
    def __init__(self, baseUrl: str):
        self.__baseUrl = baseUrl
        self.__ticket = None
        self.__session = None

    def __updateTicket(self, ticket: str = None):
        if ticket is not None:
            self.__ticket = ticket

        if self.__ticket is not None and self.__session is not None:
            basicStr = 'BASIC ' + b64encode(bytes(self.__ticket, 'utf-8')).decode('utf-8')
            self.__session.headers.update({'Authorization': basicStr})

    def __processRequest(self, api: str, opUrl: str, version: str, params: Dict, headers: Dict, responseHandler: Callable[[Response], Any], errorHandler: Callable[[Response], Any], requestHandler: Callable[[str, Dict, Dict, Any], Any], payload: Any = None, files: Dict = None):
        effectiveVersion = '1'
        if version is not None:
            effectiveVersion = version
        effectiveUrl = self.__baseUrl + '/api/-default-/public/' + api + '/versions/' + effectiveVersion + '/' + opUrl

        # OrderedDict to keep any ordering in provided data during mapping
        effectiveParams = OrderedDict()
        effectiveHeaders = OrderedDict()
        effectiveFiles = OrderedDict()

        if params is not None:
            for k in params:
                if isinstance(params[k], list):
                    if len(params[k]) > 0:
                        # Public v1 ReST API always expects concatenated multi-value params
                        effectiveParams[k] = ','.join(params[k])
                else:
                    effectiveParams[k] = params[k]

        if headers is not None:
            for k in headers:
                effectiveHeaders[k] = headers[k]

        if files is not None:
            for k in files:
                effectiveFiles[k] = files[k]

        if self.__session is None:
            self.__session = Session()
            self.__updateTicket()

        with requestHandler(effectiveUrl, effectiveParams, effectiveHeaders, effectiveFiles, payload) as response:
            return self.__processResponse(response, responseHandler, errorHandler)

    def __doGet(self, efUrl: str, efParams: Dict, efHeaders: Dict, payload: Any):
        # ignore payload - should have been part of efParams
        return self.__session.get(efUrl, params=efParams, headers=efHeaders, stream=True)

    def __doPost(self, efUrl: str, efParams: Dict, efHeaders: Dict, payload: Any):
        return self.__session.post(efUrl, data=payload, params=efParams, headers=efHeaders, stream=True)

    def __doJsonPost(self, efUrl: str, efParams: Dict, efHeaders: Dict, payload: Any):
        return self.__session.post(efUrl, json=payload, params=efParams, headers=efHeaders, stream=True)

    def __doMultipartPost(self, efUrl: str, efParams: Dict, efHeaders: Dict, efFiles: Dict, payload: Any):
        return self.__session.post(efUrl, headers=efHeaders, params=efParams, files=efFiles, data=payload)

    def __doPut(self, efUrl: str, efParams: Dict, efHeaders: Dict, payload: Any):
        return self.__session.put(efUrl, data=payload, params=efParams, headers=efHeaders, stream=True)

    def __doJsonPut(self, efUrl: str, efParams: Dict, efHeaders: Dict, payload: Any):
        return self.__session.put(efUrl, json=payload, params=efParams, headers=efHeaders, stream=True)

    def __doDelete(self, efUrl: str, efParams: Dict, efHeaders: Dict, payload: Any):
        # ignore payload - should have been part of efParams
        return self.__session.delete(efUrl, params=efParams, headers=efHeaders, stream=True)

    def __processResponse(self, response: Response, responseHandler: Callable[[Response], Any], errorHandler: Callable[[Response], Any]):
        if response.status_code >= 400 and response.status_code < 600:
            if errorHandler is not None:
                return errorHandler(response)
            error = handleErrorResponse(response)
            raise error
        if response.status_code >= 200 and response.status_code < 300:
            if responseHandler is not None:
                return responseHandler(response)
            if response.status_code != 204:
                if search('^application/json(;charset=.+)?$', response.headers['Content-type']):
                    jsonRes = response.json()
                    if 'entry' in jsonRes:
                        return jsonRes['entry']
                    return jsonRes
                if search('^text/.+(;charset=.+)?$', response.headers['Content-type']):
                    return response.text
                return response.content
        # TODO What to do about 100/300 response status codes? (redirection already handled by requests)
        return None

    def useTicket(self, ticket: str):
        self.__updateTicket(ticket)

    def login(self, userName: str, password: str):
        ticketEntity = self.jsonPost('authentication', 'tickets', payload={'userId': userName, 'password': password})
        self.__updateTicket(ticketEntity['id'])

    def get(self, api: str, opUrl: str, version: str = None, params: Dict = None, headers: Dict = None, responseHandler: Callable[[Response], Any] = None, errorHandler: Callable[[Response], Any] = None):
        return self.__processRequest(api, opUrl, version, params=params, headers=headers, responseHandler=responseHandler, errorHandler=errorHandler, requestHandler=self.__doGet)

    def multipartPost(self, api: str, opUrl: str, payload: Dict, version: str = None, params: Dict = None, headers: Dict = None, files: Dict = None, responseHandler: Callable[[Response], Any] = None, errorHandler: Callable[[Response], Any] = None):
        return self.__processRequest(api, opUrl, version, payload=payload, params=params, headers=headers, files=files, responseHandler=responseHandler, errorHandler=errorHandler, requestHandler=self.__doMultipartPost)

    def jsonPost(self, api: str, opUrl: str, payload: Dict, version: str = None, params: Dict = None, headers: Dict = None, responseHandler: Callable[[Response], Any] = None, errorHandler: Callable[[Response], Any] = None):
        return self.__processRequest(api, opUrl, version, payload=payload, params=params, headers=headers, responseHandler=responseHandler, errorHandler=errorHandler, requestHandler=self.__doJsonPost)

    def jsonPut(self, api: str, opUrl: str, payload: Dict, version: str = None, params: Dict = None, headers: Dict = None, responseHandler: Callable[[Response], Any] = None, errorHandler: Callable[[Response], Any] = None):
        return self.__processRequest(api, opUrl, version, payload=payload, params=params, headers=headers, responseHandler=responseHandler, errorHandler=errorHandler, requestHandler=self.__doJsonPut)


def connect(baseUrl: str, userName: str = None, password: str = None, ticket: str = None):
    client = Client(baseUrl)
    if ticket is not None:
        client.useTicket(ticket)
    elif userName is not None and password is not None:
        client.login(userName, password)
    return client
