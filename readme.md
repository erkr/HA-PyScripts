# Home Assistant Extras – Pyscript Tools and Unavailable Devices

This guide explains how to install and configure a number of useful Python scripts for Home Assistant. The scripts run through the custom **Pyscript** integration and add, among other things, search functions and an extended check for unavailable devices.

After installation, you will have:

- A search function for all YAML files (automatically traverses includes)
- A search function for Home Assistant dashboards
- A `pyscript.unavailable_devices` entity that tracks which devices are unavailable
- Diagnostic actions to troubleshoot the device availability checks
- A Lovelace card that provides a clear overview of unavailable devices

---

## 1. Install and Configure Pyscript

### 1.1 Install Pyscript via HACS

First, install **Pyscript** (preferably via HACS).

> **Important:** After installation, do **not** add Pyscript to Home Assistant through **Settings → Devices & services → Integrations**.

For these scripts, Pyscript is used in **YAML mode** so that all required configuration options are available.

### 1.2 Add Pyscript to `configuration.yaml`

Open:

```text
/config/configuration.yaml
```

Add:

```yaml
pyscript: !include pyscript/config.yaml
```

The folder name `pyscript` is fixed and must not be changed.

The resulting configuration structure should look like this:

```text
config/
├── configuration.yaml
└── pyscript/
    ├── config.yaml
    ├── ...
    └── modules/
        └── ...
```

### 1.3 Copy the Pyscript Files

Extract the provided ZIP file.

Copy all included files and subfolders to:

```text
/config/pyscript/
```

Also copy the folder:

```text
modules
```

including all of its contents.

The original folder structure from the ZIP file must be preserved.

---

## 2. Create a Long-Lived Access Token

The search scripts (yaml/dashboards) communicate with Home Assistant itself through the Home Assistant API. For this, a **Long-Lived Access Token** is required.

### 2.1 Create the Token

Open your Home Assistant user profile via your profile icon in the sidebar.

Then open the **Security** tab.

At the bottom of the page, you will find the option to create a **Long-Lived Access Token**.

Click:

**Create Token**

Give the token a recognizable name, for example:

```text
Pyscript
```

After creating it, Home Assistant will display a long string of characters.

> **Important:** Copy the token immediately and store it temporarily. Home Assistant will not show the full token again later.

---

## 3. Add the Token to `secrets.yaml`

Open:

```text
/config/secrets.yaml
```

Add two secrets.

Replace `<token>` in the examples below with the complete Long-Lived Access Token.

```yaml
ha_long_lived_token: <token>
```

And:

```yaml
ha_long_lived_header: 'Bearer <token>'
```

Example:

```yaml
ha_long_lived_token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
ha_long_lived_header: 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
```

For the second variant, make sure that:

- `Bearer` remains in place
- There is exactly one space between `Bearer` and the token
- The single quotes around the complete value are preserved

---

## 4. Check the Configuration and Restart Home Assistant

Do not restart Home Assistant yet.

First, check whether the configuration is valid.

Use the Home Assistant **Check Configuration** function and run the configuration check.

Resolve any reported configuration errors before continuing.

If the configuration check completes successfully, restart Home Assistant.

After the restart, also check the Home Assistant logs for any Pyscript-related errors.

---

## 5. Available Pyscript Actions

If the installation completed correctly, several new Pyscript actions will be available under **Tools → Actions**.

### `pyscript.search_yaml`

Searches the Home Assistant YAML files for a specified text string or partial string.

This is useful, for example, if you want to find:

- Where a specific entity is used
- Which YAML file contains a specific setting
- Where an old entity name still appears

Wildcards can also be used:

```text
*
```

Matches any sequence of characters.

```text
?
```

Matches exactly one character.

### `pyscript.search_dashboard`

Searches Home Assistant dashboards for a specified text string or partial string.

This is useful when you want to find out on which dashboard or in which card a specific entity is being used.

Wildcards such as `*` and `?` can also be used here.

### `pyscript.get_integrations`

Helper action that returns a list of names of all available Home Assistant integrations. 

---

## 6. `pyscript.unavailable_devices`

The scripts also create the following entity:

```text
pyscript.unavailable_devices
```

This entity tracks which devices are currently unavailable.

This differs from Home Assistant's standard list of unavailable entities.

### Why Check Devices Instead of Entities?

Home Assistant mainly works with the concept of an **unavailable entity**.

However, a physical device can contain multiple entities. For example, a smart plug may contain:

- A switch
- A power sensor
- An energy sensor
- A voltage sensor
- A connection sensor

If such a device fails, several entities may become unavailable at the same time.

Displaying all individual entities can quickly result in a long and difficult-to-read list.

The script therefore groups this information at **device level**.

The basic principle is:

> If the relevant entities of a device are unavailable, the device itself is considered unavailable.

This makes it much easier to see which physical devices are actually missing or unreachable.

---

## 7. Default Exceptions

Not every entity can be used directly to determine whether a device is available.

The script therefore includes several default exceptions.

### Connection Entities

Entities of the `connection` type are ignored.

These entities may remain available even when other entities of the same device are no longer responding. They are therefore not suitable as a reliable availability check.

### Entities Added by Other Integrations

Some integrations add extra entities to an existing device.

Examples include:

- Powercalc
- Template helpers (that add the entity to a device)

These entities do not necessarily have the same availability status as the physical device itself.

The script can take this into account so that these additional entities do not unintentionally affect the device availability check.
Entities from integrations that should be ignored are defined in `extend_integrations` (Default PowerCalc and Template).

---

## 8. Configure Your Own Exceptions

In special situations, you can configure additional exceptions.

This configuration is stored in:

```text
unavailable_devices.py
```

Several types of exceptions are available.

### 8.1 Ignore Devices Completely

You can define a list of devices that should be excluded entirely from the availability check.

The **device ID** is used for this.

This is useful for devices that you intentionally want to keep outside the availability monitoring.

### 8.2 Expected Devices

Some devices are not permanently present or are intentionally powered off completely.

One example is a smart light that is regularly switched off using the physical wall switch.

These devices can be registered as **expected devices**.

An expected device:

- Is still monitored by the script
- Still appears in the results when it is unavailable
- Is counted separately
- Is shown as informational rather than as an unexpected failure

This allows you to distinguish between:

- Devices that are unexpectedly missing
- Devices that are sometimes unavailable by design or by user choice

### 8.3 Exclude Specific Entities

In exceptional cases, a device may contain an entity that is not suitable for determining the availability of that device.

These specific entities can be excluded individually from the unavailable test.

Only use this when there is a clear reason to do so.

An example would be an entity that remains permanently available through an integration even when the underlying physical device is no longer reachable.

### 8.4 Exclude Additional Integrations

The script contains a list of integrations that may add entities to existing devices.

By default, this includes, among others:

- Powercalc
- Template

If you use another integration that adds extra entities to existing devices in the same way, you can add it to this list.

For most Home Assistant installations, this will not be necessary.

---

## 9. Diagnostic Actions

To make maintenance and troubleshooting easier, the script adds additional diagnostic actions.

### `pyscript.device_availability_check_configured_lists`

This action checks whether the manually configured exceptions are still valid.

Use this check, for example, after:

- Devices have been removed
- Devices have been added again
- Entity IDs have changed
- Integrations have been reinstalled
- Exception lists have been modified

This allows you to quickly detect whether a configured device ID or entity no longer exists.

### `pyscript.device_availability_test`

This action runs the availability check for a specific device and shows the results of the individual entity tests.

Use this function when a device:

- Is incorrectly shown as unavailable
- Is not shown as unavailable when you expect it to be
- Is evaluated incorrectly because of a specific entity

This is the main diagnostic function to use when configuring exceptions.

---

## 10. Unavailable Devices Card

In addition to the scripts, a Lovelace card is included that provides a clear visual representation of the results from `pyscript.unavailable_devices`.

By default, the card shows:

- The trend/history of the number of unavailable devices
- The current number of unavailable devices
- The current list of unavailable devices
- Separate overviews of expected and unexpected unavailable devices

---

## 11. Alerts and Info

The current list is divided into two categories.

### Alerts

The **Alerts** section contains devices that are unexpectedly unavailable.

These are devices that would normally be expected to remain reachable.

This list should therefore receive attention first.

### Info

The **Info** section contains devices configured as `expected_devices`.

These devices are unavailable, but that may be an expected situation.

For example, a light or another device may intentionally be fully powered off from time to time.

---

## 12. Navigation from the Card

The card is interactive.

When you click a device, Home Assistant navigates to the corresponding **device panel**.

From there, you can directly:

- Inspect the entities of the device
- Check its current status
- View diagnostic information
- Check which integration the device belongs to

---

## 13. Summary When Many Devices Are Unavailable

During events such as a Home Assistant startup, many devices may temporarily be unavailable at the same time.

A list containing dozens of devices is not very useful in that situation.

For that reason, the card switches to a summarized view above a configurable limit.

Instead of showing all individual devices, the card then shows, among other things:

- The number of missing devices
- A grouping by integration
- The number of missing devices per integration

When you click an integration, Home Assistant navigates to that integration.

The threshold at which the card switches from the full list to the summarized view is configurable.

By default, the limit is:

```text
30 devices
```

The value can be changed in the script.

---

## 14. Required Custom Cards

The Unavailable Devices card requires four custom Lovelace cards.

These can be installed through HACS.

### Expander Card

Use:

```text
custom:expander-card
```

Repository:

<https://github.com/MelleD/lovelace-expander-card>

### Statistics Graph Chart Card

Use:

```text
custom:statistics-graph-chart-card
```

Repository:

<https://github.com/cataseven/Statistics-Graph-Chart-Card>

### Auto Entities

Several variants of Auto Entities exist.

The recommended version is the one maintained by **Lint-Free Technology**:

```text
custom:auto-entities
```

Repository:

<https://github.com/Lint-Free-Technology/lovelace-auto-entities>

### Template Entity Row

For Template Entity Row, the version maintained by **Lint-Free Technology** is also recommended:

```text
custom:template-entity-row
```

Repository:

<https://github.com/Lint-Free-Technology/lovelace-template-entity-row>

---

## 15. Add the Unavailable Devices Card to a Dashboard

Once the four required custom cards have been installed, the provided card can be added to a Home Assistant dashboard.

The easiest method is:

1. Open the Home Assistant dashboard where you want to add the card.
2. Select **Edit Dashboard**.
3. Add a new card.
4. Choose a manually configurable card or open the **Code Editor** directly.
5. Remove the existing YAML code from the card.
6. Open the provided file:

   ```text
   unavailable-devices-card.yaml
   ```

7. Copy the complete contents of this file.
8. Paste the contents into the card's code editor.
9. Save the card.

If all required custom cards are installed correctly and `pyscript.unavailable_devices` is active, the card should now work immediately.

---

## 16. Troubleshooting

If the installation does not work correctly, check the following items in order.

### Pyscript Actions Are Missing

Check that this line is present and correct in `configuration.yaml`:

```yaml
pyscript: !include pyscript/config.yaml
```

Then check:

- Whether `/config/pyscript/config.yaml` exists
- Whether all script files are stored in `/config/pyscript/`
- Whether the `modules` folder and all of its contents were copied
- Whether Home Assistant was fully restarted after installation
- Whether the Home Assistant logs contain any Pyscript-related errors

### Scripts Report Authentication Errors

Check `secrets.yaml`.

The following two values must be present:

```yaml
ha_long_lived_token: <token>
ha_long_lived_header: 'Bearer <token>'
```

Pay particular attention to the following:

- The complete token must have been copied
- `Bearer` must be spelled correctly
- There must be exactly one space between `Bearer` and the token

### A Device Is Incorrectly Shown as Unavailable

Run:

```text
pyscript.device_availability_test
```

for the affected device.

Use the result to determine which entities are being used for the availability check.

Only if necessary, add a device, entity, or integration to the exceptions in:

```text
unavailable_devices.py
```

### Exceptions No Longer Work

Run:

```text
pyscript.device_availability_check_configured_lists
```

This allows you to verify whether all configured devices and entities still exist in Home Assistant.

### The Dashboard Card Does Not Work

First, verify that all four required custom cards have been installed through HACS:

```text
custom:expander-card
custom:statistics-graph-chart-card
custom:auto-entities
custom:template-entity-row
```

Then check:

- Whether HACS reports any updates or errors
- Whether the browser cache needs to be refreshed
- Whether `pyscript.unavailable_devices` exists
- Whether the complete contents of `unavailable-devices-card.yaml` were pasted into the card

---

## 17. Installation Summary

For a new installation, the complete process is:

1. Install **Pyscript** through HACS.
2. Do not add Pyscript through the Integrations UI.
3. Add the following to `configuration.yaml`:

   ```yaml
   pyscript: !include pyscript/config.yaml
   ```

4. Copy all provided Pyscript files to:

   ```text
   /config/pyscript/
   ```

5. Create a Home Assistant **Long-Lived Access Token**.
6. Add the token to `secrets.yaml` in both required formats.
7. Check the Home Assistant configuration.
8. Restart Home Assistant.
9. Verify that the new Pyscript actions are available.
10. Verify that `pyscript.unavailable_devices` exists.
11. Install the four required custom Lovelace cards through HACS.
12. Add `unavailable-devices-card.yaml` to the desired dashboard using the card code editor.

At this point, both the Pyscript tools and the Unavailable Devices monitoring are fully installed.
