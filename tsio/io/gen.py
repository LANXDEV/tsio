import numpy as np
from tsio.constants import SOURCE
from tsio.io.db import DBIO, convert_to_ts_collection


def generate_source_map(ts, external_interfaces):
    source_map = dict()
    ts_collection = convert_to_ts_collection(ts)
    for ts in ts_collection:
        for i, external_interface in enumerate(external_interfaces):
            if external_interface.is_member(ts, SOURCE):
                source_map[i] = source_map.get(i, []) + [ts]
                break
    return source_map


class GenIO(DBIO):
    def __init__(self, host_address, db_name, collection_name, external_interfaces=None):
        super().__init__(host_address=host_address, db_name=db_name, collection_name=collection_name)
        if not external_interfaces:
            self.external_interfaces = []
        else:
            self.external_interfaces = external_interfaces
        self.interfaces_map = {i: interface for i, interface in enumerate(self.external_interfaces)}

    def read_attributes(self, ts, components=True, depth=np.inf, attributes=None, use_external=True, **kwargs):
        super().read_attributes(ts=ts, components=components, depth=depth, attributes=attributes)
        if use_external:
            source_map = generate_source_map(ts, self.external_interfaces)
            for interface_code, ts_list in source_map.items():
                self.interfaces_map[interface_code].read_values(ts=ts_list, components=components, depth=depth,
                                                                attributes=attributes, **kwargs)

    def read_values(self, ts, components=True, depth=np.inf, use_external=True, **kwargs):
        super().read(ts=ts, components=components, depth=depth)
        if use_external:
            source_map = generate_source_map(ts, self.external_interfaces)
            for interface_code, ts_list in source_map.items():
                self.interfaces_map[interface_code].read_values(ts=ts_list, components=components, depth=depth,
                                                                **kwargs)

    def read(self, ts, components=True, depth=np.inf, use_external=True, **kwargs):
        super().read(ts=ts, components=components, depth=depth)
        if use_external:
            source_map = generate_source_map(ts, self.external_interfaces)
            for interface_code, ts_list in source_map.items():
                self.interfaces_map[interface_code].read(ts=ts_list, components=components, depth=depth, **kwargs)