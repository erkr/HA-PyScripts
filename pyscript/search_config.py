# All credits how to use websockets to retrieve the lovelace configuration goes to https://github.com/qui3xote:
# https://github.com/custom-components/pyscript/discussions/272#discussioncomment-1709728
# This example adds a service that looks-up all custom:datetime-card based cards in a particular dashboard
# There it evaluates all entities if they exceed the max time configured in that card and lists them in the response
# MIT license by Eric Kreuwels

import os
import json
import yaml
import datetime
import collections.abc
import fnmatch
from websocket_command import websocket_command
from yaml_loader import yaml_loader



#############%
# YAML Files parser

@service(supports_response="only")
def search_yaml_files(value, root='/config/configuration.yaml',doAppend=False, readableIdx=True, matchSubString=True, ignoreCase=False, return_response=True):
    """yaml
description: Parser for the yaml config files
fields:
    value:
        description: Search phrase in values. Supports wildcards (*? according Unix filename pattern matching)
        example: '!secret*'
        required: true
        default: ''
        selector:
            text:
    readableIdx:
        name: Readable Indices (default True)
        description: try to lookup readible indices instead of numbers 
        example: true
        selector:
            boolean: 
    doAppend:
        name: Append matched values (default False)
        description: Option to append matched values to the paths found
        example: false
        selector:
            boolean: 
    matchSubString:
        name: Match substring (default True)
        description: Option to match the search value as a substring (ignored if wildcards used)
        example: true
        selector:
            boolean: 
    ignoreCase:
        name: Ignore case Option (default False)
        description: Option to compare case insensitive 
        example: false
        selector:
            boolean: 
    root:
        name: Root file to parse (default /config/configuration.yaml)
        example: '/config/configuration.yaml'
        selector:
            text:
"""    
    matches=[]
    # matchSubstring only if no wildcards
    if matchSubString and not ('*' in value or '?' in value):
        value = '*'+value+'*'
        
    success = parse_yaml_file(value, root, matches, doAppend, readableIdx, ignoreCase)
    return {"success":success,"matches":matches}
    
    

def load_yaml(filename):
    """ load yaml file as python data into memory """
    try:
        #with os.fdopen(os.open(filename,os.O_RDONLY)) as f:
        #    data = yaml.load(f, Loader=yaml_loader())
        with os.fdopen(os.open(filename,os.O_RDONLY)) as f:
            data = task.executor(yaml.load, f, Loader=yaml_loader())
        return True, data
    except:
        log.error(f"Can't open file: {filename}")
        return False, None

def parse_yaml_file(value, file, matches, doAppend, readableIdx, ignoreCase):
    """yaml
description: Recursive filecparser. Scans source for all values that match 
arguments:
    value: search string with wildcard support 
    file:  yaml file, includes are parsed recursive 
    matches: output list for the paths of Matches
    doAppend: flag to append the source values
    readableIdx:  flag to try to resolve list indices by readable text
    ignoreCase: flag to compare case insensitive 
"""  

    log.info(f"Parse file: {file}")
    success, data = load_yaml(file)

    # parse for value matches
    name = file.split('/')[-1].split('.')[0]
    includes=[]
    get_values(data, value, matches, name, includes, doAppend, readableIdx, ignoreCase)
    log.info(f"Parse completed: {file}")
    #log.warning(f"includes:{includes}")
    for ifile in includes:
       success = (parse_yaml_file(value, ifile, matches, doAppend, readableIdx, ignoreCase) 
                  and success)
    return success
    


def check_includes(source, includes):
    """yaml
description: returns the file name(s) that are part of an include tag
arguments:
    source:  One of the HA include tags
    includes: the output list for file paths
"""  
    if ('!include ' in source):
        # its a normal !include
        inc = source.split('!include ')
        includes.append('/config/' + inc[1].replace('./',''))
        #log.warning(f"include prefix: {inc[0]}, inc file: {inc[1]}")
        return
    if ('!include_' in source):
        dir_types=['!include_dir_list','!include_dir_named','!include_dir_merge_list','!include_dir_merge_named']
        for t in dir_types:
            if t in source:
                inc = source.split(t + ' ')
                path = '/config/' + inc[1].replace('./','')
                #with os.scandir(path) as it:
                with task.executor(os.scandir,path) as it:
                    for entry in it:
                        if not entry.name.startswith('.') and entry.is_file():
                            includes.append(path + '/' + entry.name)
                return            


###########
# dashboard parser

@service(supports_response="only")
def search_dashboards(value, doAppend=True, readableIdx=True, matchSubString=True, ignoreCase=False, return_response=True):
    """yaml
description: Parser for the UI Dashboard configuration
fields:
    value:
        name: Search Value
        description: Search phrase. Supports wildcards (*?)
        required: true
        example: 'custom:*'
        selector:
            text:
    readableIdx:
        name: Readable Indices
        description: try to lookup readible indices instead of numbers
        example: True
        selector:
            boolean:
    doAppend:
        name: Append matched values (default True)
        description: Option to append matched values to the paths found
        example: true
        selector:
            boolean: 
    matchSubString:
        name: Match substring (default True)
        description: Option to match the search value as a substring (ignored if wildcards used)
        example: true
        selector:
            boolean: 
    ignoreCase:
        name: Ignore case Option
        description: Option to compare case insensitive 
        example: False
        selector:
            boolean:
"""  
    matches=[]
    # matchSubstring only if no wildcards
    if matchSubString and not ('*' in value or '?' in value):
        value = '*'+value+'*'

    success = True
    getDashboardList = {"type": "lovelace/dashboards/list"}
    dashboards = websocket_command(getDashboardList)
    if 'result' in dashboards and dashboards['success']:
        #log.info(f"dashboard list: {dashboards}")
        for dashboard in dashboards['result']:
            log.info(f"Parse dashboard[{dashboard['title']}]") 
            getDashboardConfig = {"type": "lovelace/config", "url_path": dashboard['url_path'] }
            result = websocket_command(getDashboardConfig)
            if 'result' in result and result['success']:
                data = result['result']
                get_values(data, value, matches, dashboard['title'], None, doAppend, readableIdx, ignoreCase)
            else:
                success=False
    else:
        success=False
    return {"success":success,"matches":matches}




#########
# support functions 


# inspired by: https://stackoverflow.com/a/72951525
def get_values(source, value, matches, path, includes=None, doAppend=False, readableIdx=False, ignoreCase=False):
    """yaml
description: Recursive parser. Scans source for all values that match value 
arguments:
    source:  python data input 
    value: search string with wildcard support 
    matches: output list for the paths of Matches
    path:  the root path 
    includes: the output list for included file, skipped is None
    doAppend: flag to append matching source values (can be large)
    readableIdx:  flag to try to resolve list indices by readable text 
"""  

    if isinstance(source, collections.abc.MutableMapping):
        for k, v in source.items():
            newPath = path + '.' + k
            if fnmatch.fnmatchcase(k.lower() if ignoreCase else k, value.lower() if ignoreCase else value):
                matches.append( newPath + ' (key match)' )
            get_values(v, value, matches, newPath, includes, doAppend, readableIdx, ignoreCase)
    elif isinstance(source, collections.abc.Sequence):
        if isinstance(source, str):
            if (includes != None and source and source[0] == '!'):
                check_includes(source, includes)
            if fnmatch.fnmatchcase(source.lower() if ignoreCase else source, value.lower() if ignoreCase else value):
                if doAppend:
                    matches.append( path + '=' + source )
                else:
                    matches.append( path + ' (value match)')
        else:
            for i,x in enumerate(source):
                idx = i
                if readableIdx and isinstance(x,collections.abc.MutableMapping):
                    for tag in ['alias','unique_id','name','title']:
                        if tag in x:
                            idx = x[tag]
                            break;
                newPath = path + '.[' + str(idx) + ']'
                get_values(x, value, matches, newPath, includes, doAppend, readableIdx, ignoreCase)
    return 


# source: https://stackoverflow.com/a/72951525
def get_paths(source):
    paths = []
    if isinstance(source, collections.abc.MutableMapping):
        for k, v in source.items():
            if k not in paths:
                paths.append(k)
            for x in get_paths(v):
                if k + '.' + x not in paths:
                    paths.append(k + '.' + x)
    elif isinstance(source, collections.abc.Sequence) and not isinstance(source, str):
        for x in source:
            for y in get_paths(x):
                if '[].' + y not in paths:
                    paths.append('[].' + y)
    return paths

#@service(supports_response="only")
#def explore_data():
#    paths = []
#    data = []
#    paths = get_paths(data)
#    return {"matches":paths}    


