import urllib
from typing import List

class Node:
   def __init__(self, api, nodeId:str, nodeData=None, loadParameters=None):
      self.api = api
      self.nodeId = nodeId
      self.nodeData = nodeData
      self.loadParameters = loadParameters
   
   def reload(self):
      if self.loadParameters != None:
         self.nodeData = self.api.loadNodeData(self.nodeId, fields=self.loadParameters[0], loadAllowableOperations=self.loadParameters[1], loadPermissions=self.loadParameters[2], loadAssociations=self.loadParameters[3], loadPath=self.loadParameters[4], loadIsLink=self.loadParameters[5], loadIsFavorite=self.loadParameters[6], loadIsLocked=self.loadParameters[7])
      else:
         self.nodeData = self.api.loadNodeData(self.nodeId)
   
class InternalNodesAPI:
   def __init__(self, connection):
      self.connection = connection
   
   def loadNodeData(self, nodeId:str, relativePath:str=None, fields:List[str]=None, loadAllowableOperations:bool=False, loadPermissions:bool=False, loadAssociations:bool=False, loadPath:bool=False, loadIsLink:bool=False, loadIsFavorite:bool=False, loadIsLocked:bool=False):
      opUrl = 'nodes/' + urllib.parse.quote_plus(nodeId)
      paramInclude = []
      if loadAllowableOperations:
         paramInclude.append('allowableOperations')
      if loadPermissions:
         paramInclude.append('permissions')
      if loadAssociations:
         paramInclude.append('associations')
      if loadPath:
         paramInclude.append('path')
      if loadIsLink:
         paramInclude.append('isLink')
      if loadIsFavorite:
         paramInclude.append('isFavorite')
      if loadIsLocked:
         paramInclude.append('isLocked')
      
      params = {'include':paramInclude}
      if fields != None:
         params['fields'] = fields
      if relativePath != None:
         params['relativePath'] = relativePath
      nodeData = self.connection.client.get('alfresco', opUrl, self.connection.ticket, params=params)
      return nodeData
   
class NodesAPI:
   def __init__(self, connection):
      self.internalAPI = InternalNodesAPI(connection)
   
   def loadNode(self, nodeId:str, relativePath:str=None, fields:List[str]=None, loadAllowableOperations:bool=False, loadPermissions:bool=False, loadAssociations:bool=False, loadPath:bool=False, loadIsLink:bool=False, loadIsFavorite:bool=False, loadIsLocked:bool=False):
      nodeData = self.internalAPI.loadNodeData(nodeId, relativePath=relativePath, fields=fields, loadAllowableOperations=loadAllowableOperations, loadPermissions=loadPermissions, loadAssociations=loadAssociations, loadPath=loadPath, loadIsLink=loadIsLink, loadIsFavorite=loadIsFavorite, loadIsLocked=loadIsLocked)
      loadParameters = (fields, loadAllowableOperations, loadPermissions, loadAssociations, loadPath, loadIsLink, loadIsFavorite, loadIsLocked)
      node = Node(self.internalAPI, nodeData['id'], nodeData, loadParameters);
      return node