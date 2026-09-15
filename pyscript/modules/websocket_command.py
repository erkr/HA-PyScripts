# All credits how to use websockets to retrieve the lovelace configuration goes to https://github.com/qui3xote:
# https://github.com/custom-components/pyscript/discussions/272#discussioncomment-1709728

import json
import websockets


#dashboardTitle = "Testboard"

#example command payloads
#listDashboard = {"type": "lovelace/dashboards/list"}
#createDashboard =  {"type": "lovelace/dashboards/create", "title": dashboardTitle, "url_path": dashboardUrl}
#getDashboardConfig = {"type": "lovelace/config", "url_path": dashboardUrl}
#setDashboardConfig = {"type": "lovelace/config/save", "url_path": dashboardUrl, "config": config}
#getPanels = {"type": "get_panels"}
#getConfig = {"type": "get_config"}


#Some usage examples websocket_command:
#create a new dashboard:
#result = websocket_command(createDashboard)
#dashboard_id = result['result']['id'] #need this to be able to delete later
#set the dashboard config:
#result = websocket_command(setDashboardConfig)
#now delete:
#deleteDashboard = {"type": "lovelace/dashboards/delete", "dashboard_id": dashboard_id}
#websocket_command(deleteDashboard)


async def websocket_command(command: dict, url=None, token=None):
    """ returns json result as python data """
    if token==None and 'token' in pyscript.config['global']:
        token = pyscript.config['global']['token']
    if url==None:
        url = 'ws://127.0.0.1:8123/api/websocket'
    # ids are returned in the receive phase so you tie back to originating command. 
    # The API has feelings about these: they must increment, at least per session
    websocket_command.counter += 1
    command['id'] = websocket_command.counter  
    async with websockets.connect(url) as websocket:
        log.info(websocket.recv()) #first receive will give you HA version, if it matters
        await websocket.send(json.dumps({"type": "auth", "access_token": token})) #send auth
        log.info(websocket.recv()) #once ok is received we go into command phase
        await websocket.send(json.dumps(command))
        result = websocket.recv()
        log.info(result)
    return json.loads(result)
websocket_command.counter = 0


