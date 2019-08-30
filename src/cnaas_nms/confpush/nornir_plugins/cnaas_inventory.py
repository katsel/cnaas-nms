import ipaddress

from nornir.core.deserializer.inventory import Inventory

from cnaas_nms.db.device import Device, DeviceType, DeviceState
from cnaas_nms.db.settings import get_groups
import cnaas_nms.db.session

class CnaasInventory(Inventory):
    def _get_management_ip(self, management_ip, dhcp_ip):
        if issubclass(management_ip.__class__, ipaddress.IPv4Address):
            return str(management_ip)
        elif issubclass(dhcp_ip.__class__, ipaddress.IPv4Address):
            return str(dhcp_ip)
        else:
            return None

    def __init__(self, **kwargs):
        hosts = {}
        with cnaas_nms.db.session.sqla_session() as session:
            instance: Device
            for instance in session.query(Device):
                hosts[instance.hostname] = {
                    'platform': instance.platform,
                    'groups': [
                        'T_'+instance.device_type.name,
                        'S_'+instance.state.name
                    ],
                    'data': {
                        'synchronized': instance.synchronized,
                        'managed': (True if instance.state == DeviceState.MANAGED else False)
                    }
                }
                for group in get_groups(instance.hostname):
                    hosts[instance.hostname]['groups'].append(group)
                hostname = self._get_management_ip(instance.management_ip, instance.dhcp_ip)
                if hostname:
                    hosts[instance.hostname]['hostname'] = hostname
                if instance.port and isinstance(instance.port, int):
                    hosts[instance.hostname]['port'] = instance.port
        groups = {
            'global': {
                'data': {
                    'k': 'v'
                }
            }
        }
        for device_type in list(DeviceType.__members__):
            groups['T_'+device_type] = {}
        for device_type in list(DeviceState.__members__):
            groups['S_'+device_type] = {}
        for group in get_groups():
            groups[group] = {}
        groups['S_DHCP_BOOT']['username'] = 'admin'
        groups['S_DHCP_BOOT']['password'] = 'admin'
        groups['S_DISCOVERED']['username'] = 'admin'
        groups['S_DISCOVERED']['password'] = 'abc123abc123'
        groups['S_INIT']['username'] = 'admin'
        groups['S_INIT']['password'] = 'abc123abc123'
        groups['S_MANAGED']['username'] = 'admin'
        groups['S_MANAGED']['password'] = 'abc123abc123'
        defaults = {'data': {'k': 'v'} }
        super().__init__(hosts=hosts, groups=groups, defaults=defaults, **kwargs)


