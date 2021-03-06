Changelog
=========

Version 1.1.0
-------------

New features:

- New options for connecting access switches:

  - Two access switches as an MLAG pair
  - Access switch connected to other access switch

- New template variables:

  - device_model: Hardware model of this device
  - device_os_version: OS version of this device

- Get/restore previous config versions for a device
- API call to update facts (serial,os version etc) about device
- Websocket event improvements for logs, jobs and device updates

Version 1.0.0
-------------

New features:

- Syncto for core devices
- Access interface updates via API calls, "port bounce"
- Static, BGP and OSPF external routing template support
- eBGP / EVPN fabric template support
- VXLAN definition improvements (dhcp relay, mtu)

Version 0.2.0
-------------

New features:

- Syncto for dist devices
- VXLAN definitions in settings
- Firmware upgrade for Arista

Version 0.1.0
-------------

Initial test release including device database, syncto and ZTP for access devices, git repository refresh etc.
