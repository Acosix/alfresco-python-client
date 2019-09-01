from alfpyclient.common.connections import Client
from alfpyclient.api.nodes import NodesAPI
from typing import Dict, List, Any
from urllib.parse import quote

_relationFields = ['containers', 'members']
_siteFields = _relationFields + ['id', 'guid', 'title', 'description', 'visibility', 'preset', 'role']

class Site:
    def __init__(self, api:Any, siteData:Dict, loadParameters:Dict):
        self.id = siteData['id']
        self.__api = api
        self.__siteData = siteData
        self.__loadParameters = loadParameters
        self.__cachedNode = None
        
    def reload(self):
        self.__siteData = self.__api.loadSiteData(self.id, fields=self.__loadParameters['fields'],includes=self.__loadParameters['include'])
        
    def __getattr__(self, fieldName:str):
        if fieldName not in self.__siteData:
            reloadable = False
            # only non-empty fields list actually restricts the loaded data
            if self.__loadParameters['fields'] != None and len(self.__loadParameters['fields']) > 0 and fieldName in _siteFields and fieldName not in self.__loadParameters['fields']:
                self.__loadParameters['fields'].append(fieldName)
                reloadable = True
                
            if fieldName in _relationFields and fieldName not in self.__loadParameters['relations']:
                self.__loadParameters['include'].append(fieldName)
                reoadable = True

            if reloadable:
                self.reload()

        return self.__siteData[fieldName]
    
    def getSiteNode(self):
        if self.__cachedNode == None:
            self.__cachedNode = self.__api.loadSiteNode(self.__siteData.guid)
        return self.__cachedNode
    
    def getDocumentLibrary(self):
        documentLibraryNode = self.__api.loadSiteContainerNode(self.id, 'documentLibrary')
        return documentLibraryNode
    
    def getCalendar(self):
        calendarNode = self.__api.loadSiteContainerNode(self.id, 'calendar')
        return calendarNode
    
    def getLinks(self):
        linksContainerNode = self.__api.loadSiteContainerNode(self.id, 'links')
        return linksContainerNode
    
    # TODO Other common containers

class _InternalSitesAPI:
    def __init__(self, client:Client):
        self.__client = client
    
    def loadSite(self, siteId:str, relations:List[str]=None, fields:List[str]=None):
        loadParameters = {'relations': []}
        
        if relations != None:
            loadParameters['relations'] = list(relations)
        
        if fields != None:
            loadParameters['fields'] = list(fields)
            if 'id' not in loadParameters['fields']:
                loadParameters['fields'].append('id')
            if 'guid' not in loadParameters['fields']:
                loadParameters['fields'].append('guid')
        
        siteData = self.loadSiteData(siteId, loadParameters)
        site = Site(self, siteData, loadParameters)
        return site
    
    def loadSiteData(self, siteId:str, loadParameters:Dict=None):
        opUrl = 'sites/' + quote(siteId)

        params = {}
        if loadParameters != None:
            params = dict(loadParameters)

        if 'fields' in params and (params['fields'] == None or len(params['fields']) == 0):
            del params['fields']

        # TODO deal with relations, which currently is filtered out by the 'entry' default handling in get()
        siteData = self.__client.get('alfresco', opUrl, params=params)
        return siteData
    
    def loadSiteNode(self, siteGuid:str):
        nodesApi = NodesAPI(self.__client)
        siteNode = nodesApi.getNode(guid)
        return siteNode
    
    def loadSiteContainerNode(self, siteId:str, containerId:str):
        opUrl = 'sites/' + quote(siteId) + '/containers/' + quote(containerId)
        siteContainerData = self.__client.get('alfresco', opUrl)
        nodesApi = NodesAPI(self.__client)
        siteContainerNode = nodesApi.getNode(siteContainerData['id'])
        return siteContainerNode

class SitesAPI:
    def __init__(self, client:Client):
        self.__client = client
    
    def getSite(self, siteId:str, relations:List[str]=None, fields:List[str]=None):
        api = _InternalSitesAPI(self.__client)
        site = api.loadSite(siteId, relations, fields)
        return site