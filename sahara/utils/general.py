# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import six

from sahara import conductor as c
from sahara import context
from sahara.i18n import _LI
from sahara.openstack.common import log as logging
from sahara.utils.notification import sender

conductor = c.API
LOG = logging.getLogger(__name__)


def find_dict(iterable, **rules):
    """Search for dict in iterable of dicts using specified key-value rules."""

    for item in iterable:
        # assert all key-value pairs from rules dict
        ok = True
        for k, v in six.iteritems(rules):
            ok = ok and k in item and item[k] == v

        if ok:
            return item

    return None


def find(lst, **kwargs):
    for obj in lst:
        match = True
        for attr, value in kwargs.items():
            if getattr(obj, attr) != value:
                match = False

        if match:
            return obj

    return None


def get_by_id(lst, id):
    for obj in lst:
        if obj.id == id:
            return obj

    return None


def change_cluster_status(cluster, status, status_description=None):
    if cluster is None:
        return None

    update_dict = {"status": status}
    if status_description:
        update_dict["status_description"] = status_description

    cluster = conductor.cluster_update(context.ctx(), cluster, update_dict)

    LOG.info(_LI("Cluster status has been changed: id=%(id)s, New status="
                 "%(status)s"), {'id': cluster.id, 'status': cluster.status})

    sender.notify(context.ctx(), cluster.id, cluster.name, cluster.status,
                  "update")

    return cluster


def check_cluster_exists(cluster):
    ctx = context.ctx()
    # check if cluster still exists (it might have been removed)
    cluster = conductor.cluster_get(ctx, cluster)
    return cluster is not None


def get_instances(cluster, instances_ids=None):
    inst_map = {}
    for node_group in cluster.node_groups:
        for instance in node_group.instances:
            inst_map[instance.id] = instance

    if instances_ids is not None:
        return [inst_map[id] for id in instances_ids]
    else:
        return [v for v in six.itervalues(inst_map)]


def clean_cluster_from_empty_ng(cluster):
    ctx = context.ctx()
    for ng in cluster.node_groups:
        if ng.count == 0:
            conductor.node_group_remove(ctx, ng)


def generate_etc_hosts(cluster):
    hosts = "127.0.0.1 localhost\n"
    for node_group in cluster.node_groups:
        for instance in node_group.instances:
            hosts += "%s %s %s\n" % (instance.internal_ip,
                                     instance.fqdn(),
                                     instance.hostname())

    return hosts


def generate_instance_name(cluster_name, node_group_name, index):
    return ("%s-%s-%03d" % (cluster_name, node_group_name, index)).lower()


def generate_auto_security_group_name(cluster_name, node_group_name):
    return ("%s-%s" % (cluster_name, node_group_name)).lower()
