##############################################################################
# COPYRIGHT Ericsson AB 2013
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

from litp.core.plugin import Plugin
from litp.core.plugin_context_api import PluginApiContext


def mock_rpc_command(self, nodes, agent, action, action_kwargs, timeout=None, retries=0):
    result = {}
    if action == 'get_all_packages':
        for node in nodes:
            result[node] = {'data': {'out': "kernel_CXP9030581 1.26.5 1 noarch\nat 3.1.10 44.el6_6.2 x86_64\naugeas-libs 1.0.0 7.el6_6.1 x86_64\nbash 4.1.2 29.el6_6.1 x86_64",
                                     'status': 0,
                                     'err': ''},
                            'errors': ''}
        return result


    return original_rpc_command(self, nodes, agent, action, action_kwargs, timeout, retries)

original_rpc_command = PluginApiContext.rpc_command
PluginApiContext.rpc_command = mock_rpc_command

class PatchMcollectivePlugin(Plugin):
    def create_configuration(self, plugin_api_context):
        return []

    def create_snapshot_plan(self, plugin_api_context):
        return []
