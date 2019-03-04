import requests
import json
import base64
import re

from typing import List, Dict

import alfresco_client_nodes

class Error(Exception):
   pass

class RequestFailed(Error):
   def __init__(self, statusCode:int, message:str=None):
      self.statusCode = statusCode
      self.message = message
   
   def __str__(self):
      myStr = str(self.statusCode)
      if self.message != None:
         myStr = myStr + ' ' + self.message
      return myStr

class UnhandledStatus(Error):
   def __init__(self, statusCode:int):
      self.statusCode = statusCode

class Client:
   def __init__(self, baseUrl:str):
      self.baseUrl = baseUrl

   def login(self, userName:str, password:str):
      entity = self.post('authentication', 'tickets', None, json.dumps({'userId': userName, 'password' : password}))
      return entity['id']
   
   def get(self, api:str, opUrl:str, ticket:str, params:Dict=None, headers:Dict=None, responseDataHandler=None, specialStatusHandler=None):
      url = self.baseUrl + '/api/-default-/public/' + api + '/versions/1/' + opUrl
      effParams = {}
      effHeaders = {}
      
      if params != None:
         for k in params:
            effParams[k] = params[k]
      
      if headers != None:
         for k in headers:
            effHeaders[k] = headers[k]
      
      if ticket != None:
         effHeaders['Authorization'] = 'BASIC ' + base64.b64encode(bytes(ticket, 'utf-8')).decode('utf-8')

      res = requests.get(url, headers=effHeaders, params=effParams)

      if res.status_code >= 400:
         if re.search('^application/json(;charset=.+)?$', res.headers['Content-type']):
            jsonRes = res.json()
            if 'briefSummary' in jsonRes:
               raise RequestFailed(res.status_code, message=jsonRes['briefSummary'])
         raise RequestFailed(res.status_code, message=res.text)
      
      if res.status_code >= 200 and res.status_code < 300:
         if responseDataHandler != None:
            return responseDataHandler(res)
         if re.search('^application/json(;charset=.+)?$', res.headers['Content-type']):
            jsonRes = res.json()
            if 'entry' in jsonRes:
               return jsonRes['entry']
            return jsonRes
         if re.search('^text/.+(;charset=.+)?$', res.headers['Content-type']):
            return res.text
         return res.content
      if specialStatusHandler != None:
         specialStatusHandler(res)
      else:
         raise UnhandledStatus(res.status_code)
   
   def post(self, api:str, opUrl:str, ticket:str, data:Dict, params:Dict=None, headers:Dict=None, responseDataHandler=None, specialStatusHandler=None):
      url = self.baseUrl + '/api/-default-/public/' + api + '/versions/1/' + opUrl
      effParams = {}
      effHeaders = {}
      
      if params != None:
         for k in params:
            effParams[k] = params[k]
      
      if headers != None:
         for k in headers:
            effHeaders[k] = headers[k]
      
      if ticket != None:
         effHeaders['Authorization'] = 'BASIC ' + base64.b64encode(bytes(ticket, 'utf-8')).decode('utf-8')

      res = requests.post(url, data=data, headers=effHeaders, params=effParams)

      if res.status_code >= 400:
         if re.search('^application/json(;charset=.+)?$', res.headers['Content-type']):
            jsonRes = res.json()
            if 'briefSummary' in jsonRes:
               raise RequestFailed(res.status_code, message=jsonRes['briefSummary'])
         raise RequestFailed(res.status_code, message=res.text)
      
      if res.status_code >= 200 and res.status_code < 300:
         if responseDataHandler != None:
            return responseDataHandler(res)
         if re.search('^application/json(;charset=.+)?$', res.headers['Content-type']):
            jsonRes = res.json()
            if 'entry' in jsonRes:
               return jsonRes['entry']
            return jsonRes
         if re.search('^text/.+(;charset=.+)?$', res.headers['Content-type']):
            return res.text
         return res.content
      if specialStatusHandler != None:
         specialStatusHandler(res)
      else:
         raise UnhandledStatus(res.status_code)

class Connection:
   def __init__(self, client:Client):
      self.client = client
   
   def connect(self, userName:str, password:str):
      self.ticket = self.client.login(userName, password)
   
   def nodesAPI(self):
      return alfresco_client_nodes.NodesAPI(self)

def connect(baseUrl:str, userName:str, password:str):
   client = Client(baseUrl)
   connection = Connection(client)
   connection.connect(userName, password)
   return connection