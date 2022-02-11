#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2021, Simon Dodsley (simon@purestorage.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = r"""
---
module: fusion_info
version_added: '1.0.0'
short_description: Collect information from Pure Fusion
description:
  - Collect information from a Pure Fusion environment.
  - By default, the module will collect basic
    information including counts for arrays, availabiliy_zones, volunmes, snapshots
    . Fleet capacity and data reduction rates are also provided.
  - Additional information can be collected based on the configured set of arguements.
author:
  - Pure Storage ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  gather_subset:
    description:
      - When supplied, this argument will define the information to be collected.
        Possible values for this include all, minimum, appliances, subscriptions,
        contracts
    type: list
    elements: str
    required: false
    default: minimum
extends_documentation_fragment:
  - purestorage.fusion.purestorage.fusion
"""

EXAMPLES = r"""
- name: collect default set of information
  fusion_info:
    app_id: key_name
    key_file: "az-admin-private-key.pem"
    register: fusion_info

- name: show default information
  debug:
    msg: "{{ fusion_info['fusion_info']['default'] }}"

- name: collect all information
  fusion_info:
    gather_subset:
      - all
    app_id: key_name
    key_file: "az-admin-private-key.pem"

- name: show all information
  debug:
    msg: "{{ fusion_info['fusion_info'] }}"
"""

RETURN = r"""
fusion_info:
  description: Returns the information collected from Fusion
  returned: always
  type: complex
"""

HAS_FUSION = True
try:
    import fusion as purefusion
except ImportError:
    HAS_FUSION = False

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.purestorage.fusion.plugins.module_utils.fusion import (
    get_fusion,
    fusion_argument_spec,
)
import datetime
import time


def generate_default_dict(fusion):
    default_info = {}

    arrays_api_instance = purefusion.ArraysApi(fusion)
    az_api_instance = purefusion.AvailabilityZonesApi(fusion)
    default_api_instance = purefusion.DefaultApi(fusion)
    hw_api_instance = purefusion.HardwareTypesApi(fusion)
    host_access_api_instance = purefusion.HostAccessPoliciesApi(fusion)
    id_api_instance = purefusion.IdentityManagerApi(fusion)
    nic_api_instance = purefusion.NetworkInterfacesApi(fusion)
    plgrp_api_instance = purefusion.PlacementGroupsApi(fusion)
    placement_api_instance = purefusion.PlacementsApi(fusion)
    protpol_api_instance = purefusion.ProtectionPoliciesApi(fusion)
    subnet_api_instance = purefusion.ProviderSubnetsApi(fusion)
    role_assign_api_instance = purefusion.RoleAssignmentsApi(fusion)
    roles_api_instance = purefusion.RolesApi(fusion)
    snapshot_api_instance = purefusion.SnapshotsApi(fusion)
    storage_api_instance = purefusion.StorageClassesApi(fusion)
    tenantnetwork_api_instance = purefusion.TenantNetworksApi(fusion)
    tenant_api_instance = purefusion.TenantsApi(fusion)
    tenantspace_api_instance = purefusion.TenantSpacesApi(fusion)
    vol_api_instance = purefusion.VolumesApi(fusion)
    volsnap_api_instance = purefusion.VolumeSnapshotsApi(fusion)

    default_info["version"] = default_api_instance.get_version().version

    storage_classes = storage_api_instance.list_storage_classes()
    default_info["storage_classes"] = len(storage_classes.items)

    protection_policies = protpol_api_instance.list_protection_policies()
    default_info["protection_policies"] = len(protection_policies.items)

    users = id_api_instance.list_users()
    default_info["users"] = len(users)

    host_access_policies = host_access_api_instance.list_host_access_policies()
    default_info["host_access_policies"] = len(host_access_policies.items)

    hw_types = hw_api_instance.list_hardware_types()
    default_info["hardware_types"] = len(hw_types.items)

    tenants = tenant_api_instance.list_tenants()
    default_info["tenants"] = len(tenants.items)
    tenant_spaces = 0
    for tenant in range(0, len(tenants.items)):
        tenant_spaces = tenant_spaces + len(
            tenantspace_api_instance.list_tenant_spaces(
                tenant_name=tenants.items[tenant].name
            ).items
        )
    default_info["tenant_spaces"] = tenant_spaces

    roles = roles_api_instance.list_roles()
    assignments = 0
    default_info["roles"] = len(roles)
    for role in range(0, len(roles)):
        assignments = assignments + len(
            role_assign_api_instance.list_role_assignments(role_name=roles[role].name)
        )
    default_info["role_assignments"] = assignments

    azs = az_api_instance.list_availability_zones()
    default_info["availability_zones"] = len(azs.items)

    arrays = subnets = networks = nics = 0
    for count in range(0, len(azs.items)):
        array_details = arrays_api_instance.list_arrays(
            availability_zone_name=azs.items[count].name
        )
        for array_detail in range(0, len(array_details.items)):
            nics = nics + len(
                nic_api_instance.list_network_interfaces(
                    availability_zone_name=azs.items[count].name,
                    array_name=array_details.items[array_detail].name,
                ).items
            )
        arrays = arrays + len(array_details.items)
        subnets = subnets + len(
            subnet_api_instance.list_provider_subnets(
                availability_zone_name=azs.items[count].name
            ).items
        )
        networks = networks + len(
            tenantnetwork_api_instance.list_tenant_networks(
                availability_zone_name=azs.items[count].name
            ).items
        )
    default_info["appiiances"] = arrays
    default_info["network_interfaces"] = nics

    default_info["provider_subnets"] = subnets
    default_info["tenant_networks"] = networks

    volumes = placement_grps = placements = snapshots = 0
    for tenant in range(0, len(tenants.items)):
        tenant_spaces = tenantspace_api_instance.list_tenant_spaces(
            tenant_name=tenants.items[tenant].name
        ).items
        for tenant_space in range(0, len(tenant_spaces)):
            volumes = volumes + len(
                vol_api_instance.list_volumes(
                    tenant_name=tenants.items[tenant].name,
                    tenant_space_name=tenant_spaces[tenant_space].name,
                ).items
            )
            placement_grps = placement_grps + len(
                plgrp_api_instance.list_placement_groups(
                    tenant_name=tenants.items[tenant].name,
                    tenant_space_name=tenant_spaces[tenant_space].name,
                ).items
            )
            placements = placements + len(
                placement_api_instance.list_placements(
                    tenant_name=tenants.items[tenant].name,
                    tenant_space_name=tenant_spaces[tenant_space].name,
                ).items
            )
            snapshots = snapshots + len(
                snapshot_api_instance.list_snapshots(
                    tenant_name=tenants.items[tenant].name,
                    tenant_space_name=tenant_spaces[tenant_space].name,
                ).items
            )
    default_info["volumes"] = volumes
    default_info["placements"] = placements
    default_info["placements_groups"] = placement_grps
    default_info["snapshots"] = snapshots

    return default_info


def generate_nics_dict(fusion):
    nics_info = {}
    nic_api_instance = purefusion.NetworkInterfacesApi(fusion)
    arrays_api_instance = purefusion.ArraysApi(fusion)
    az_api_instance = purefusion.AvailabilityZonesApi(fusion)

    azs = az_api_instance.list_availability_zones()
    for count in range(0, len(azs.items)):
        array_details = arrays_api_instance.list_arrays(
            availability_zone_name=azs.items[count].name
        )
        for array_detail in range(0, len(array_details.items)):
            array_name = (
                azs.items[count].name + "/" + array_details.items[array_detail].name
            )
            nics_info[array_name] = {}
            nics = nic_api_instance.list_network_interfaces(
                availability_zone_name=azs.items[count].name,
                array_name=array_details.items[array_detail].name,
            )

            for nic in range(0, len(nics.items)):
                nics_info[array_name][nics.items[nic].name] = {
                    "enabled": nics.items[nic].enabled,
                    "display_name": nics.items[nic].display_name,
                    "interface_type": nics.items[nic].interface_type,
                    "services": nics.items[nic].services,
                    "speed": nics.items[nic].speed,
                    "vlan": nics.items[nic].eth.vlan,
                    "address": nics.items[nic].eth.address,
                    "mac_address": nics.items[nic].eth.mac_address,
                    "gateway": nics.items[nic].eth.gateway,
                    "mtu": nics.items[nic].eth.mtu,
                    "provider_subnet": nics.items[nic].eth.provider_subnet.name,
                }
    return nics_info


def generate_hap_dict(fusion):
    hap_info = {}
    api_instance = purefusion.HostAccessPoliciesApi(fusion)
    hosts = api_instance.list_host_access_policies()
    for host in range(0, len(hosts.items)):
        name = hosts.items[host].name
        hap_info[name] = {
            "personality": hosts.items[host].personality,
            "display_name": hosts.items[host].display_name,
            "iqn": hosts.items[host].iqn,
        }
    return hap_info


def generate_array_dict(fusion):
    array_info = {}
    array_api_instance = purefusion.ArraysApi(fusion)
    az_api_instance = purefusion.AvailabilityZonesApi(fusion)
    azs = az_api_instance.list_availability_zones()
    for az in range(0, len(azs.items)):
        arrays = array_api_instance.list_arrays(
            availability_zone_name=azs.items[az].name
        )
        for array in range(0, len(arrays.items)):
            array_name = arrays.items[array].name
            array_space = array_api_instance.get_array_space(
                availability_zone_name=azs.items[az].name, array_name=array_name
            )
            array_perf = array_api_instance.get_array_performance(
                availability_zone_name=azs.items[az].name, array_name=array_name
            )
            array_info[array_name] = {
                "availability_zone": azs.items[az].name,
                "host_name": arrays.items[array].host_name,
                "display_name": arrays.items[array].display_name,
                "hardware_type": arrays.items[array].hardware_type.name,
                "appliance_id": arrays.items[array].appliance_id,
                "apartment_id": getattr(arrays.items[array], "apartment_id", None),
                "space": {
                    "total_physical_space": array_space.space_data.total_physical_space,
                },
                "performance": {
                    "read_bandwidth": array_perf.perf_data.read_bandwidth,
                    "read_latency": array_perf.perf_data.read_latency,
                    "reads_per_sec": array_perf.perf_data.reads_per_sec,
                    "write_bandwidth": array_perf.perf_data.write_bandwidth,
                    "write_latency": array_perf.perf_data.write_latency,
                    "writes_per_sec": array_perf.perf_data.writes_per_sec,
                },
            }
    return array_info


def generate_pg_dict(fusion):
    pg_info = {}
    tenant_api_instance = purefusion.TenantsApi(fusion)
    tenantspace_api_instance = purefusion.TenantSpacesApi(fusion)
    pg_api_instance = purefusion.PlacementGroupsApi(fusion)
    tenants = tenant_api_instance.list_tenants()
    for tenant in range(0, len(tenants.items)):
        tenant_spaces = tenantspace_api_instance.list_tenant_spaces(
            tenant_name=tenants.items[tenant].name
        ).items
        for tenant_space in range(0, len(tenant_spaces)):
            groups = pg_api_instance.list_placement_groups(
                tenant_name=tenants.items[tenant].name,
                tenant_space_name=tenant_spaces[tenant_space].name,
            )
            for group in range(0, len(groups.items)):
                group_name = (
                    tenants.items[tenant].name
                    + "/"
                    + tenant_spaces[tenant_space].name
                    + "/"
                    + groups.items[group].name
                )
                pg_info[group_name] = {
                    "tenant": groups.items[group].tenant.name,
                    "display_name": groups.items[group].display_name,
                    "placement_engine": groups.items[group].placement_engine,
                    "tenant_space": groups.items[group].tenant_space.name,
                    "az": groups.items[group].availability_zone.name,
                    "array": getattr(groups.items[group].array, "name", None),
                }
    return pg_info


def generate_tn_dict(fusion):
    tn_info = {}
    az_api_instance = purefusion.AvailabilityZonesApi(fusion)
    tn_api_instance = purefusion.TenantNetworksApi(fusion)
    zones = az_api_instance.list_availability_zones()
    for zone in range(0, len(zones.items)):
        networks = tn_api_instance.list_tenant_networks(
            availability_zone_name=zones.items[zone].name
        ).items
        for network in range(0, len(networks)):
            tn_name = zones.items[zone].name + "/" + networks[network].name
            tn_info[tn_name] = {
                "availability_zone": zones.items[zone].name,
                "display_name": networks[network].display_name,
                "tenant_subnets": [],
            }
            for subnet in range(0, len(networks[network].tenant_subnets)):
                tn_info[tn_name]["tenant_subnets"].append(
                    {
                        "addresses": networks[network].tenant_subnets[subnet].addresses,
                        "gateway": networks[network].tenant_subnets[subnet].gateway,
                        "mtu": networks[network].tenant_subnets[subnet].mtu,
                        "prefix": networks[network].tenant_subnets[subnet].prefix,
                        "provider_subnets": [],
                    }
                )
                for psubnet in range(
                    0, len(networks[network].tenant_subnets[subnet].provider_subnets)
                ):
                    tn_info[tn_name]["tenant_subnets"][subnet][
                        "provider_subnets"
                    ].append(
                        networks[network]
                        .tenant_subnets[subnet]
                        .provider_subnets[psubnet]
                        .name
                    )
    return tn_info


def generate_ps_dict(fusion):
    ps_info = {}
    az_api_instance = purefusion.AvailabilityZonesApi(fusion)
    ps_api_instance = purefusion.ProviderSubnetsApi(fusion)
    zones = az_api_instance.list_availability_zones()
    for zone in range(0, len(zones.items)):
        subnets = ps_api_instance.list_provider_subnets(
            availability_zone_name=zones.items[zone].name
        ).items
        for subnet in range(0, len(subnets)):
            name = zones.items[zone].name + "/" + subnets[subnet].name
            ps_info[name] = {
                "availability_zone": zones.items[zone].name,
                "display_name": subnets[subnet].display_name,
                "gateway": subnets[subnet].gateway,
                "mtu": subnets[subnet].mtu,
                "vlan": subnets[subnet].vlan,
                "prefix": subnets[subnet].prefix,
            }
    return ps_info


def generate_placements_dict(fusion):
    pl_info = {}
    tenant_api_instance = purefusion.TenantsApi(fusion)
    tenantspace_api_instance = purefusion.TenantSpacesApi(fusion)
    pl_api_instance = purefusion.PlacementsApi(fusion)
    tenants = tenant_api_instance.list_tenants()
    for tenant in range(0, len(tenants.items)):
        tenant_spaces = tenantspace_api_instance.list_tenant_spaces(
            tenant_name=tenants.items[tenant].name
        ).items
        for tenant_space in range(0, len(tenant_spaces)):
            placements = pl_api_instance.list_placements(
                tenant_name=tenants.items[tenant].name,
                tenant_space_name=tenant_spaces[tenant_space].name,
            )
            for placement in range(0, len(placements.items)):
                pl_name = (
                    tenants.items[tenant].name
                    + "/"
                    + tenant_spaces[tenant_space].name
                    + "/"
                    + placements.items[placement].name
                )
                pl_info[pl_name] = {
                    "tenant": tenants.items[tenant].name,
                    "tenant_space": tenant_spaces[tenant_space].name,
                    "display_name": placements.items[placement].display_name,
                    "placement_group": placements.items[placement].placement_group.name,
                    "storage_class": placements.items[placement].storage_class.name,
                    "array": placements.items[placement].array.name,
                    "protocols": {
                        "iscsi": {},
                        "fc": {},
                        "nvme": {},
                    },
                }
                if placements.items[placement].protocols.iscsi:
                    pl_info[pl_name]["protocols"]["iscsi"] = {
                        "iqn": placements.items[placement].protocols.iscsi.iqn,
                        "addresses": placements.items[
                            placement
                        ].protocols.iscsi.addresses,
                    }
    return pl_info


def generate_ts_dict(fusion):
    ts_info = {}
    tenant_api_instance = purefusion.TenantsApi(fusion)
    tenantspace_api_instance = purefusion.TenantSpacesApi(fusion)
    tenants = tenant_api_instance.list_tenants()
    for tenant in range(0, len(tenants.items)):
        tenant_spaces = tenantspace_api_instance.list_tenant_spaces(
            tenant_name=tenants.items[tenant].name
        ).items
        for tenant_space in range(0, len(tenant_spaces)):
            ts_name = (
                tenants.items[tenant].name + "/" + tenant_spaces[tenant_space].name
            )
            ts_info[ts_name] = {
                "tenant": tenants.items[tenant].name,
                "display_name": tenant_spaces[tenant_space].display_name,
            }
    return ts_info


def generate_pp_dict(fusion):
    pp_info = {}
    api_instance = purefusion.ProtectionPoliciesApi(fusion)
    policies = api_instance.list_protection_policies()
    for policy in range(0, len(policies.items)):
        policy_name = policies.items[policy].name
        pp_info[policy_name] = {
            "local_rpo": policies.items[policy].local_rpo,
            "display_name": policies.items[policy].display_name,
            "local_retention": policies.items[policy].local_retention,
        }
    return pp_info


def generate_tenant_dict(fusion):
    tenant_info = {}
    api_instance = purefusion.TenantsApi(fusion)
    tenants = api_instance.list_tenants()
    for tenant in range(0, len(tenants.items)):
        name = tenants.items[tenant].name
        tenant_info[name] = {
            "display_name": tenants.items[tenant].display_name,
        }
    return tenant_info


def generate_zones_dict(fusion):
    zones_info = {}
    api_instance = purefusion.AvailabilityZonesApi(fusion)
    zones = api_instance.list_availability_zones()
    for zone in range(0, len(zones.items)):
        az_name = zones.items[zone].name
        zones_info[az_name] = {
            "display_name": zones.items[zone].display_name,
            "region": zones.items[zone].region.name,
        }
    return zones_info


def generate_roles_dict(fusion):
    roles_info = {}
    api_instance = purefusion.RolesApi(fusion)
    roles = api_instance.list_roles()
    for role in range(0, len(roles)):
        name = roles[role].name
        roles_info[name] = {
            "display_name": roles[role].display_name,
            "scopes": roles[role].assignable_scopes,
        }
    return roles_info


def generate_users_dict(fusion):
    users_info = {}
    api_instance = purefusion.IdentityManagerApi(fusion)
    users = api_instance.list_users()
    for user in range(0, len(users)):
        name = users[user].name
        users_info[name] = {
            "display_name": users[user].display_name,
            "email": users[user].email,
            "id": users[user].id,
        }
    return users_info


def generate_hardware_dict(fusion):
    hardware_info = {}
    api_instance = purefusion.HardwareTypesApi(fusion)
    hw_types = api_instance.list_hardware_types()
    for hw_type in range(0, len(hw_types.items)):
        type_name = hw_types.items[hw_type].name
        hardware_info[type_name] = {
            "array_type": hw_types.items[hw_type].array_type,
            "display_name": hw_types.items[hw_type].display_name,
            "media_type": hw_types.items[hw_type].media_type,
        }
    return hardware_info


def generate_storageclass_dict(fusion):
    sc_info = {}
    api_instance = purefusion.StorageClassesApi(fusion)
    classes = api_instance.list_storage_classes()
    for s_class in range(0, len(classes.items)):
        sc_name = classes.items[s_class].name
        sc_info[sc_name] = {
            "bandwidth_limit": getattr(classes.items[s_class], "bandwidth_limit", None),
            "iops_limit": getattr(classes.items[s_class], "iops_limit", None),
            "size_limit": getattr(classes.items[s_class], "size_limit", None),
            "display_name": classes.items[s_class].display_name,
            "hardware_type": classes.items[s_class].hardware_type.name,
        }
    return sc_info


def generate_volumes_dict(fusion):
    volume_info = {}

    tenant_api_instance = purefusion.TenantsApi(fusion)
    vol_api_instance = purefusion.VolumesApi(fusion)
    tenant_space_api_instance = purefusion.TenantSpacesApi(fusion)

    tenants = tenant_api_instance.list_tenants()
    for tenant in range(0, len(tenants.items)):
        tenant_spaces = tenant_space_api_instance.list_tenant_spaces(
            tenant_name=tenants.items[tenant].name
        ).items
        for tenant_space in range(0, len(tenant_spaces)):
            volumes = vol_api_instance.list_volumes(
                tenant_name=tenants.items[tenant].name,
                tenant_space_name=tenant_spaces[tenant_space].name,
            )
            for volume in range(0, len(volumes.items)):
                vol_name = (
                    tenants.items[tenant].name
                    + "/"
                    + tenant_spaces[tenant_space].name
                    + "/"
                    + volumes.items[volume].name
                )
                volume_info[vol_name] = {
                    "tenant": tenants.items[tenant].name,
                    "tenant_space": tenant_spaces[tenant_space].name,
                    "name": volumes.items[volume].name,
                    "size": volumes.items[volume].size,
                    "display_name": volumes.items[volume].display_name,
                    "array": volumes.items[volume].array.name,
                    "placement": volumes.items[volume].placement.name,
                    "placement_group": volumes.items[volume].placement_group.name,
                    "source_volume_snapshot": getattr(
                        volumes.items[volume].source_volume_snapshot, "name", None
                    ),
                    "protection_policy": getattr(
                        volumes.items[volume].protection_policy, "name", None
                    ),
                    "storage_class": volumes.items[volume].storage_class.name,
                    "serial_number": volumes.items[volume].serial_number,
                    "target": {},
                }
                volume_info[vol_name]["target"] = {
                    "iscsi": {
                        "addresses": volumes.items[volume].target.iscsi.addresses,
                        "iqn": volumes.items[volume].target.iscsi.iqn,
                    },
                    "nvme": {
                        "addresses": None,
                        "nqn": None,
                    },
                    "fc": {
                        "addresses": None,
                        "wwns": None,
                    },
                }
    return volume_info


def main():
    argument_spec = fusion_argument_spec()
    argument_spec.update(
        dict(gather_subset=dict(default="minimum", type="list", elements="str"))
    )

    module = AnsibleModule(argument_spec, supports_check_mode=True)
    if not HAS_FUSION:
        module.fail_json(msg="fusion SDK required for this module")

    fusion = get_fusion(module)

    subset = [test.lower() for test in module.params["gather_subset"]]
    valid_subsets = (
        "all",
        "minimum",
        "roles",
        "users",
        "placements",
        "arrays",
        "hardware",
        "volumes",
        "hosts",
        "storageclass",
        "protection_policies",
        "placement_groups",
        "interfaces",
        "zones",
        "subnets",
        "snapshots",
        "tenants",
        "tenant_spaces",
        "tenant_networks",
    )
    subset_test = (test in valid_subsets for test in subset)
    if not all(subset_test):
        module.fail_json(
            msg="value must gather_subset must be one or more of: %s, got: %s"
            % (",".join(valid_subsets), ",".join(subset))
        )

    info = {}

    if "minimum" in subset or "all" in subset:
        info["default"] = generate_default_dict(fusion)
    if "hardware" in subset or "all" in subset:
        info["hardware"] = generate_hardware_dict(fusion)
    if "users" in subset or "all" in subset:
        info["users"] = generate_users_dict(fusion)
    if "subnets" in subset or "all" in subset:
        info["subnets"] = generate_ps_dict(fusion)
    if "zones" in subset or "all" in subset:
        info["zones"] = generate_zones_dict(fusion)
    if "roles" in subset or "all" in subset:
        info["roles"] = generate_roles_dict(fusion)
    if "placements" in subset or "all" in subset:
        info["placements"] = generate_placements_dict(fusion)
    if "volumes" in subset or "all" in subset:
        info["volumes"] = generate_volumes_dict(fusion)
    if "protection_policies" in subset or "all" in subset:
        info["protection_policies"] = generate_pp_dict(fusion)
    if "placement_groups" in subset or "all" in subset:
        info["placement_groups"] = generate_pg_dict(fusion)
    if "storageclass" in subset or "all" in subset:
        info["storageclass"] = generate_storageclass_dict(fusion)
    if "interfaces" in subset or "all" in subset:
        info["interfaces"] = generate_nics_dict(fusion)
    if "hosts" in subset or "all" in subset:
        info["hosts"] = generate_hap_dict(fusion)
    if "arrays" in subset or "all" in subset:
        info["arrays"] = generate_array_dict(fusion)
    if "tenants" in subset or "all" in subset:
        info["tenants"] = generate_tenant_dict(fusion)
    if "tenant_spaces" in subset or "all" in subset:
        info["tenant_spaces"] = generate_ts_dict(fusion)
    if "tenant_networks" in subset or "all" in subset:
        info["tenant_networks"] = generate_tn_dict(fusion)

    module.exit_json(changed=False, fusion_info=info)


if __name__ == "__main__":
    main()
