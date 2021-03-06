#!/usr/bin/env python3

import yaml
from cnaas_nms.db.session import sqla_session

from cnaas_nms.db.site import Site
from cnaas_nms.db.device import Device

with sqla_session() as session:
    for site_instance in session.query(Site).order_by(Site.id):
        print(site_instance.id, site_instance.description)
    for device_instance in session.query(Device).order_by(Device.id):
        print(device_instance.hostname, device_instance.ztp_mac, device_instance.serial)

