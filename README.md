# About

This project is an experimental, work-in-progress Python client library for accessing Alfresco Content Services via its v1 Public ReST API. This project mostly evolves based on the needs I or my customers may have in our projects, or as interested community members contribute pull requests.

## Import / Dependencies

As I am fairly new to Python development in general, this project may not follow any of the standard packaging / distribution patterns common in the Python ecosystem / community. Currently, the easiest way to include this library in a project would be to clone it into a directory '_alfpyclient_' located in one of the Python lookup paths.

```text
git clone git@github.com:Acosix/alfresco-python-client.git alfpyclient
```

This project uses the following dependencies in addition to standard / built-in APIs:

- [https://2.python-requests.org](requests)

## Usage / API

### Connecting

A client connection can be established in the following ways

```python
from alfpyclient.common.connections import connect

# authenticate using password
client = connect('<serverAddress>/alfresco', 'admin', 'admin')
# alternatively using named parameters
client = connect('<serverAddress>/alfresco', userName='admin', password='admin')

# authenticate using a pre-established authentication ticket
client = connect('<serverAddress>/alfresco', ticket='<ticketId>')
```

### Errors

Errors in the execution of a ReST request as indicated by the HTTP status code of the server response will be raised as exceptions defined in the _alfpyclient.common.errors_ package, unless already handled by API services / object representations of this project to accommodate sensible operation flows. The following exception types are currently defined:

- RequestError (generic)
- BadRequest
- Unauthorized
- Forbidden
- NotFound
- Conflict
- InternalServerError

Each exception instance will define the instance members _statusCode_ and _message_, providing as much detail as provided in the server response by Alfresco.

### Working with Sites

```python
from alfpyclient.api.sites import SitesAPI

sitesApi = SitesAPI(client)

# retrieve a named site
mySite = sitesApi.getSite('<shortname>')

# retrieve a named site with optional parameters restricting loaded data to specified fields
# the field 'id' will always be forced to load internally, even if not specified
mySite = sitesApi.getSite('<shortname>', fields=['title', 'description'])

# accessing high-level properties (if not loaded due to restricted fields, site will be re-loaded with requested field added in fields restriction list)
print(mySite.id)
print(mySite.guid)
print(mySite.title)
print(mySite.description)
print(mySite.visibility)
print(mySite.preset)
print(mySite.role)

# access the node representing the site
siteNode = mySite.getSiteNode()

# access special container nodes
doclib = mySite.getDocumentLibrary()
calendar = mySite.getCalendar()
links = mySite.getLinks()
```

### Working with Nodes

```python
# optional import + lookup (unless reference to node already retrieved via other APIs, e.g. SitesAPI)
from alfpyclient.api.nodes import NodesAPI

nodesApi = NodesAPI(client)
companyHome = nodesAPI.getCompanyHome()
sharedFiles = nodesAPI.getSharedFiles()
myFiles = nodesAPI.getMyFiles()

# simple ID based lookup
anyNode = nodesAPI.getNode('<id>')

# extended, parameterised lookup
# the field 'id' will always be forced to load internally, even if not specified in fields list
anyNode = nodesAPI.getNode('<id>', relativePath='path/to/target', fields=['name', 'nodeType', 'path'], path=True)
# full named parameter list: relativePath:str, fields:List[str], allowableOperations:bool, permissions:bool, path:bool, isLink:bool, isFavorite:bool, isLocked:bool

# accessing high-level properties (if not loaded due to restricted fields, site will be re-loaded with requested field added in fields restriction list, potentially also adding flags to explicitly request additional data, e.g. such as path / permissions)
# any sub-structures (except for properties) will be regular Dict / List instances
# full details on the structure of a node can be obtained from the documentation at https://api-explorer.alfresco.com/api-explorer/#!/nodes/getNode
print(anyNode.id)
print(anyNode.name)
print(anyNode.nodeType)
print(anyNode.isFolder)
print(anyNode.isFile)
print(anyNode.modifiedByUser['displayName'])
print(anyNode.content['mimeType'])

# accessing properties / simple metadata
# properties is a slightly enhanced Dict instance
print(anyNode.properties['cm:title'])
# properties supports fallback with automatic addition of cm: prefix
print(anyNode.properties['title'])

# as any Dict, properties can be iterated (fallback names without prefix will not be included)
for propertyName in anyNode.properties:
    print(propertyName + ': ' + properties[propertyName])


# accessing associations
# targetAssociations are pointing from the node to other nodes
# sourceAssociations are pointing from other nodes to the node
# both structures are slightly enhanced Dict instances which lazily load entries as requested, so they cannot be iterated over to access all existing associations
originals = anyNode.targetAssociations['cm:original']
if len(originals) == 1:
    print('Node was created as a copy of ' + originals[0].id

# source + targetAssociations support fallback with automatic addition of cm: prefix
originals = anyNode.targetAssociations['original']


# resolving a descendant node by path
descendant = anyNode.resolveChildPath('path/to/node')


# accessing children
# like regular associations, childAssociations is a slightly enhanced Dict instance which lazily loads entries
# this type of access will always only list the first 100 children for a specific type of child association
# fallback with automatic addition of cm: prefix is supported
# example: load regular file / folder contents of a folder via cm:contains
folderContents = folderNode.childAssociations['cm:contains']
for node in folderContents:
    print(node.name)


# download content of node into provided file
with open('path/to/' + anyNode.name, 'wb') as f:
    anyNode.downloadContent(f)