from litp.core.plugin import Plugin
from litp.core.task import ConfigTask
from litp.core.task import CallbackTask
from litp.core.plugin_context_api import PluginApiContext

from litp.plan_types.deployment_plan import deployment_plan_tags

def mock_rpc_command(self, nodes, agent, action, action_kwargs,
                     timeout=None, retries=0):
    result = {}
    if action == 'get_all_packages':
        for node in nodes:
            if node == 'node1':
                # VRTSvxvm
                result[node] = {'data': {
                    'out': "VRTSamf 7.3.1.3500 RHEL7 x86_64\nVRTSaslapm 6.1.1.620 RHEL6 x86_64\nVRTSgab 7.3.1.2500 RHEL7 x86_64\nVRTSllt 7.3.1.4500 RHEL7 x86_64\nVRTSodm 7.3.1.2800 RHEL7 x86_64\nVRTSvxfen 7.3.1.3500 RHEL7 x86_64\nVRTSvxfs 7.3.1.3200 RHEL7 x86_64\nVRTSvxvm 7.3.1.3208 RHEL7 x86_64",
                    'status': 0,
                    'err': ''},
                                'errors': ''}
                # no VRTSvxvm but other VRTS packages
            elif node == 'node2' or node == 'node3':
                result[node] = {'data': {
                    'out': "VRTSamf 7.3.1.3500 RHEL7 x86_64\nVRTSgab 7.3.1.2500 RHEL7 x86_64\nVRTSllt 7.3.1.4500 RHEL7 x86_64\nVRTSvxfen 7.3.1.3500 RHEL7 x86_64",
                    'status': 0,
                    'err': ''},
                                'errors': ''}

        return result

    return original_rpc_command(self, nodes, agent, action, action_kwargs,
                            timeout, retries)

original_rpc_command = PluginApiContext.rpc_command
PluginApiContext.rpc_command = mock_rpc_command

class Dummy313395Plugin(Plugin):

    def _pre_cluster_cb(self, api):
        pass

    def _vxvm_upgrade_cb(self, api):
        pass

    def create_configuration(self, api):
        tasks = []

        for cluster_node in api.query("node"):
            for node_item in cluster_node.query("torf-313395"):
                tasks.append(ConfigTask(
                    cluster_node,
                    node_item,
                    'Dummy node task for {0}'.format(cluster_node.hostname),
                    'cluster_resource',
                    'resource_title_{0}'.format(node_item.prop),
                ))
        return tasks
