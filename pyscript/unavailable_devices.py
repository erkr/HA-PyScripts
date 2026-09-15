ignore_devices = [
     # Add ids of devices to be ignored here. 
     # The template {{ device_id('entity id') }}  can be used to find device id's
     ]
 
ignore_entities = [
     ]

extend_integrations = [
     # Add integrations whose entities are added to devices but can remain available
     "powercalc", "template"]

expected_devices = [
     # devices that expected to be unavailable (eg smart devices that were switched physically)       
     ]

CHECKER_ID = "pyscript.unavailable_devices"
# the real limit for detailed reporting is ca 100 devices, as the max Attribute size is 16Kb
CONST_MAX_DEVICES = 30 # report a summary of devives per integrations when max is exceeded
 
from homeassistant.helpers import entity_registry as erm
from homeassistant.helpers import device_registry as drm

from homeassistant.const import STATE_UNAVAILABLE
import json

     
@service(supports_response="only")
def device_availability_check_configured_lists():
     """yaml
description: Verify device_availability_checker configured lists
"""
     dr = drm.async_get(hass)
     ids = []
     for d in dr.devices:
        ids = ids + [d.id]
     extend_integrations_issues = []
     integrations = list(hass.config.all_components)
     for i in extend_integrations:
         if i not in integrations:
             extend_integrations_issues = extend_integrations_issues + [i]
     ignore_devices_issues = []
     for id in ignore_devices:
         if id not in ids:
             ignore_devices_issues = ignore_devices_issues + [id]
     expected_devices_issues = []
     for id in expected_devices:
         if id not in ids:
             expected_devices_issues = expected_devices_issues + [id]
     ignore_entities_issues = []
     for e in ignore_entities:
         if not state.exist(e):
             ignore_entities_issues = ignore_entities_issues + [e]
     return {"extend_integrations_issues": extend_integrations_issues if len(extend_integrations_issues) else "ok",
            "ignore_devices_issues": ignore_devices_issues if len(ignore_devices_issues) else "ok",
             "expected_devices_issues": expected_devices_issues if len(expected_devices_issues) else "ok",
             "ignore_entities_issues": ignore_entities_issues if len(ignore_entities_issues) else "ok"
     }



@service(supports_response="only")
def device_availability_test(device_id: str):
     """yaml
description: Test the device_availability_checker result for a specific device
fields:
     device_id:
         description: device id to be tested
         required: true
         default: ''
         example: 2e6ec7645070322e572e1e161306c2f7
         selector:
             device:
             multiple: false
"""
     if device_id in ignore_devices:
         return {"result": "ignored device" }
         
     er = erm.async_get(hass)
     dr = drm.async_get(hass)

     device_info = {"error": "not found"}
     for d in dr.devices:
         if (d.id == device_id):
             name = d.name if d.name_by_user is None else d.name_by_user
             manufacturer = d.manufacturer
             model = d.model
             area = d.area_id or ""
             integration="unknown"
             entry = hass.config_entries.async_get_entry(entry_id=d.primary_config_entry)
             if entry is not None: 
                 integration = entry.domain 
             device_info = {
                 "integration": integration,
                 "area": area,
                 "name": name,
                 "manufacturer": manufacturer,
                 "model": model,
             }
             break
     

     result=[]
     for e in erm.async_entries_for_device(er, device_id):
         useForCheck = "Yes"
         if (   # check if entity should be ignored 
                (e.original_device_class == "connectivity") or
                (e.platform in extend_integrations) or
                (e.entity_id in ignore_entities)
            ):
             useForCheck = "Ignored"
         #log.warning(f"avaliablity test entity {e.entity_id}")
         result.append( {"entity": e.entity_id, "part_of_check": useForCheck, "available": "No" if hass.states.is_state(e.entity_id, STATE_UNAVAILABLE) else "Yes", "platform":e.platform,  "device_class": e.original_device_class} )
         
     return {"device": device_info, "result": result }
 
#@time_trigger('cron(*/5 * * * *)')
@time_trigger('cron(* * * * *)')
@time_trigger('startup')
def device_availability_checker(doNotify=False):
     er = erm.async_get(hass)
     dr = drm.async_get(hass)

     unavailable_devices = {}
     unavailable_since = {}
     integrations_involved={} #  number of unavailable devices for integrations involved
     integrations_expected={}  # are all missing devices of hte integration expected
     devices_per_integration={} # total number of devices owned
     
     # Iterate over all devices and check whether they are unavailable
     # A device is supposed to be unavailable if all related entities are in
     # state "unavailable". Except some added entities by other integrations, and connectivity types
     for d in dr.devices:
         if d.id in ignore_devices or d.disabled_by:
             continue
         
         # update some stats in case we provide a summary
         integration="unknown"
         entry = hass.config_entries.async_get_entry(entry_id=d.primary_config_entry)
         if entry is not None: 
             integration = entry.domain 
         devices_per_integration[integration] = devices_per_integration.get(integration, 0) + 1

         # check device availability
         unavailable = False
         since = None
         for e in erm.async_entries_for_device(er, d.id):

             if ( # check if entity should be ignored
                  (e.original_device_class == "connectivity") or
                  (e.platform in extend_integrations) or
                  (e.entity_id in ignore_entities)
                ):
                 continue
             elif hass.states.is_state(e.entity_id, STATE_UNAVAILABLE):
                 unavailable  = True
                 since = hass.states.get(e.entity_id).last_changed
             else:
                 unavailable = False
                 break
         if unavailable:
             unavailable_devices[d.id] = dr.async_get(d.id)
             unavailable_since[d.id] = since

     notifs = []
     devices = {}
     expected = 0
     icon_color='gray'
         
     # Iterate over all unavailable devices and construct notification text
     # for a persistent_notification
     for k, d in unavailable_devices.items():
         name = d.name if d.name_by_user is None else d.name_by_user
         manufacturer = d.manufacturer
         model = d.model
         area = d.area_id or ""
         integration="unknown"
         entry = hass.config_entries.async_get_entry(entry_id=d.primary_config_entry)
         if entry is not None: 
             integration = entry.domain 

         if doNotify:
             text = f'- {name}'
             desc = ""
             if model is not None:
                 desc += model
             if manufacturer is not None:
                 if desc != "":
                     desc += f" [{manufacturer}]"
                 else:
                     desc += manufacturer
             if desc != "":
                 text += "\n    - " + desc
             if area is not None:
                 text += f"\n    - Area: {area}"
             text += f"\n    - Integration: {integration}"
             text += f"\n    - Since: {unavailable_since[k]}"
             text += f"\n    - ID: {d.id}"
             notifs.append(text)
         to_be_expected = bool(k in expected_devices) 
         devices[k] = {
             "integration": integration,
             "area": area,
             "name": name,
             "manufacturer": manufacturer,
             "model": model,
             "since": unavailable_since[k],
             "expected": to_be_expected
         }
         if to_be_expected:
             expected+=1
             
         # track #devices on integration level
         integrations_involved[integration] = integrations_involved.get(integration, 0) + 1
         integrations_expected[integration] = integrations_expected.get(integration,True) if to_be_expected else False

     total = len(devices)
     
     if doNotify:       
         # Show a persistent notification or dismiss an old one if there is nothing
         # to show
         ntext = "\n".join(notifs)
         if ntext != "":
             hass.services.async_call("persistent_notification", "create", {
                 "notification_id": "device_availability_warning",
                 "title": f"List of {total} Unavailable Devices",
                 "message": ntext
             }, False)
         else:
             hass.services.async_call("persistent_notification", "dismiss", {
                 "notification_id": "device_availability_warning"
             }, False)

     if total > expected: 
         icon_color='red'
         icon='mdi:power-plug-off-outline'
     elif expected > 0:
         icon_color='orange'
         icon='mdi:power-plug-off-outline'
     else:
         icon_color='green'
         icon='mdi:power-plug-outline'
         
     # prevent huge lists at startup
     summary = False
     if total > CONST_MAX_DEVICES:
         summary=True
         devices={}
         for k,v in integrations_involved.items():
            devices[k] = {"tot": devices_per_integration.get(k, 0), "uav": v, "exp": integrations_expected.get(k, False) }
         
     state.set(CHECKER_ID, total, devices=devices, expected=expected, icon_color=icon_color, icon=icon, summary=summary, state_class='total')


# Helper action to lookup the names of all available integrations
@service(supports_response="only")
def get_integrations():
    """Get all integrations."""
    return {"integrations": list(hass.config.all_components)}

