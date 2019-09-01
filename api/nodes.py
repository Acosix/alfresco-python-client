from alfpyclient.common.connections import Client
from typing import Dict, List, Callable, BinaryIO, Any
from urllib.parse import quote
from re import search

_includeFields = ['allowableOperations', 'permissions', 'path', 'isLink', 'isFavorite', 'isLocked']
_nodeFields = _includeFields + ['id', 'name', 'nodeType', 'isFile', 'isFolder', 'modifiedAt', 'modifiedByUser', 'createdAt', 'createdByUser', 'parentId', 'content', 'aspectNames', 'properties']

class _LazyLoaderDict(dict):
    def __init__(self, defaultState:Dict, loader:Callable[[Any], Any]):
        super().__init__(defaultState)
        self.__loader = loader;
        
    def __getitem__(self, key):
        try:
            existing = dict.__getitem__(self, key)
            return existing
        except KeyError:
            lazyVal = self.__loader(key)
            if lazyVal != None:
                dict.__setitem__(self, key, lazyVal)
                return lazyVal
            raise

class Node:
    def __init__(self, api:Any, nodeData:Dict, loadParameters:Dict):
        self.id = nodeData['id']
        self.__api = api
        self.__nodeData = nodeData
        self.__loadParameters = loadParameters
        self.__cachedProperties = None
        self.__cachedTargetAssociations = None
        self.__cachedTargets = None
        self.__cachedSourceAssociations = None
        self.__cachedSources = None
        self.__cachedChildAssociations = None
        self.__cachedChildren = None
    
    def reload(self):
        self.__nodeData = self.__api.loadNodeData(self.id, loadParameters=self.__loadParameters)
        self.__cachedProperties = None
        self.__cachedTargetAssociations = None
        self.__cachedTargets = None
        self.__cachedSourceAssociations = None
        self.__cachedSources = None
        self.__cachedChildAssociations = None
        self.__cachedChildren = None
        
    def resolveChildPath(self, relativePath:str):
        resolvedNode = self.__api.loadNode(self.id, relativePath=relativePath, includes=self.__loadParameters['include'], fields=self.__loadParameters['fields'])
        return resolvedNode
    
    def downloadContent(self, outputFile:BinaryIO):
        self.__api.loadContent(self.id, outputFile)
    
    def __getattr__(self, fieldName:str):
        if fieldName == 'associations' or fieldName == 'targetAssociations':
            if self.__cachedTargets == None:
                self.__cachedTargetAssociations = {}
                self.__cachedTargets = _LazyLoaderDict(self.__cachedTargetAssociations, lambda x: self.__getTargetAssociationFallback(x))
            return self.__cachedTargets
        if fieldName == 'sourceAssociations':
            if self.__cachedSources == None:
                self.__cachedSourceAssociations = {}
                self.__cachedSources = _LazyLoaderDict(self.__cachedSourceAssociations, lambda x: self.__getSourceAssociationFallback(x))
            return self.__cachedTargets
        if fieldName == 'children' or fieldName == 'childAssociations':
            if self.__cachedChildren == None:
                self.__cachedChildAssociations = {}
                self.__cachedChildren = _LazyLoaderDict(self.__cachedChildAssociations, lambda x: self.__getChildAssociationFallback(x))
            return self.__cachedChildren

        if fieldName not in self.__nodeData:
            reloadable = False
            # only non-empty fields list actually restricts the loaded data
            if len(self.__loadParameters['fields']) > 0 and fieldName in _nodeFields and fieldName not in self.__loadParameters['fields']:
                self.__loadParameters['fields'].append(fieldName)
                reloadable = True
                
            if fieldName in _includeFields and fieldName not in self.__loadParameters['include']:
                self.__loadParameters['include'].append(fieldName)
                reoadable = True

            if reloadable:
                print('Reloading node ' + self.id)
                self.reload()

        if fieldName == 'properties':
            if self.__cachedProperties == None:
                self.__cachedProperties = _LazyLoaderDict(self.__nodeData['properties'], lambda x: self.__getPropertyFallback(x))
            return self.__cachedProperties

        return self.__nodeData[fieldName]
    
    def __getPropertyFallback(self, propertyName):
        value = None
        if 'properties' in self.__nodeData and search('^[^:]+$', propertyName):
            try:
                # default fallback for core Alfresco properties
                value = self.__nodeData['properties'][str('cm:' + propertyName)]
            except KeyError:
                pass
        return value
    
    def __getTargetAssociationFallback(self, associationName):
        targets = None
        if search('^[^:]+$', associationName):
            fallbackAssociationName = str('cm:' + associationName)
            # default fallback for core Alfresco associations
            if self.__cachedTargetAssociations == None or fallbackAssociationName not in self.__cachedTargetAssociations:
                loadedTargets = self.__api.loadTargets(self.id, '(assocType=' + fallbackAssociationName + ')', self.__loadParameters)
                if self.__cachedTargetAssociations == None:
                    self.__cachedTargetAssociations = {}
                self.__cachedTargetAssociations[fallbackAssociationName] = loadedTargets[fallbackAssociationName]
            targets = self.__cachedTargetAssociations[fallbackAssociationName]
        else:
            if self.__cachedTargetAssociations == None or associationName not in self.__cachedTargetAssociations:
                loadedTargets = self.__api.loadTargets(self.id, '(assocType=' + associationName + ')', self.__loadParameters)
                if self.__cachedTargetAssociations == None:
                    self.__cachedTargetAssociations = {}
                self.__cachedTargetAssociations[associationName] = loadedTargets[associationName]
            targets = self.__cachedTargetAssociations[associationName]
        return targets
    
    def __getSourceAssociationFallback(self, associationName):
        sources = None
        if search('^[^:]+$', associationName):
            fallbackAssociationName = str('cm:' + associationName)
            # default fallback for core Alfresco associations
            if self.__cachedSourceAssociations == None or fallbackAssociationName not in self.__cachedSourceAssociations:
                loadedSources = self.__api.loadSources(self.id, '(assocType=' + fallbackAssociationName + ')', self.__loadParameters)
                if self.__cachedSourceAssociations == None:
                    self.__cachedSourceAssociations = {}
                self.__cachedSourceAssociations[fallbackAssociationName] = loadedSources[fallbackAssociationName]
            sources = self.__cachedSourceAssociations[fallbackAssociationName]    
        else:
            if self.__cachedSourceAssociations == None or associationName not in self.__cachedSourceAssociations:
                loadedSources = self.__api.loadSources(self.id, '(assocType=' + associationName + ')', self.__loadParameters)
                if self.__cachedSourceAssociations == None:
                    self.__cachedSourceAssociations = {}
                self.__cachedSourceAssociations[associationName] = loadedSources[associationName]
            sources = self.__cachedSourceAssociations[associationName]
        return sources
    
    def __getChildAssociationFallback(self, associationName):
        children = None
        if search('^[^:]+$', associationName):
            fallbackAssociationName = str('cm:' + associationName)
            # default fallback for core Alfresco associations
            if self.__cachedChildAssociations == None or fallbackAssociationName not in self.__cachedChildAssociations:
                loadedChildren = self.__api.loadChildren(self.id, '(assocType=' + fallbackAssociationName + ')', loadParameters=self.__loadParameters)
                if self.__cachedChildAssociations == None:
                    self.__cachedChildAssociations = {}
                self.__cachedChildAssociations[fallbackAssociationName] = loadedChildren[fallbackAssociationName]
            children = self.__cachedChildAssociations[fallbackAssociationName]    
        else:
            if self.__cachedChildAssociations == None or associationName not in self.__cachedChildAssociations:
                loadedChildren = self.__api.loadChildren(self.id, '(assocType=' + associationName + ')', loadParameters=self.__loadParameters)
                if self.__cachedChildAssociations == None:
                    self.__cachedChildAssociations = {}
                self.__cachedChildAssociations[associationName] = loadedChildren[associationName]
            children = self.__cachedChildAssociations[associationName]
        return children

class _InternalNodesAPI:
    def __init__(self, client:Client):
        self.__client = client
        
    def loadNode(self, nodeId:str, relativePath:str=None, includes:List[str]=None, fields:List[str]=None):
        loadParameters = {}

        if includes != None:
            loadParameters['include'] = list(includes)
        else:
            loadParameters['include'] = []

        if fields != None:
            loadParameters['fields'] = list(fields)
            if len(loadParameters['fields']) > 0 and 'id' not in loadParameters['fields']:
                print('Adding id to fields list')
                loadParameters['fields'].append('id')
        else:
            loadParameters['fields'] = []

        nodeData = self.loadNodeData(nodeId, relativePath, loadParameters)
        
        node = Node(self, nodeData, loadParameters)
        return node
    
    def loadNodeData(self, nodeId:str, relativePath:str=None, loadParameters:Dict=None):
        opUrl = 'nodes/' + quote(nodeId)
        
        params = {}
        if loadParameters != None:
            params = dict(loadParameters)

        if relativePath != None:
            params['relativePath'] = relativePath
        
        if 'fields' in params and (params['fields'] == None or len(params['fields']) == 0):
            del params['fields']
        
        nodeData = self.__client.get('alfresco', opUrl, params=params)
        return nodeData
    
    def loadTargets(self, nodeId:str, where:str=None, loadParameters:Dict=None):
        opUrl = 'nodes/' + quote(nodeId) + '/targets'
        
        params = {}
        if loadParameters != None:
            params = dict(loadParameters)
        if where != None:
            params['where'] = where
        
        if 'fields' in params and (params['fields'] == None or len(params['fields']) == 0):
            del params['fields']
        elif 'id' not in params['fields']:
            param['fields'].append('id')

        if 'include' not in params:
            params['include'] = ['association']
        elif 'association' not in params['include']:
            params['include'].append('association')
        
        targetsListResult = self.__client.get('alfresco', opUrl, params=params)
        targetEntries = targetsListResult['list']['entries']
        targetsByAssoc = {}
        
        for targetEntry in targetEntries:
            nodeData = targetEntry['entry']
            loadParametersCopy = {}
            for key in loadParameters:
                if isinstance(loadParameters[key], dict):
                    loadParametersCopy[key] = dict(loadParameters[key])
                if isinstance(loadParameters[key], list):
                    loadParametersCopy[key] = list(loadParameters[key])
                # add other types if we actually use them for loadParameter values
        
            targetNode = Node(self, nodeData, loadParametersCopy)
            assocType = nodeData['association']['assocType']
            del nodeData['association']
            if assocType not in targetsByAssoc:
                targetsByAssoc[assocType] = []
            targetsByAssoc[assocType].append(targetNode)
        
        return targetsByAssoc
    
    def loadSources(self, nodeId:str, where:str=None, loadParameters:Dict=None):
        opUrl = 'nodes/' + quote(nodeId) + '/sources'
        
        params = {}
        if loadParameters != None:
            params = dict(loadParameters)
        if where != None:
            params['where'] = where
        
        if 'fields' in params and (params['fields'] == None or len(params['fields']) == 0):
            del params['fields']
        elif 'id' not in params['fields']:
            param['fields'].append('id')

        if 'include' not in params:
            params['include'] = ['association']
        elif 'association' not in params['include']:
            params['include'].append('association')
        
        sourcesListResult = self.__client.get('alfresco', opUrl, params=params)
        sourceEntries = sourcesListResult['list']['entries']
        sourcesByAssoc = {}
        
        for sourceEntry in sourceEntries:
            nodeData = sourceEntry['entry']
            loadParametersCopy = {}
            for key in loadParameters:
                if isinstance(loadParameters[key], dict):
                    loadParametersCopy[key] = dict(loadParameters[key])
                # add other types if we actually use them for loadParameter values
        
            sourceNode = Node(self, nodeData, loadParametersCopy)
            assocType = nodeData['association']['assocType']
            del nodeData['association']
            if assocType not in sourcesByAssoc:
                sourcesByAssoc[assocType] = []
            sourcesByAssoc[assocType].append(sourceNode)
        
        return sourcesByAssoc
    
    def loadChildren(self, nodeId:str, where:str=None, skipCount:int=0, maxItems:int=100, orderBy:List[str]=None, loadParameters:Dict=None):
        opUrl = 'nodes/' + quote(nodeId) + '/children'
        
        params = {
            'skipCount': skipCount,
            'maxItems': maxItems
        }
        if loadParameters != None:
            params = dict(loadParameters)
        if where != None:
            params['where'] = where
        if orderBy != None:
            params['orderBy'] = orderBy
        
        if 'fields' in params and (params['fields'] == None or len(params['fields']) == 0):
            del params['fields']
        elif 'id' not in params['fields']:
            param['fields'].append('id')

        if 'include' not in params:
            params['include'] = ['association']
        elif 'association' not in params['include']:
            params['include'].append('association')
        
        childrenListResult = self.__client.get('alfresco', opUrl, params=params)
        childEntries = childrenListResult['list']['entries']
        childrenByAssoc = {}
        
        for childEntry in childEntries:
            nodeData = childEntry['entry']
            loadParametersCopy = {}
            for key in loadParameters:
                if isinstance(loadParameters[key], dict):
                    loadParametersCopy[key] = dict(loadParameters[key])
                # add other types if we actually use them for loadParameter values
        
            childNode = Node(self, nodeData, loadParametersCopy)
            assocType = nodeData['association']['assocType']
            del nodeData['association']
            if assocType not in childrenByAssoc:
                childrenByAssoc[assocType] = []
            childrenByAssoc[assocType].append(childNode)
        
        return childrenByAssoc
    
    def loadContent(self, nodeId:str, outputFile:BinaryIO):
        opUrl = 'nodes/' + quote(nodeId) + '/content'
        self.__client.get('alfresco', opUrl, responseHandler=lambda response: outputFile.write(response.content))

class NodesAPI:
    def __init__(self, client:Client):
        self.__client = client

    def getCompanyHome(self):
        return self.getNode('-root-')
    
    def getSharedFiles(self):
        return self.getNode('-shared-')
    
    def getMyFiles(self):
        return self.getNode('-my-')
        
    def getNode(self, id:str, relativePath:str=None, fields:List[str]=None, allowableOperations:bool=False, permissions:bool=False, path:bool=False, isLink:bool=False, isFavorite:bool=False, isLocked:bool=False):
        includes = []
        if allowableOperations:
            includes.append('allowableOperations')
        if permissions:
            includes.append('permissions')
        if path:
            includes.append('path')
        if isLink:
            includes.append('isLink')
        if isFavorite:
            includes.append('isFavorite')
        if isLocked:
            includes.append('isLocked')
    
        api = _InternalNodesAPI(self.__client)
        node = api.loadNode(id, relativePath, includes, fields)
        return node