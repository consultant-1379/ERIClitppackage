##############################################################################
# COPYRIGHT Ericsson AB 2013
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

import itertools
import re
import os
import time
from collections import defaultdict
from litp.core.plugin import Plugin
from litp.core.execution_manager import ConfigTask,\
                                        CallbackExecutionException,\
                                        PlanStoppedException
from litp.plan_types.deployment_plan.deployment_plan_tags \
    import VXVM_UPGRADE_TAG
from litp.core.task import CallbackTask
from litp.core.validators import ValidationError
from litp.core.model_item import ModelItem
from litp.core.plugin import PluginError
from litp.core.node_utils import wait_for_node_down,\
    wait_for_node_timestamp, wait_for_node_puppet_applying_catalog_valid
from litp.core.rpc_commands import RpcCommandProcessorBase,\
                                   RpcCommandOutputProcessor,\
                                   RpcCommandOutputNoStderrProcessor,\
                                   NoStandardErrorRpcCommandProcessor,\
                                   PuppetMcoProcessor, \
                                   RpcExecutionException,\
                                   reduce_errs,\
                                   run_rpc_command
from litp.core.litp_logging import LitpLogger
import vcs_extension.vcs_extension as vcs_ext

log = LitpLogger()

EXTRLITPPUPPET_PKG_NAME = 'EXTRlitppuppet_CXP9030746'
EXTRLITPMCOLLECTIVE_PKG_NAME = 'EXTRlitpmcollective_CXP9031034'
EXTRLITPMCOCOMMON_PKG_NAME = 'EXTRlitpmcollectivecommon_CXP9031353'
EXTRSERVERJRE_PKG_NAME = 'EXTRserverjre_CXP9035480'
DISALLOWED_PACKAGES_COMMON = ['EXTRlitpmcollective_CXP9031034',
                              EXTRLITPPUPPET_PKG_NAME,
                              'EXTRlitppuppetserver_CXP9030764',
                              'EXTRlitppuppetserver_CXP9037406']

DISALLOWED_PACKAGES_MS = DISALLOWED_PACKAGES_COMMON + \
                         ['httpd',
                          'EXTRlitperlang_CXP9031333',
                          'EXTRlitprabbitmqserver_CXP9031043',
                          'EXTRlitpmcollectiveclient_CXP9031352']

DISALLOWED_PACKAGES_MN = DISALLOWED_PACKAGES_COMMON + ['openssh-server']

DMP_MSG_to_IGNORE = 'following vgs could not be migrated as they are in use'
VERITAS_UG_ERR = "ERROR: No appropriate modules found. Error in "\
                 "loading module \"vxdmp\". See documentation."
YUM_PENDING_ERROR = \
    "There are unfinished transactions remaining. You might consider " \
    "running yum-complete-transaction, or \"yum-complete-transaction " \
    "--cleanup-only\" and \"yum history redo last\", first to finish them. " \
    "If those don't work you'll have to try removing/installing packages by " \
    "hand (maybe package-cleanup can help)."

VXVM_RPM_NAME = 'VRTSvxvm'
YUM_WARNING_to_IGNORE = 'Warning: RPMDB altered outside of yum'
YUM_INJECTIONINIT_MSG_to_IGNORE = "No module named injectioninit"
YUM_MCO_AGENT = "yum"
YUM_UPGRADE_PACKAGE_ACTION = "upgrade_package"
YUM_SET_STATE_VCS_SERVICES_ACTION = "set_state_vcs_services"

HA_UPGRD_ONLY_TMP_DIR = '/tmp/ha_engine_upgrade/'
VCS_API_MCO_AGENT = 'vcs_engine_upgrade_api'


class YumErrCheckRpcCommandProcessor(RpcCommandProcessorBase):
    """A command processor that checks stderr and stdout for a specific error
    that happens sometimes during Veritas upgrade. """

    def _look_for_errors_in_node(self, node, agent_result, errors, args):
        if agent_result.get('errors'):
            errors[node].append(agent_result.get('errors'))
        elif self._errors_in_agent(node, agent_result, *args):
            errors[node].extend(
                self._errors_in_agent(node, agent_result, *args)
            )
        return errors

    def _errors_in_agent(self, node, agent_result):
        errors = []
        # super call will return errors if retcode != 0
        error = super(YumErrCheckRpcCommandProcessor, self). \
            _errors_in_agent(node, agent_result)
        if not error:
            stdout_text = agent_result.get('data', {}).get('out')
            regex = r"^(.*)Package {0}(.*) will be an update(.*)$".format(
                VXVM_RPM_NAME)
            pattern = re.compile(regex, re.MULTILINE)
            stderr_text = agent_result.get('data', {}).get('err')
            # keep checking only if veritas rpm is going to be updated
            if pattern.search(stdout_text):
                if VERITAS_UG_ERR in stderr_text or \
                   VERITAS_UG_ERR in stdout_text:
                    errors.append(VERITAS_UG_ERR)
            # usual stderr check for any other yum error
            if stderr_text:
                if YUM_WARNING_to_IGNORE in stderr_text:
                    pass
                elif YUM_INJECTIONINIT_MSG_to_IGNORE in stderr_text:
                    pass
                else:
                    errors.append("{0} produced error message: {1}".
                                  format(node, stderr_text))

        else:
            errors.append(error)
        return errors


class PackagePlugin(Plugin):

    """LITP package plugin for installation and upgrade\
     of software packages."""

    _permanent_repos = ['OS', 'CUSTOM', 'UPDATES', 'LITP']

    class Timeout(object):
        def __init__(self, seconds):
            self._wait_for = seconds
            self._start_time = PackagePlugin.Timeout.get_time()

        @staticmethod
        def get_time():
            return time.time()

        @staticmethod
        def sleep_for(seconds):
            time.sleep(seconds)

        def has_time_elapsed(self):
            return self.get_time_elapsed() >= self._wait_for

        def get_time_elapsed(self):
            return int(PackagePlugin.Timeout.get_time() - self._start_time)

    def validate_model(self, api_context):
        """
        The package plugin validates the following:

        - package is uniquely linked under the node.

        - package for upgrade has the same name and architecture as the \
        original one.

        - the replacement of a modelled package is not supported.

        - packages requirements must be modelled, cannot be marked for \
          removal from the model, and cannot have cycles.

        - packages included in the default manifests (apache, rabbitmq etc) \
          cannot be modelled.
        """
        errors = []
        errors.extend(self._validate_name_and_arch(api_context))
        errors.extend(self._validate_all_packages(api_context))
        errors.extend(self._validate_yum_repos(api_context))
        errors.extend(self._validate_packages_replacements(api_context))
        errors.extend(self._validate_packages_requirements(api_context))
        errors.extend(self._validate_not_allowed_packages(api_context))
        return errors

    @staticmethod
    def _get_nodes_and_ms(api_context):
        nodes = api_context.query("node") + api_context.query("ms")
        return [node for node in nodes if not node.is_for_removal()]

    @staticmethod
    def _get_cluster_services(api_context):
        cluster_services = []
        #INFO: Refactor to .query('vcs-cluster-service') when/if implemented
        vcs_clusters = api_context.query('vcs-cluster')
        for cluster in vcs_clusters:
            cluster_services.extend(cluster.services)
        return cluster_services

    @staticmethod
    def _is_replacement_package(package):
        """
        Determine if a package object has the replaces property.

        :param package : that is the the subject of the task.
        :type  package : object

        :return : boolean
        """
        return hasattr(package, 'replaces') and \
                package.replaces is not None

    @staticmethod
    def _has_requirements(package):
        """
        Determine if a package object has the requires property.

        :param package : that is the the subject of the task.
        :type  package : object

        :return : boolean
        """
        return hasattr(package, 'requires') and \
                package.requires is not None

    @staticmethod
    def _get_package_by_name(package_name, node_packages):
        """
        Retrieve a package object from a list of packages on a
        given node by its name property, which should be a
        unique identifier.

        :param package_name : the name of a package object.
        :type  package_name : string

        :param node_packages : the packages present on a node.
        :type  node_packages : list of QueryItems

        :return : retrieved package with name or None
        """
        retrieved = [package for package in node_packages
                             if package.name == package_name]
        if retrieved:
            return retrieved[0]
        return None

    @staticmethod
    def _get_cycle_errors(package, node_packages):
        """
        Given a package with requirements and the list of packages
        on the node, determine if the there is a circular dependency
        involving package.

        :param package : that is the the subject of the task.
        :type  package : object

        :param node_packages : the packages present on a node.
        :type  node_packages : list of QueryItems

        :return : list of packages invloved in the cycle or None.
        """
        # iterative depth first search on a directed graph
        # is the cheapest way to detect cycles
        to_visit = [package]
        discovered = set()
        errors = dict()

        while len(to_visit) > 0:
            visiting = to_visit.pop()
            if not visiting in discovered:
                discovered.add(visiting)
                # visit each of the required nodes
                if PackagePlugin._has_requirements(visiting):
                    for required_package_name in visiting.requires.split(','):
                        required_package = PackagePlugin._get_package_by_name(
                                    required_package_name,
                                    node_packages
                                )
                        if required_package is not None:
                            # detect circular dependency here
                            if package == required_package and \
                                not package.get_vpath() in errors:
                                errors[package.get_vpath] = ValidationError(
                                        error_message='A cyclical requires '
                                        'exists with package(s) "%s" '
                                        'defined by "requires" property' % \
                                        ", ".join(package.requires.split(',')),
                                        item_path=package.get_vpath()
                                    )
                            else:
                                to_visit.append(required_package)
        return errors.values()

    def _validate_yum_repos(self, plugin_api_context):
        errors = []
        nodes = [n for n in plugin_api_context.query('node') if \
                                              self._node_marked_for_upgrade(n)]
        for node in nodes:
            for repo in [r for r in node.query("yum-repository") if \
                r.is_for_removal()]:
                errors.append(
                    ValidationError(
                        error_message='Create plan failed, '
                        'an upgraded node "%s" has a yum repository "%s" '
                        'in "%s" state.' % (node.hostname, repo.name,
                            repo.get_state()),
                        item_path=node.get_vpath()
                    )
                )
        return errors

    def _validate_all_packages(self, api_context):
        nodes = self._get_nodes_and_ms(api_context)
        errors = []
        for node in nodes:
            errors.extend(self._validate_all_packages_on_node(node,
                                                              api_context))
        return errors

    def _validate_packages_replacements(self, api_context):
        """
        - A package can not be replaced if the same package is already
          modelled in the node.
        - A package can not be replaced more than once.
        """
        errors = []
        all_packages = []

        nodes = self._get_nodes_and_ms(api_context)
        for node in nodes:
            replaced = {}
            all_packages = [package for package in
                        self._all_model_packages_in_node(node, api_context)
                        if not package.is_removed() and
                        not package.is_for_removal()]

            for replacer in [pkg for pkg in all_packages
                            if PackagePlugin._is_replacement_package(pkg)]:

                for package in \
                    [pkg for pkg in all_packages if pkg != replacer]:

                    if replacer.replaces == package.name:
                        msg = 'Replacement of a modelled package '\
                        '"{0}" with "{1}" is not currently supported.'.\
                           format(package.name, replacer.name)

                        errors.append(
                            ValidationError(
                                error_message=msg,
                                item_path=replacer.get_vpath())
                            )

                # LITPCDS-9963 Account replaced packages.
                replaced.setdefault(replacer.replaces, [])
                replaced[replacer.replaces].append(replacer)

            # LITPCDS-9963.
            for replaced_name, replacers in replaced.items():
                if 1 < len(replacers):
                    for replacer in replacers:
                        msg = 'Package "{0}", being replaced by "{1}", '\
                              'may be replaced only once.'.\
                              format(replaced_name, replacer.name)

                        errors.append(
                            ValidationError(
                                error_message=msg,
                                item_path=replacer.get_vpath())
                            )

        return errors

    def _validate_packages_requirements(self, api_context):
        """
        Validate all packages with the requirements property on a node

        - A packages requirements must be modelled.
        - A packages requirements cannot be marked for removal from the model.
        - A packages requirements cannot contain any cyclical dependencies.
            e.g. package_A <- package_B <- package_A

        :param plugin_api_context: plugin_api
        :type  plugin_api: object

        :return : a list of validation errors.
        """
        # LITPCDS-10123 makes sure all requires for modelled packages
        # are satisified prior to running the plan
        errors = []
        nodes = self._get_nodes_and_ms(api_context)

        for node in nodes:

            node_packages = self._all_model_packages_in_node(node, api_context)
            packages_with_requires = [package for package in node_packages
                                      if not package.is_for_removal() and
                                         not package.is_removed() and
                                      PackagePlugin._has_requirements(package)]

            for package in packages_with_requires:
                for required_package in package.requires.split(','):
                    # determine if the package has been modelled
                    modelled = PackagePlugin._get_package_by_name(
                                    required_package, node_packages
                                )
                    # Case 1. required package not inherited to the node
                    if not modelled:
                        msg = ('Package "{0}", required by "{1}",' + \
                                ' is not inherited to this node.'). \
                                format(required_package, package.name)
                        errors.append(
                            ValidationError(
                                error_message=msg,
                                item_path=package.get_vpath()
                            )
                        )
                    else:
                        # Case 2. plan wants to remove the required package,
                        #         can't remove a package that has a requirement
                        if modelled.is_for_removal() or modelled.is_removed():
                            msg = ('Package "{0}" is required by "{1}" ' + \
                                    'and cannot be removed.'). \
                                    format(modelled.name, package.name)
                            errors.append(
                                ValidationError(
                                    error_message=msg,
                                    item_path=package.get_vpath()
                                )
                            )
                # Case 3. add a validation error for each cycle detected
                #         check each package with requires for cycles
                errors += PackagePlugin._get_cycle_errors(
                                package, node_packages)
        return errors

    def _get_packages_for_node_in_cluster(self, node, api_context):
        """
        A node linked to a cluster-service will install the packages present
        in that cluster-service. This helper method retrieves all packages,
        from all the cluster-services the node is linked to.
        :param node: litp_node object
        :type node: object
        :param plugin_api_context: plugin_api
        :type  plugin_api: object
        """

        service_packages = []
        cluster_services = self._get_cluster_services(api_context)

        for service in cluster_services:
            service_nodes = [sn.get_source() if sn.get_source() else sn \
                             for sn in service.nodes]
            service_nodes = [sn for sn in service_nodes
                             if not sn.is_for_removal()]
            for node_in_cluster_service in service_nodes:
                #This is node we are looking for:
                if node_in_cluster_service == node:
                    service_packages.extend(service.runtimes.query('package'))
                    service_packages.extend( \
                                        service.applications.query('package'))

        return service_packages

    def _validate_all_packages_on_node(self, node, api_context):
        # Checks that each package in a node is uniquely linked.
        # Checks also packages defined in the cluster for cluster-services
        errors = []
        packages = [package for package in
                            self._all_model_packages_in_node(node, api_context)
                    if package.get_state() != ModelItem.ForRemoval]
        pack_names = defaultdict(list)
        for package in packages:
            pack_names[package.name].append(package)
        duplicates = []
        for (p_name, p) in pack_names.iteritems():
            if len(pack_names[p_name]) > 1:
                duplicates.extend(p)
        for package in duplicates:
            errors.append(
                ValidationError(
                    error_message='Package "%s" is duplicated '
                        'for node "%s"' % (package.name, node.hostname),
                    item_path=package.get_vpath()
                )
            )
        return errors

    def _validate_name_and_arch(self, api_context):
        nodes = self._get_nodes_and_ms(api_context)
        errors = []
        for node in nodes:
            for package in node.query("package", is_updated=True):
                if package.name != package.applied_properties.get("name") or \
                   package.arch != package.applied_properties.get("arch"):
                    errors.append(
                        ValidationError(
                            error_message="Package name or architecture "
                            "can't be modified",
                            item_path=package.get_vpath()
                        )
                    )
        return errors

    @staticmethod
    def _get_removed_nodes(cs, removed_item_ids):
        cluster = cs.parent.parent
        node_dict = dict((node.item_id, node) for node in cluster.nodes)
        return [node_dict[node_id] for node_id in removed_item_ids]

    def _get_cs_packages(self, cs):
        ''' Return a list of packages in the specified service group '''
        runtime_pkgs = cs.runtimes.query('package')
        app_pkgs = cs.applications.query('package')
        return [package for package in
                itertools.chain(runtime_pkgs, app_pkgs)
                if not package.is_for_removal()]

    def _get_cs_expansion_packages_for_node(self, cs, node):
        '''
        Return a list of packages to be added to a node as a result of
        an expansion of service group cs
        '''
        packages = []
        applied_nodes = cs.applied_properties['node_list'].split(",")
        nodes_list = cs.node_list.split(",")
        added_nodes_item_ids = set(nodes_list) - set(applied_nodes)
        if node.item_id in added_nodes_item_ids:
            packages = self._get_cs_packages(cs)
        return packages

    def _get_packages_for_node_for_sg_contraction(self, node, api):
        '''
        Return a list of packages to be removed from node as a result of
        a service group contraction
        '''
        packages = []
        cluster_services = self._get_cluster_services(api)
        for cs in cluster_services:
            if cs.is_updated():
                applied_nodes = cs.applied_properties['node_list'].split(",")
                nodes_list = cs.node_list.split(",")
                removed_ids = set(applied_nodes) - set(nodes_list)
                if node.item_id in removed_ids:
                    packages.extend(self._get_cs_packages(cs))
        return packages

    def _is_package_new(self, node, package):
        is_new = False
        if package.get_node() or package.get_ms():
            is_new = package.is_initial()
        else:
            cs = package.get_ancestor("clustered-service")
            if (cs and (package.is_initial() or cs.is_initial() or
                        (cs.is_updated() and package in
                         self._get_cs_expansion_packages_for_node(cs, node)))):
                is_new = True
        return is_new

    def _update_model_items(self, task, package):
        cs = package.get_ancestor("clustered-service")
        if cs:
            task.model_items.add(cs)

    def _validate_not_allowed_packages(self, api_context):
        errors = []
        nodes_and_packages = [['ms', DISALLOWED_PACKAGES_MS],
                              ['node', DISALLOWED_PACKAGES_MN]]

        for node_type, disallowed_packages in nodes_and_packages:
            nodes = api_context.query(node_type)
            # fear no more, might look like n^3 complexity but in reality it is
            # n^2 (check packages for each package in each node)
            for node in nodes:
                for package in node.query('package'):
                    if package.name in disallowed_packages:
                        errors.append(
                            ValidationError(
                                error_message="Package {0} is managed by LITP".
                                              format(package.name),
                                item_path=package.get_vpath()
                            )
                        )
        return errors

    @staticmethod
    def _is_upgrade_flag_set(api_context, flag):
        """
        Check is a specific upgrade flag set
        e.g redeploy_ms which will trigger
        the generation of MS based tasks only.
        ie. LMS Redeploy Plan for RH6 Plan in RH7 Uplift.
        :param api_context: Plugin API context
        :type api_context: class PluginApiContext
        :param flag: Upgrade flag
        :type flag: string
        :return: True if flag is set on an upgrade item , else False
        :rtype: boolean
        """
        if api_context and any(
            [True for node in api_context.query('node')
             for upgrd_item in node.query('upgrade')
             if getattr(upgrd_item, flag, 'false') == 'true']):
            log.trace.info('Upgrade flag {0} is true.'.format(flag))
            return True
        else:
            return False

    def _gen_ha_upgrd_only_tasks(self, api_context):
        """
        Generate 'HA manager upgrade only' tasks
        :param api_context: Plugin API context
        :type api_context: class litp.core.plugin_context_api.PluginApiContext
        :return: list of tasks
        :rtype: list of CallbackTask objects
        """
        def _gen_freeze_tasks(clusters, ms, verb, cb):
            return [CallbackTask(ms,
                                 ('{0} all service groups on cluster "{1}"'.
                                                format(verb, c.item_id)),
                                 cb,
                                 c.query('node')[0].hostname)
                    for c in clusters]

        def _gen_update_tasks(clusters, ms):
            return [CallbackTask(ms,
                       'Updating HA software on node "{0}"'.format(n.hostname),
                                 self._ha_upgrd_only_upgrd_ha_cb,
                                 n.hostname)
                    for c in clusters
                    for n in c.nodes]

        def _gen_configure_tasks(clusters, ms):
            return [CallbackTask(ms,
                     'Configure HA software on node "{0}"'.format(n.hostname),
                                 self._ha_upgrd_only_cnfgr_ha_cb,
                                 n.hostname)
                    for c in clusters
                    for n in c.nodes]

        def _gen_stop_services_tasks(clusters, ms):
            return [CallbackTask(ms,
                                 ('Stop Puppet and disable VCS services '
                                  'on node "{0}"').format(n.hostname),
                                 self._ha_upgrd_only_stop_srvcs_cb,
                                 n.hostname)
                    for c in clusters
                    for n in c.nodes]

        def _gen_start_services_tasks(clusters, ms):
            return [CallbackTask(ms,
                                 ('Enable VCS services and start Puppet '
                                  'on node "{0}"').format(n.hostname),
                                 self._ha_upgrd_only_start_srvcs_cb,
                                 n.hostname)
                    for c in clusters
                    for n in c.nodes]

        the_ms = api_context.query('ms')[0]
        clusters = api_context.query('vcs-cluster')

        if not the_ms or not clusters:
            return []

        ts1 = _gen_freeze_tasks(clusters, the_ms, 'Freeze',
                                self._ha_upgrd_only_frz_cb)
        ts2 = _gen_stop_services_tasks(clusters, the_ms)
        ts3 = _gen_update_tasks(clusters, the_ms)
        ts4 = _gen_configure_tasks(clusters, the_ms)
        ts5 = _gen_start_services_tasks(clusters, the_ms)
        ts6 = _gen_freeze_tasks(clusters, the_ms, 'Unfreeze',
                                self._ha_upgrd_only_unfrz_cb)

        return PackagePlugin._post_process_task_sets((ts1, ts2, ts3,
                                                      ts4, ts5, ts6))

    @staticmethod
    def _post_process_task_sets(task_sets):
        """
        Post process task sets
        - merging into 1 list
        - asserting dependencies
        :param task_sets: six task sets
        :type task_sets: 6-tuple
        :return: list of CallbackTask objects
        :rtype: list
        """
        for idx, ts in enumerate(task_sets[0:-1]):
            for t in task_sets[idx + 1]:
                t.requires = set(ts)

        return [t for ts in task_sets for t in ts]

    # ---- Six callbacks ----

    @staticmethod
    def _enc_list_as_str(the_list, seperator=';'):
        """
        Encode list as string
        :param the_list: the list to iterate
        :type the_list: list
        :param seperator: the optional seperator to use for encoding
        :type seperator: string
        :return: list encoded as string
        :rtype: string
        """
        return seperator.join(the_list)

    def _start_vrts_srvcs(self, cb_api, hostname):
        """
        Start VRTS services
        :param cb_api: Callback API
        :type cb_api: class litp.core.callback_api.CallbackApi
        :param hostname: hostname of node to operate upon
        :type hostname: string
        :return: None
        """
        start_cmds = ['/etc/init.d/llt start',
                      '/etc/init.d/gab start',
                      '/etc/init.d/vxfen start',
                      '/etc/init.d/amf start',
                      '/opt/VRTSvcs/bin/hastart',
                      '/opt/VRTSvcs/bin/haconf -makerw']

        start_cmds_str = PackagePlugin._enc_list_as_str(start_cmds)
        self._do_set_state_srvcs(cb_api, hostname, start_cmds_str)

    def _ha_upgrd_only_start_srvcs_cb(self, cb_api, hostname):
        """
        HA manager upgrade only start services callback handler
        :param cb_api: Callback API
        :type cb_api: class litp.core.callback_api.CallbackApi
        :param hostname: hostname of node to operate upon
        :type hostname: string
        :return: None
        """
        self._start_vrts_srvcs(cb_api, hostname)
        self._enable_puppet(cb_api, hostname)

    def _ha_upgrd_only_stop_srvcs_cb(self, cb_api, hostname):
        """
        HA manager upgrade only stop services callback handler
        :param cb_api: Callback API
        :type cb_api: class litp.core.callback_api.CallbackApi
        :param hostname: hostname of node to operate upon
        :type hostname: string
        :return: None
        """
        self._disable_puppet(cb_api, hostname)
        self._stop_vrts_srvcs(cb_api, hostname)

    def _stop_vrts_srvcs(self, cb_api, hostname):
        """
        Stop VRTS services
        :param cb_api: Callback API
        :type cb_api: class litp.core.callback_api.CallbackApi
        :param hostname: hostname of node to operate upon
        :type hostname: string
        :return: None
        """
        stop_cmds = ['/opt/VRTSvcs/bin/haconf -dump -makero',
                     '/opt/VRTSvcs/bin/hastop -local -force',
                     '/etc/init.d/amf stop',
                     '/etc/init.d/vxfen stop',
                     '/etc/init.d/gab stop',
                     '/etc/init.d/llt stop']

        stop_cmds_str = PackagePlugin._enc_list_as_str(stop_cmds)
        self._do_set_state_srvcs(cb_api, hostname, stop_cmds_str)

    def _do_set_state_srvcs(self, cb_api, hostname, cmds_str):
        """
        Execute the yum::set_state_vcs_services MCO agent action
        :param cb_api: Callback API
        :type cb_api: class litp.core.callback_api.CallbackApi
        :param hostname: hostname of node to operate upon
        :type hostname: string
        :param cmd_str: the command(s) to execute
        :type cmd_str: string
        :return: None
        """
        self._execute_rpc_in_callback_task(cb_api,
                                           [hostname],
                                           "yum",
                                           "set_state_vcs_services",
                                           {'commands_str': cmds_str},
                                           timeout=600)

    def _ha_upgrd_only_cnfgr_ha_cb(self, cb_api, hostname):
        """
        HA manager upgrade only configure HA callback handler
        :param cb_api: Callback API
        :type cb_api: class litp.core.callback_api.CallbackApi
        :param hostname: hostname of node to operate upon
        :type hostname: string
        :return: None
        """
        conf_dir = os.path.join('/etc', 'VRTSvcs', 'conf')
        types_cf_file = "types.cf"
        dst_path = os.path.join(conf_dir, "config", types_cf_file)
        src_path = os.path.join(conf_dir, types_cf_file)

        self._execute_rpc_in_callback_task(cb_api,
                                           [hostname],
                                           'packagesimport',
                                           'save_version_file',
                                           {'destination_path': dst_path,
                                            'source_path': src_path})

        self._do_vrts_rpc(cb_api, hostname, 'update_licence')

    @staticmethod
    def _gen_full_pkg_name(pkg):
        """
        Generate full package name
        :param pkg: package representation
        :type pkg: dict
        :return: full package name
        :rtype: string
        """
        if 'Linux' == pkg['release'] and not pkg['arch']:
            pkg_name = "{0}-{1}_{2}.rpm".format(pkg['name'], pkg['version'],
                                                pkg['release'])
        else:
            pkg_name = "{0}-{1}-{2}.{3}.rpm".format(pkg['name'],
                        pkg['version'], pkg['release'], pkg['arch'])

        return pkg_name

    @staticmethod
    def _get_ha_engine_pkg_data():
        """
        Get HA manager/engine upgrade only package data
        :return: data structure representing upgrade packages
        :rtype: list of dicts
        """
        return [{'name': 'VRTSamf',
                 'version': '7.3.1.300',
                 'release': 'RHEL6',
                 'arch': 'x86_64'},
                {'name': 'VRTSgab',
                 'version': '7.3.1.200',
                 'release': 'RHEL6',
                 'arch': 'x86_64'},
                {'name': 'VRTSllt',
                 'version': '7.3.1.400',
                 'release': 'RHEL6',
                 'arch': 'x86_64'},
                {'name': 'VRTSperl',
                 'version': '5.26.0.0',
                 'release': 'RHEL6',
                 'arch': 'x86_64'},
                {'name': 'VRTSpython',
                 'version': '3.5.1.1',
                 'release': 'RHEL6',
                 'arch': 'x86_64'},
                {'name': 'VRTSsfcpi',
                 'version': '7.3.1.000',
                 'release': 'GENERIC',
                 'arch': 'noarch'},
                {'name': 'VRTSsfmh',
                 'version': '7.3.1.0',
                 'release': 'Linux',
                 'arch': ''},
                {'name': 'VRTSspt',
                 'version': '7.3.1.000',
                 'release': 'RHEL6',
                 'arch': 'noarch'},
                {'name': 'VRTSvbs',
                 'version': '7.3.1.000',
                 'release': 'RHEL6',
                 'arch': 'x86_64'},
                {'name': 'VRTSvcs',
                 'version': '7.3.1.1200',
                 'release': 'RHEL6',
                 'arch': 'x86_64'},
                {'name': 'VRTSvcsag',
                 'version': '7.3.1.000',
                 'release': 'RHEL6',
                 'arch': 'x86_64'},
                {'name': 'VRTSvcsea',
                 'version': '7.3.1.100',
                 'release': 'RHEL6',
                 'arch': 'x86_64'},
                {'name': 'VRTSvcswiz',
                 'version': '7.3.1.000',
                 'release': 'RHEL6',
                 'arch': 'x86_64'},
                {'name': 'VRTSvlic',
                 'version': '3.02.73.002',
                 'release': 'RHEL6',
                 'arch': 'x86_64'},
                {'name': 'VRTSvxfen',
                 'version': '7.3.1.300',
                 'release': 'RHEL6',
                 'arch': 'x86_64'}]

    def _do_vrts_rpc(self, cb_api, hostname, action, args=None):
        """
        Execute VRTS MCO agent
        :param cb_api: Callback API
        :type cb_api: class litp.core.callback_api.CallbackApi
        :param hostname: hostname of node to operate upon
        :type hostname: string
        :param action: MCO action name
        :type action: string
        :param args: optional action arguments
        :type args: dict
        :return: None
        """
        self._execute_rpc_in_callback_task(cb_api,
                                           [hostname],
                                           'vrts',
                                           action, args,
                                           timeout=1860)

    def _cp_pkgs_to_host(self, cb_api, hostname):
        """
        Copy packages to host
        :param cb_api: Callback API
        :type cb_api: class litp.core.callback_api.CallbackApi
        :param hostname: hostname of node to operate upon
        :type hostname: string
        :return: None
        """
        pkgs = [PackagePlugin._gen_full_pkg_name(p)
                for p in PackagePlugin._get_ha_engine_pkg_data()]

        pkgs_str = PackagePlugin._enc_list_as_str(pkgs)

        ms = cb_api.query("ms")[0]
        src_uri = 'http://{0}/3pp_el6/'.format(ms.hostname)
        self._do_vrts_rpc(cb_api, hostname, 'pull_packages',
                          {'source_dir_uri': src_uri,
                           'destination_dir': HA_UPGRD_ONLY_TMP_DIR,
                           'packages': pkgs_str})

    def _rm_pkgs_from_host(self, cb_api, hostname):
        """
        Remove packages from host
        :param cb_api: Callback API
        :type cb_api: class litp.core.callback_api.CallbackApi
        :param hostname: hostname of node to operate upon
        :type hostname: string
        :return: None
        """
        remove_rpms = ['VRTSvcswiz', 'VRTSvcsea', 'VRTSvcsdr', 'VRTSvcsag',
                       'VRTScps', 'VRTSvcs', 'VRTSamf', 'VRTSvxfen',
                       'VRTSgab', 'VRTSllt', 'VRTSspt', 'VRTSsfcpi61']

        remove_rpms_str = PackagePlugin._enc_list_as_str(remove_rpms, ' ')
        self._do_vrts_rpc(cb_api, hostname, 'rpm_remove_packages',
                          {'packages': remove_rpms_str,
                           'destination_dir': HA_UPGRD_ONLY_TMP_DIR})

    def _pre_ha_upgrd(self, cb_api, hostname):
        """
        Pre-upgrade activities
        :param cb_api: Callback API
        :type cb_api: class litp.core.callback_api.CallbackApi
        :param hostname: hostname of node to operate upon
        :type hostname: string
        :return: None
        """
        self._cp_pkgs_to_host(cb_api, hostname)
        self._rm_pkgs_from_host(cb_api, hostname)

    @staticmethod
    def _get_ordered_vrts_pkgs():
        """
        Get ordered VRTS packages
        :return: sorted/ordered packages
        :rtype: list of dicts
        """
        ha_upgrd_pkg_data = PackagePlugin._get_ha_engine_pkg_data()
        ha_upgrd_pkg_names = [p['name'] for p in ha_upgrd_pkg_data]

        ha_upgrd_pkgs_by_name = {}
        for p in ha_upgrd_pkg_data:
            ha_upgrd_pkgs_by_name[p['name']] = p

        pkg_deps = {'VRTSgab': ['VRTSllt'],
                    'VRTSvxfen': ['VRTSllt', 'VRTSgab'],
                    'VRTSvcsag': ['VRTSpython'],
                    'VRTSvcswiz': ['VRTSvcsag', 'VRTSsfmh', 'VRTSsfcpi']}

        sorted_pkg_names = sorted(ha_upgrd_pkg_names, key=pkg_deps.get)
        log.trace.debug("Upgrade order: %s" % sorted_pkg_names)

        sorted_pkgs = [ha_upgrd_pkgs_by_name[s_pkg]
                       for s_pkg in sorted_pkg_names]

        return sorted_pkgs

    def _ha_upgrd(self, cb_api, hostname):
        """
        Upgrade HA software
        :param cb_api: Callback API
        :type cb_api: class litp.core.callback_api.CallbackApi
        :param hostname: hostname of node to operate upon
        :type hostname: string
        :return: None
        """

        ordered_pkgs = PackagePlugin._get_ordered_vrts_pkgs()
        upgrd_pkgs_str = \
                    PackagePlugin._enc_list_as_str([self._gen_full_pkg_name(p)
                                                    for p in ordered_pkgs])
        self._do_vrts_rpc(cb_api, hostname, 'rpm_upgrade_packages',
                          {'packages': upgrd_pkgs_str,
                           'destination_dir': HA_UPGRD_ONLY_TMP_DIR})

    def _post_ha_upgrd(self, cb_api, hostname):
        """
        Post-upgrade activities
        :param cb_api: Callback API
        :type cb_api: class litp.core.callback_api.CallbackApi
        :param hostname: hostname of node to operate upon
        :type hostname: string
        :return: None
        """
        self._do_vrts_rpc(cb_api, hostname, 'clean_packages_dir',
                          {'destination_dir': HA_UPGRD_ONLY_TMP_DIR})

    def _ha_upgrd_only_upgrd_ha_cb(self, cb_api, hostname):
        """
        HA manager upgrade only Upgrade HA callback handler
        :param cb_api: Callback API
        :type cb_api: class litp.core.callback_api.CallbackApi
        :param hostname: hostname of node to operate upon
        :type hostname: string
        :return: None
        """
        self._pre_ha_upgrd(cb_api, hostname)
        self._ha_upgrd(cb_api, hostname)
        self._post_ha_upgrd(cb_api, hostname)

    def _ha_upgrd_only_unfrz_cb(self, cb_api, hostname):
        """
        HA manager upgrade only Unfreeze callback handler
        :param cb_api: Callback API
        :type cb_api: class litp.core.callback_api.CallbackApi
        :param hostname: hostname of node to operate upon
        :type hostname: string
        :return: None
        """
        self._do_freeze_unfreeze(cb_api, hostname, 'hagrp_unfreeze')

    def _ha_upgrd_only_frz_cb(self, cb_api, hostname):
        """
        HA manager upgrade only Freeze callback handler
        :param cb_api: Callback API
        :type cb_api: class litp.core.callback_api.CallbackApi
        :param hostname: hostname of node to operate upon
        :type hostname: string
        :return: None
        """
        self._do_freeze_unfreeze(cb_api, hostname, 'hagrp_freeze')

    def _get_frozen_status(self, cb_api, hostname):
        """
        Get HA frozen status
        :param cb_api: Callback API
        :type cb_api: class litp.core.callback_api.CallbackApi
        :param hostname: hostname of node to operate upon
        :type hostname: string
        :return: Group names and state values
        :rtype: 2-tuple
        """
        out, _ = self._execute_rpc_and_get_output(cb_api,
                                                  [hostname],
                                                  VCS_API_MCO_AGENT,
                                                  'hagrp_display_all_frozen')
        lines = out[hostname].splitlines()[1:]
        groups, values = [], []

        for line in lines:
            groups.append(line.split()[0])
            values.append(line.split()[3])

        return groups, values

    def _do_freeze_unfreeze(self, cb_api, hostname, action):
        """
        Do freeze/unfleeze
        :param cb_api: Callback API
        :type cb_api: class litp.core.callback_api.CallbackApi
        :param hostname: hostname of node to operate upon
        :type hostname: string
        :param action: freeze/unfreeze action to perform
        :type action: string
        :return: None
        """

        def _do_freeze_rpc(cb_api, hostname, action, args):
            self._execute_rpc_in_callback_task(cb_api,
                                               [hostname],
                                               VCS_API_MCO_AGENT,
                                               action, args)

        def _do_haaction_rpc(cb_api, hostname, read_write):
            _do_freeze_rpc(cb_api, hostname, 'haconf',
                           {'haaction': 'make' + read_write})

        groups, values = self._get_frozen_status(cb_api, hostname)
        target_state = 0

        if 'hagrp_freeze' == action:
            _do_haaction_rpc(cb_api, hostname, 'rw')
            target_state = 1

        for group in groups:
            _do_freeze_rpc(cb_api, hostname, action, {'group_name': group})

        timeout = PackagePlugin.Timeout(1800)

        while not timeout.has_time_elapsed():

            PackagePlugin.Timeout.sleep_for(2)

            if all([int(i) == target_state for i in values]):
                break
            else:
                _, values = self._get_frozen_status(cb_api, hostname)

        if timeout.has_time_elapsed() and \
           not all([int(i) == target_state for i in values]):
            log.trace.info("Failed to transition groups to state {0}".
                                                        format(target_state))

        _do_haaction_rpc(cb_api, hostname, 'ro')

    # ---- End callbacks ----

    def create_configuration(self, api_context):

        """
        The Package plugin provides support for installation, removal \
        and upgrade of software packages (RPMs).

        *An example of a package installation on node1:*

        .. code-block:: bash

            litp create -t package -p /software/items/package_vim -o \
name="vim-enhanced"

            litp inherit -p /deployments/d1/clusters/c1/nodes/node1/\
items/vim_package -s /software/items/package_vim

        Package upgrades can by performed at deployment level. In \
        this case all nodes which are part of that deployment will be \
        updated with new versions of the package.


        *Example CLI for the deployment level packages upgrade:*

        .. code-block:: bash

            litp upgrade -p /deployments/d1


        There is also an option to update packages on the given node only.


        *Example CLI for the node level packages upgrade:*

        .. code-block:: bash

            litp upgrade -p /deployments/d1/clusters/c1/nodes/node1


        **NOTE:**  *The package won't be upgraded if it's version is \
        controlled by LITP deployment description.*

        **NOTE:**  *The software package upgrade is only performed on LITP\
        nodes, software on the MS is not upgraded using this plugin*

        For more information, see "Install, Uninstall and Replace Packages" \
from :ref:`LITP References <litp-references>`.

        """
        if PackagePlugin._is_upgrade_flag_set(api_context, 'infra_update'):
            return []
        if PackagePlugin._is_upgrade_flag_set(api_context, 'ha_manager_only'):
            return self._gen_ha_upgrd_only_tasks(api_context)

        all_tasks, vlock_tasks = [], {}
        redeploy_ms = PackagePlugin._is_upgrade_flag_set(
            api_context, 'redeploy_ms')
        if redeploy_ms:
            nodes = api_context.query("ms")
        else:
            nodes = self._get_nodes_and_ms(api_context)
        for node in nodes:
            node_num_tasks = 0
            node_packages = self._all_model_packages_in_node(node, api_context)
            add_versionlock_task = False

            packages_for_removal = self._all_packages_to_remove_from_node(
                node, node_packages, api_context
            )

            # First Pass - do Create, Replace, Update
            for package in node_packages:
                num_tasks = len(all_tasks)
                # package has been modelled for install and for removal
                new_pkg = self._is_package_new(node, package)
                if (new_pkg and
                    package.name in [p.name for p in packages_for_removal]):
                    for p in packages_for_removal:
                        if p.name == package.name:
                            packages_for_removal.remove(p)
                            task = self._update_package_task(
                                node, package, node_packages)
                            self._update_model_items(task, package)
                            all_tasks.append(task)
                            node_num_tasks += 1

                # package has been modelled for install
                elif new_pkg:
                    task = self.get_installation_task(
                        node, node_packages, package)
                    self._update_model_items(task, package)
                    all_tasks.append(task)
                    node_num_tasks += 1

                elif package.is_updated():
                    all_tasks.append(self._update_package_task(
                                 node, package, node_packages))
                    node_num_tasks += 1

                # If a task has been added for this package check if a
                # versionlock task is required
                if (len(all_tasks) > num_tasks and
                        self._package_triggers_versionlock(package, node)):
                    add_versionlock_task = True

            # Second Pass - do Remove
            for package in packages_for_removal:
                task = self._remove_package_task(node, package)
                self._update_model_items(task, package)
                all_tasks.append(task)
                if self._package_triggers_versionlock(package, node):
                    add_versionlock_task = True

            if add_versionlock_task:
                vlock_task = self._versionlock_task(api_context, node)
                all_tasks.append(vlock_task)
                node_num_tasks += 1
                vlock_tasks[node.hostname] = vlock_task

            if bool(node_num_tasks):
                self._get_remove_vrtsfsadv_task(node, all_tasks)

        if redeploy_ms:
            upgrade_tasks = {}
        else:
            upgrade_tasks = self._tasks_for_non_tree_pkgs(api_context)

        self._set_versionlock_dependencies(vlock_tasks, upgrade_tasks)

        for _, node_upgrade_tasks in upgrade_tasks.iteritems():
            all_tasks.extend(node_upgrade_tasks)

        return all_tasks

    def _get_remove_vrtsfsadv_task(self, node, all_tasks):
        if not node.is_ms():
            cluster = node.get_cluster()
            if hasattr(cluster, "cluster_type") and \
                cluster.cluster_type in ['sfha'] and \
                self._node_marked_for_upgrade(node):
                all_tasks.append(self._remove_vrtsfsasdv(node))

    def _set_versionlock_dependencies(self, vlocked_tasks, upgrade_tasks):
        """
        Set dependencies from node upgrade tasks on versionlock tasks, because
        we want versionlock tasks to be run before any other yum-related task
        :param vlocked_tasks: {node: task} with the versionlock tasks
        :param upgrade_tasks: {node: [tasklist]} with the upgrade tasks
        """
        nodes_with_both = set(vlocked_tasks.iterkeys()).intersection(
            set(upgrade_tasks.iterkeys()))
        for hostname in nodes_with_both:
            for task in upgrade_tasks[hostname]:
                task.requires.add(vlocked_tasks[hostname])
                vlocked_tasks[hostname].tag_name = task.tag_name

    def get_installation_task(self, node, node_packages, package):
        if PackagePlugin._is_replacement_package(package):
            # this package is replacing another package
            return self._replace_package_task(node, package, node_packages)
        else:
            # this package is a fresh install
            return self._install_package_task(node, package, node_packages)

    def _all_model_packages_in_node(self, node, api):
        ''' Return a list of all packages in the model for the node '''
        packages = node.query('package')
        packages.extend(self._get_packages_for_node_in_cluster(node, api))
        return packages

    def _all_packages_to_remove_from_node(self, node, node_packages, api):
        ''' Return a list of all packages to be removed from the node '''
        packages = [p for p in node_packages if p.is_for_removal()]
        packages.extend([p for p in
                    self._get_packages_for_node_for_sg_contraction(node, api)])
        return packages

    def _package_triggers_versionlock(self, package, node,
                                      check_version_in_initial=False):
        if package.is_for_removal():
            return bool(package.version)
        if not package.version and package.applied_properties.get('version'):
            return True
        if not package.release and package.applied_properties.get('release'):
            return True
        if self._is_package_new(node, package):
            # before LITPCDS-8580 we were checking if the package was initial
            # AND had a version. Due to LITPCDS-12299 we don't want to print
            # a conflict error if a modelled package with no version has
            # upgrades
            if not check_version_in_initial:
                return True
            elif check_version_in_initial and bool(package.version):
                return True
        if package.version and package.version != 'latest':
            if package.version != package.applied_properties.get('version'):
                return True
        if package.version:
            if package.applied_properties.get('version') != 'latest' and\
            package.version == 'latest' and package.is_updated():
                return True
        if package.release:
            if package.release != package.applied_properties.get('release'):
                return True
        if package.epoch and (package.release or package.version):
            if package.epoch != package.applied_properties.get('epoch'):
                return True
        return False

    def _versionlock_task(self, api, node):
        my_excluded_packages = self._versionlock_packages(api, node)
        return ConfigTask(
                        node,
                        node,
                        'Update versionlock file on node "{0}"'.\
                                                         format(node.hostname),
                        'litp::versionlock',
                        node.hostname,
                        excluded_packages=my_excluded_packages
                )

    def _check_for_task_requirements(self, package, task, node_packages):
        """
        Determine if a given package that is the subject of a task has
        requirements on any other packages, find these packages and
        add them to the tasks requires set.

        :param package : that is the the subject of the task.
        :type  package : object

        :param task : configuration task for a deployment plan.
        :type  task : object

        :param node_packages : set of packages on a node
        :type node_packages : list of QueryItems
        """
        # LITPCDS 10123 - check if there are any requirements for
        # this task on other packages.
        #
        # - this is necessary in the initial phase for install and replace
        if PackagePlugin._has_requirements(package):
            for package_name in package.requires.split(','):
                dependent_on = PackagePlugin._get_package_by_name(
                                        package_name,
                                        node_packages
                                    )
                task.requires.add(dependent_on)

    def _install_package_task(self, node, package, node_packages):
        task = ConfigTask(
                           node,
                           package,
                           'Install package "%s" on node "%s"' % (package.name,
                                                                node.hostname),
                           "package",
                           package.name,
                           **self._get_values(package)
                )
        # LITPCDS 10123 - check if this task is dependent on others
        self._check_for_task_requirements(package, task, node_packages)
        return task

    def _update_package_task(self, node, package, node_packages):
        task = ConfigTask(
                           node,
                           package,
                           'Update package "%s" on node "%s"' % (package.name,
                                                                node.hostname),
                           "package",
                           package.name,
                           **self._get_values(package)
                )
        # LITPCDS 10123 - check if this task is dependent on others
        self._check_for_task_requirements(package, task, node_packages)
        return task

    def _remove_package_task(self, node, package):
        return ConfigTask(
                           node,
                           package,
                           'Remove package "%s" on node "%s"' % (package.name,
                                                                node.hostname),
                           "package",
                           package.name,
                           **self._get_removal_values(package)
                )

    def _generate_full_package_name(self, package):
        """
        Generate a string that is the full package name based on the
        versioning provided in the Package;
        ItemType, ie. name, epoch, version, release, arch (NEVRA).

        :param package : that you want to generate the full name for.
        :type  package : object

        :return : the full string name of package.
        """
        # packages use this format; N-E:V-R.A
        # yum uses the EVR part to determine if it replaces a package

        full_name = "%s" % (package.name)

        if "0" != package.epoch \
                and hasattr(package, 'version') and package.version:
            full_name += ("-%s:%s") % (package.epoch, package.version)

        elif hasattr(package, 'version') and package.version:
            if package.version != 'latest':
                full_name += ("-%s") % (package.version)

        if hasattr(package, 'release') and package.release:
            full_name += ("-%s") % (package.release)

        if hasattr(package, 'arch') and package.arch:
            full_name += (".%s") % (package.arch)

        return full_name

    def _generate_replace_script_from_package(self, package):
        """
        Generate a string script for replacing a package with a new
        package. The script string is then used in the replace_script
        puppet manifest.

        :param package : that you want to generate the full name for.
        :type  package : object

        :return : string script for replace operation that is embedded
        in the puppet manifest for a replace configuration task.
        """
        # LITPCDS 9630 - replace one package with another package

        return "set -e\nrpm -ev --nodeps {0}\nyum -y install {1}". \
               format(package.replaces,
                      self._generate_full_package_name(package))

    def _replace_package_task(self, node, package, node_packages):
        """
            Create a replace callback task to add to a plan.
            The package must have a package.replaces property
            otherwise this is an error.
        """
        # LITPCDS 9630 - replace one package with another package
        task = CallbackTask(
                package,
                'Replace package "%s" with "%s" on node "%s"' %
                (package.replaces, package.name, node.hostname),
                self._execute_rpc_in_callback_task,
                [node.hostname],
                'yum',
                'replace_package',
                {'replacement': self._generate_full_package_name(package),
                 'replaced': package.replaces},
                timeout=120
        )
        # LITPCDS 10123 - check if this task is dependent on others
        self._check_for_task_requirements(package, task, node_packages)
        return task

    def _remove_vrtsfsasdv(self, node):
        """
            Create a callback task to remove VRTSfsadv and
            reset systemctl unit errors for vxfs_replication.
        """
        task = CallbackTask(
                node.upgrade,
                ('Remove VRTSfsadv and reset vxfs_replication '
                'errors on node "%s"') % node.hostname,
                self._execute_rpc_in_callback_task,
                [node.hostname],
                'vrts',
                'remove_vrtsfsadv')
        return task

    def _get_values(self, item):
        # get configuration values from items properties for a task
        values = {}
        if item.version:
            if item.release:
                values['ensure'] = '-'.join([item.version,
                                             item.release])
            else:
                values['ensure'] = item.version
        else:
            values['ensure'] = "installed"

        values['require'] = []
        repo = item.repository
        if repo and repo not in self._permanent_repos:
            values['require'].extend([{'type': 'Yumrepo', 'value': repo}])

        config = item.config
        if config:
            values['configfiles'] = config

        return values

    def _get_removal_values(self, item):
        # get values from items properties for removal task
        values = self._get_values(item)
        values['ensure'] = "absent"
        return values

    def _nodes_unreachable(self, err, nodes):
        # return True if error output suggests one or more nodes
        # are unreachable.
        for n in nodes:
            name = n.hostname
            if err[name] == ['No answer from node %s' % name]:
                log.trace.info("No answer from %s" % name)
                return True
        return False

    def _tasks_for_non_tree_pkgs(self, plugin_api_context):
        # "repoquery" can fail intermittently.  We try again a few
        # times if it gives an error.  See LITPCDS-10800.
        MAX_REPOQUERY_TRIES = 4
        tasks = {}
        nodes = [n for n in plugin_api_context.query('node') if \
                                              self._node_marked_for_upgrade(n)]
        if not nodes:
            return tasks
        tries = 0
        while tries < MAX_REPOQUERY_TRIES:
            tries += 1
            log.trace.debug("running get_all_packages on %s" % (
                                ', '.join([n.hostname for n in nodes])))
            out, err = self._execute_rpc_and_get_output(
                                plugin_api_context,
                                [n.hostname for n in nodes],
                                'yum',
                                'get_all_packages')
            if not err:
                break
            log.trace.info("get_all_packages errors: " +
                            ', '.join(reduce_errs(err)))
            if self._nodes_unreachable(err, nodes):
                log.trace.debug("Some nodes unreachable - giving up")
                break

        if err:
            raise PluginError(', '.join(reduce_errs(err)))
        for node in nodes:
            tasks[node.hostname] = self._create_pkg_upgrade_tasks(
                node, out.get(node.hostname, ''),
                plugin_api_context
            )

        return tasks

    def _packages_from_output(self, node_output):
        packages = []
        for package in node_output.split('\n'):
            if package:
                packages.append(package.split())
        return packages

    def _full_version(self, package):
        if not package.version:
            package_data = package.name
        elif '-' in package.version or not package.release:
            package_data = '-'.join([package.name,
                                     package.version])
        else:
            package_data = '-'.join([package.name,
                                     package.version,
                                     package.release])
        # we assume there should always be an epoch (the item type adds one
        # in case it is not specified)
        package = ':'.join([package.epoch, package_data])
        return package

    def _format_package_conflict(self, api, node, name, version, release):
        model_pkg = [p for p in self._all_model_packages_in_node(node, api)
                                                  if p.name == name][0]
        return "Found package {0} to install on \"{1}\", but there is also"\
                " an upgrade to version {2}.".format(
                                                 self._full_version(model_pkg),
                                                 node.hostname,
                                                 '-'.join([version, release])
                                                      )

    def _versionlock_packages(self, api, node):
        # will return a list of strings consisting of the package
        # name+version+release. This will be used to populate the yum
        # versionlock file
        all_packages = []
        # we only want packages that are installed and have a version
        for package in self._all_model_packages_in_node(node, api):
            if package.version and \
            not package.is_for_removal() and package.version != 'latest':
                complete_name = self._full_version(package)
                all_packages.append(complete_name)
        msg = "Packages excluded from yum operations on node {0} for being in"\
              " the model and containing a version: ".format(node.hostname)
        if all_packages:
            msg += ' '.join(all_packages)
        else:
            msg += 'none'
        log.trace.info(msg)
        return all_packages

    def _node_marked_for_upgrade(self, node):
        if not node.query('upgrade'):
            return False
        pkgs_to_update = node.get_state() in ['Applied', 'Updated'] and \
            node.query('upgrade')[0].get_state() in ['Initial', 'Updated']
        reboot_not_done = node.query('upgrade')[0].reboot_performed == 'false'
        return pkgs_to_update or reboot_not_done

    def dmp_support_callback_task(self, callback_api, node_hostname, enable):
        self._execute_rpc_dmp_command(
            callback_api,
            [node_hostname],
            'dmp',
            'dmp_config',
            {'action': 'on' if enable else 'off'},
            timeout=600,
            retries=0 if enable else 10
        )

    def _item_updated_except(self, the_item, except_properties):
        ''' Return true if an item is updated except ignored properties.
            @param: QueryItem to be checked
            @param: list of ignored properties
        '''
        # avoid O(n^2) because applied_properties contains a `for` loop inside
        applied_props = the_item.applied_properties

        def __check(prop_name):
            try:
                if getattr(the_item, prop_name) == applied_props[prop_name]:
                    return False
            except KeyError:
                pass
            return prop_name not in except_properties
        return any([__check(prop_name) for prop_name in the_item.properties])

    def _initial_or_updated_repos(self, node):
        return [repo for repo in node.query("yum-repository") if \
            repo.is_initial() or (repo.is_updated() and
            self._item_updated_except(repo, ['checksum']))]

    @staticmethod
    def _packages_require_services_restart(node, upgrade_packages_data):

        STOP_CMDS = {'amf': '/bin/systemctl stop amf.service',
                     'gab': '/bin/systemctl stop gab.service',
                     'llt': '/bin/systemctl stop llt.service',
                     'vcsmm': '/bin/systemctl stop vcsmm.service',
                     'vxfen': '/bin/systemctl stop vxfen.service',
                     'hasrv': '/opt/VRTSvcs/bin/hastop -local -force',
                     'haconf': '/opt/VRTSvcs/bin/haconf -dump -makero',
                     'cmdserver': '/opt/VRTSvcs/bin/CmdServer -stop'}

        START_CMDS = {'amf': '/bin/systemctl start amf.service',
                      'llt': '/bin/systemctl start llt.service',
                      'gab': '/bin/systemctl start gab.service',
                      'vcsmm': '/bin/systemctl start vcsmm.service',
                      'vxfen': '/bin/systemctl start vxfen.service',
                      'hasrv': '/opt/VRTSvcs/bin/hastart',
                      'haconf': '/opt/VRTSvcs/bin/haconf -makerw',
                      'cmdserver': '/opt/VRTSvcs/bin/CmdServer'}

        pkgs_requiring_restart = \
            {'VRTSamf': {'stop': ['amf'], 'start': ['amf']},
             'VRTSaslapm': None,
             'VRTSdbac': {'stop': ['hasrv', 'vcsmm'],
                          'start': ['vcsmm', 'hasrv']},
             'VRTSllt': {'stop': ['haconf', 'hasrv', 'cmdserver',
                                  'vxfen', 'gab', 'llt'],
                         'start': ['llt', 'gab', 'vxfen',
                                   'hasrv', 'cmdserver', 'haconf']},
             'VRTSgab': {'stop': ['haconf', 'hasrv', 'cmdserver',
                                  'amf', 'vxfen', 'gab'],
                         'start': ['gab', 'vxfen', 'amf',
                                   'hasrv', 'cmdserver', 'haconf']},
             'VRTSglm': None,
             'VRTSgms': None,
             'VRTSodm': None,
             'VRTSvxfen': {'stop': ['haconf', 'hasrv', 'cmdserver', 'vxfen'],
                           'start': ['llt', 'gab', 'vxfen', 'amf', 'hasrv',
                                     'cmdserver', 'haconf']},
             'VRTSvxfs': None
             }

        upgrade_package_names = [p[0] for p in upgrade_packages_data]
        vrts_packages = ['VRTSamf', 'VRTSaslapm', 'VRTSdbac', 'VRTSllt',
                         'VRTSgab', 'VRTSglm', 'VRTSodm', 'VRTSvxfen',
                         'VRTSvxfs']

        stop_key_order = ['haconf', 'hasrv', 'vcsmm', 'cmdserver',
                          'amf', 'vxfen', 'gab', 'llt']

        start_key_order = ['llt', 'gab', 'vxfen', 'amf',
                           'vcsmm', 'hasrv', 'cmdserver', 'haconf']

        s1 = set(upgrade_package_names)
        s2 = [i for i in vrts_packages if i in s1]

        log.trace.debug("Node %s upgradeable packages: %s" % \
                        (node.hostname, s2))

        pkgs_stop_keys = []
        pkgs_start_keys = []
        for pkg in s2:
            if pkgs_requiring_restart[pkg]:
                pkgs_stop_keys.extend(pkgs_requiring_restart[pkg]['stop'])
                pkgs_start_keys.extend(pkgs_requiring_restart[pkg]['start'])

        uniq_pkgs_stop_keys = set(pkgs_stop_keys)
        uniq_pkgs_start_keys = set(pkgs_start_keys)

        # pylint: disable=W0108
        ordrd_pkgs_stop_keys = sorted(uniq_pkgs_stop_keys,
                                      key=lambda x: stop_key_order.index(x))
        # pylint: disable=W0108
        ordrd_pkgs_start_keys = sorted(uniq_pkgs_start_keys,
                                       key=lambda x: start_key_order.index(x))

        log.trace.debug("Stop keys ordered: %s" % ordrd_pkgs_stop_keys)
        log.trace.debug("Start keys ordered: %s" % ordrd_pkgs_start_keys)

        stop_commands = [STOP_CMDS[c] for c in ordrd_pkgs_stop_keys]
        start_commands = [START_CMDS[c] for c in ordrd_pkgs_start_keys]

        log.trace.debug("Node %s, VRTS RPMs to upgrade: %s, "
                        "stop commands: %s, start commands: %s" % \
                        (node.hostname, str(bool(s2)),
                         stop_commands, start_commands))

        return bool(s2), stop_commands, start_commands

    def _disable_vcs_services(self, callback_api, hostname, stop_commands):
        self._disable_puppet(callback_api, hostname)

        self._execute_rpc_in_callback_task(callback_api,
                                           [hostname],
                                           "yum",
                                           "set_state_vcs_services",
                                           {'commands_str': stop_commands},
                                           timeout=600)

    @staticmethod
    def _encode_vcs_cmds(commands):
        return ';'.join(commands)

    def _create_stop_services_task(self, node, upgrade_task,
                                   vxvm_upgrade_pre_reboot_tasks,
                                   stop_commands):

        commands_str = PackagePlugin._encode_vcs_cmds(stop_commands)

        if vxvm_upgrade_pre_reboot_tasks:
            desc = 'Disable VCS services on node "%s"' % node.hostname
            task = CallbackTask(upgrade_task.model_item, desc,
                                self._execute_rpc_in_callback_task,
                                [node.hostname],
                                'yum',
                                'set_state_vcs_services',
                                {'commands_str': commands_str},
                                timeout=600)

            for pre_reboot_task in vxvm_upgrade_pre_reboot_tasks:
                task.requires.add(pre_reboot_task)

        else:
            desc = 'Stop Puppet and disable VCS services on node "%s"' % \
                   node.hostname
            task = CallbackTask(upgrade_task.model_item, desc,
                                self._disable_vcs_services,
                                node.hostname,
                                commands_str)

        upgrade_task.requires.add(task)

        return task

    def _enable_vcs_services_start_puppet(self, callback_api,
                                          hostname, start_commands):

        commands_str = PackagePlugin._encode_vcs_cmds(start_commands)

        self._execute_rpc_in_callback_task(callback_api,
                                           [hostname],
                                           'yum',
                                           'set_state_vcs_services',
                                           {'commands_str': commands_str},
                                           timeout=600)
        self._enable_puppet(callback_api, hostname)

    def _create_start_services_task(self, node,
                                    upgrade_task, will_reboot,
                                    vxvm_upgrade_pre_reboot_tasks,
                                    start_commands):

        # vxvm_upgrade_pre_reboot_tasks includes a reboot task,
        # see _gen_upgrade_vxvm_tasks()
        task = None

        if not vxvm_upgrade_pre_reboot_tasks:
            if will_reboot:
                task = self._gen_enable_puppet_task(node)
            else:
                desc = 'Enable VCS services and start Puppet on "%s"' % \
                       node.hostname
                task = CallbackTask(upgrade_task.model_item, desc,
                                    self._enable_vcs_services_start_puppet,
                                    node.hostname,
                                    start_commands)

        if task:
            task.requires.add(upgrade_task)

        return task

    def _create_pkg_upgrade_tasks(self, node, packages, plugin_api_context):
        tasks = []

        upgrade_task = None
        mco_upgrade_task = None
        mco_restart_task = None
        puppet_being_upgraded = False
        mco_being_upgraded = False
        vxvm_upgrade_tasks = []
        enable_puppet_task = None
        stop_services_task = None

        # The task around which others revolve, upgrade or mcollective restart
        upgrade_anchor_task = None

        kernel_upgrd = False
        veritas_upgrd = False
        vxvm_upgrd = False

        package_upgrades = self._packages_from_output(packages)
        repos = self._initial_or_updated_repos(node)

        cobbler_services = plugin_api_context.query("cobbler-service")

        boot_mode = cobbler_services[0].boot_mode \
            if cobbler_services else 'bios'

        for package in package_upgrades:
            name, version, release, arch = package
            package_data = {'name': name,
                            'version': version,
                            'release': release,
                            'arch': arch}

            kernel_upgrd |= self._contains_kernel_upgrade(package_data)
            veritas_upgrd |= self._contains_veritas_upgrade(package_data)
            vxvm_upgrd |= self._contains_vxvm_upgrade(package_data)

            node_upgrade_item = node.query('upgrade')[0]
            if hasattr(node_upgrade_item, 'disable_reboot') and \
                    node_upgrade_item.disable_reboot == 'true':
                node_upgrade_item.requires_reboot = 'false'
            elif self._should_include_reboot(package_data):
                node_upgrade_item.requires_reboot = 'true'
                node_upgrade_item.reboot_performed = 'false'

            if self._puppet_being_upgraded(package_data):
                puppet_being_upgraded = True

            if self._mcollective_being_upgraded(package_data):
                mco_being_upgraded = True

            if self._contains_vxvm_upgrade(package_data):
                vxvm_upgrade_tasks = self._gen_upgrade_vxvm_tasks(node,
                                                                  boot_mode)

        restart_services, stop_commands, start_commands = \
             PackagePlugin._packages_require_services_restart(node,
                                                              package_upgrades)

        if repos or package_upgrades:
            wait_based_on_puppet = not bool(vxvm_upgrade_tasks)
            (mco_upgrade_task, upgrade_task, mco_restart_task) = \
                self._gen_all_pkg_upgrade_tasks(node,
                                                puppet_being_upgraded,
                                                mco_being_upgraded,
                                                wait_based_on_puppet,
                                                restart_services,
                                                veritas_upgrd)
            if mco_restart_task:
                upgrade_anchor_task = mco_restart_task
            elif upgrade_task:
                upgrade_anchor_task = upgrade_task
            elif mco_upgrade_task:
                upgrade_anchor_task = mco_upgrade_task

            if vxvm_upgrade_tasks:
                # First repos, then TORF-152429 tasks, then yum update
                upgrade_task.requires = set(vxvm_upgrade_tasks)
                for task in vxvm_upgrade_tasks:
                    task.requires.update(repos)
                    task.tag_name = VXVM_UPGRADE_TAG
                    tasks.append(task)
            else:
                # First repos, then yum update
                upgrade_task.requires = set(repos)

            if mco_upgrade_task:
                tasks.append(mco_upgrade_task)
            tasks.append(upgrade_task)
            if mco_restart_task:
                tasks.append(mco_restart_task)

        if upgrade_task and restart_services:
            stop_services_task = \
                self._create_stop_services_task(node, upgrade_task,
                                                vxvm_upgrade_tasks,
                                                stop_commands)
            tasks.append(stop_services_task)

        will_reboot = self._upgrade_requires_reboot(node)

        if will_reboot:
            cluster = node.get_cluster()
            loose = bool(vxvm_upgrade_tasks)
            wait_based_on_puppet = not (bool(stop_services_task) or \
                                        bool(vxvm_upgrade_tasks))
            reboot_task = self._gen_reboot_task(node, loose=loose,
                                     wait_based_on_puppet=wait_based_on_puppet)
            dmp_conf_task = None

            if upgrade_task is not None:
                reboot_task.requires = set([upgrade_anchor_task])
                self.add_vxvm_upgrade_tag([mco_upgrade_task, upgrade_task,
                                           mco_restart_task])

            if hasattr(cluster, 'cluster_type') and \
               'sfha' == cluster.cluster_type and \
               (kernel_upgrd or vxvm_upgrd) and \
                'uefi' != boot_mode:
                dmp_conf_task = CallbackTask(node,
                    'Re-enable VxDMP on node "%s"' % node.hostname,
                    self.dmp_support_callback_task,
                    node.hostname,
                    enable=True,
                    tag_name=VXVM_UPGRADE_TAG)
                if upgrade_task is not None:
                    dmp_conf_task.requires = set([upgrade_anchor_task])
                reboot_task.requires.add(dmp_conf_task)
                tasks.append(dmp_conf_task)
            reboot_task.tag_name = VXVM_UPGRADE_TAG
            tasks.append(reboot_task)
            if vxvm_upgrade_tasks:
                enable_puppet_task = self._gen_enable_puppet_task(node)
                enable_puppet_task.requires = set([reboot_task])
                enable_puppet_task.tag_name = VXVM_UPGRADE_TAG
                tasks.append(enable_puppet_task)
                if boot_mode != 'uefi':
                    lvm_filter_task = self._gen_lvm_add_filter_task(node)
                    lvm_filter_task.tag_name = VXVM_UPGRADE_TAG
                    reboot_task.requires.add(lvm_filter_task)
                    if upgrade_task:
                        lvm_filter_task.requires = set([upgrade_anchor_task])

                    # Where there is a Re-enable VxDMP task, then the Add LVM
                    # task
                    # needs to require it.
                    if dmp_conf_task:
                        lvm_filter_task.requires.add(dmp_conf_task)

                    tasks.append(lvm_filter_task)

        start_services_task = None
        if upgrade_task and restart_services:
            start_services_task = \
                   self._create_start_services_task(node,
                                                    upgrade_anchor_task,
                                                    will_reboot,
                                                    bool(vxvm_upgrade_tasks),
                                                    start_commands)
            if start_services_task:
                tasks.append(start_services_task)

        self.add_vxvm_upgrade_tag([stop_services_task,
                                   start_services_task])

        return tasks

    def add_vxvm_upgrade_tag(self, tasks):

        for task in tasks:
            if task is not None:
                task.tag_name = VXVM_UPGRADE_TAG

    def _contains_vxvm_upgrade(self, package_data):
        return package_data['name'] == VXVM_RPM_NAME and \
           package_data['release'] == 'RHEL7'

    def _contains_veritas_upgrade(self, package_data):
        return 'VRTS' in package_data['name']

    def _contains_kernel_upgrade(self, package_data):
        return 'kernel' in package_data['name']

    def _contains_serverjre_upgrade(self, package_data):
        return EXTRSERVERJRE_PKG_NAME in package_data['name']

    def _should_include_reboot(self, package_data):
        # TORF-152429: an update in vxvm package requires a restart to reload
        # all the modules
        return self._contains_kernel_upgrade(package_data) or \
               self._contains_serverjre_upgrade(package_data) or \
               self._contains_vxvm_upgrade(package_data)

    def _puppet_being_upgraded(self, package_data):
        return EXTRLITPPUPPET_PKG_NAME in package_data['name']

    def _mcollective_being_upgraded(self, package_data):
        return EXTRLITPMCOLLECTIVE_PKG_NAME in package_data['name']

    def _upgrade_requires_reboot(self, node):
        # assumes the node contains an upgrade object (has been checked before)
        return node.query('upgrade')[0].requires_reboot == 'true'

    def _gen_all_pkg_upgrade_tasks(self, node, puppet_being_upgraded,
                                  mco_being_upgraded,
                                  wait_based_on_puppet, restart_services,
                                  veritas_upg):
        msg1 = 'Update packages on node "%s"' % node.hostname
        upgrade_item = node.query('upgrade')[0]
        t0 = None

        try:
            cluster = node.get_cluster()
            cluster_type = cluster.cluster_type
        except Exception:  # pylint: disable=W0703
            cluster_type = None

        if mco_being_upgraded:
            t0 = self._gen_mco_pkg_upgrade_task(node)
        t1 = CallbackTask(upgrade_item,
                          msg1,
                          self._upgrade_callback_task,
                          node=node.hostname,
                          cluster=cluster_type,
                          veritas_upgrade=veritas_upg,
                          wait_based_on_puppet=wait_based_on_puppet)
        if t0 is not None:
            t1.requires = set([t0])

        t2 = None
        if puppet_being_upgraded:
            t2 = self._gen_mco_restart_task(node)
            t2.requires = set([t1])

        if restart_services:
            self.add_vxvm_upgrade_tag([t0, t1, t2])
        return (t0, t1, t2)

    def _gen_mco_restart_task(self, node):
        msg = 'Restart mcollective on node "%s"' % node.hostname
        command = '/usr/bin/systemctl restart mcollective.service'
        upgrade_item = node.query('upgrade')[0]
        mco_restart_task = CallbackTask(upgrade_item,
                          msg,
                          self._restart_mco_and_wait,
                          node=node.hostname,
                          command={'commands_str': command})
        return mco_restart_task

    def _restart_mco_and_wait(self, callback_api, node, command):
        aerr = "No answer from node %s" % node
        self._execute_rpc_in_callback_task(callback_api,
                                            [node],
                                            YUM_MCO_AGENT,
                                            YUM_SET_STATE_VCS_SERVICES_ACTION,
                                            command,
                                            timeout=7,
                                            allowed_errors=[aerr])
        self.wait_for_mco_connectivity(callback_api, node)

    def _gen_mco_pkg_upgrade_task(self, node):
        msg = 'Update mcollective on node "%s"' % node.hostname
        package = EXTRLITPMCOLLECTIVE_PKG_NAME + " " +\
                  EXTRLITPMCOCOMMON_PKG_NAME
        upgrade_item = node.query('upgrade')[0]
        mco_upgrade_task = CallbackTask(upgrade_item,
                                        msg,
                                        self._upgrade_mco_and_wait,
                                        node=node.hostname,
                                        package={'name': package})
        return mco_upgrade_task

    def _upgrade_mco_and_wait(self, callback_api, node, package):
        aerr = "No answer from node %s" % node
        self._execute_rpc_in_callback_task(callback_api,
                                            [node],
                                            YUM_MCO_AGENT,
                                            YUM_UPGRADE_PACKAGE_ACTION,
                                            package,
                                            timeout=60,
                                            allowed_errors=[aerr])

        self.wait_for_mco_connectivity(callback_api, node)

    def wait_for_mco_connectivity(self, callback_api, node, max_wait=90):
        start_time = self.get_current_time()

        while not self.mco_responding(node):
            if not callback_api.is_running():
                raise PlanStoppedException("Plan execution has been stopped.")

            counter = self.get_current_time() - start_time
            if counter % 5 == 0:
                log.trace.info("Waiting for mcollective on node %s" % node)

            if counter >= max_wait:
                raise CallbackExecutionException(
                            "mcollective has not come up within {0} seconds"
                            .format(max_wait))

            time.sleep(1.0)

        log.trace.info("MCO has come up on %s" % node)

    def _gen_reboot_task(self, node, loose=False, wait_based_on_puppet=True):
        return CallbackTask(node.query('upgrade')[0],
                            'Reboot node "%s"' % node.hostname,
                            self._reboot_node_and_wait,
                            node.hostname,
                            loose,
                            wait_based_on_puppet)

    def _gen_disable_puppet_task(self, node):
        return CallbackTask(node.query('upgrade')[0],
                            'Stop Puppet on node "%s"' \
                                % node.hostname,
                            self._disable_puppet,
                            node.hostname)

    def _gen_enable_puppet_task(self, node):
        return CallbackTask(node.query('upgrade')[0],
                            'Start Puppet on node "%s"' \
                                % node.hostname,
                            self._enable_puppet,
                            node.hostname)

    def _gen_lvm_remove_filter_task(self, node):
        return CallbackTask(node.query('upgrade')[0],
                            'Remove LVM filter on node "%s"' \
                                % node.hostname,
                            self._remove_lvm_filter,
                            node.hostname)

    def _gen_lvm_add_filter_task(self, node):
        return CallbackTask(node.query('upgrade')[0],
                            'Add LVM filter on node "%s"' \
                                % node.hostname,
                            self._add_lvm_filter,
                            node.hostname)

    def _gen_disable_vxvm_boot_task(self, node):
        """
        Create a callback task to disable vxvm-boot.service.

        :param node: The node that vxvm-boot will be disabled on.
        :type node: litp.core.model_manager.QueryItem
        :return: Callback task
        :rtype: CallbackTask object
        """
        return CallbackTask(node.query('upgrade')[0],
                            'Disable vxvm-boot.service on node "%s"'
                            % node.hostname,
                            self._disable_vxvm_boot,
                            node.hostname)

    def _gen_upgrade_vxvm_tasks(self, node, boot_mode):
        puppet_task = self._gen_disable_puppet_task(node)
        vxvm_boot_task = self._gen_disable_vxvm_boot_task(node)
        reboot_task = self._gen_reboot_task(node, loose=True,
                                            wait_based_on_puppet=False)

        # ENM on Rack only requires disable puppet, disable vxvm-boot and
        # reboot
        if boot_mode == 'uefi':
            vxvm_boot_task.requires = set([puppet_task])
            reboot_task.requires = set([vxvm_boot_task])
            return [puppet_task, vxvm_boot_task, reboot_task]
        else:
            lvm_filter_task = self._gen_lvm_remove_filter_task(node)
            dmp_conf_task = CallbackTask(node,
                       'Disable VxDMP on node "%s"' % node.hostname,
                       self.dmp_support_callback_task, node.hostname,
                       enable=False)

            lvm_filter_task.requires = set([puppet_task])
            dmp_conf_task.requires = set([puppet_task, lvm_filter_task])
            vxvm_boot_task.requires = set([dmp_conf_task])
            reboot_task.requires = set([dmp_conf_task, vxvm_boot_task])

            return [puppet_task, lvm_filter_task, dmp_conf_task,
                    vxvm_boot_task, reboot_task]

    def _disable_vxvm_boot(self, callback_api, hostname):
        """
        Disable vxvm-boot.service.

        :param callback_api: Callback API
        :type callback_api: class litp.core.callback_api.CallbackApi
        :param hostname: hostname of node to operate upon
        :type hostname: string
        :return: None
        """
        self._do_vrts_rpc(callback_api, hostname, 'disable_vxvm_boot')

    def _disable_puppet(self, callback_api, hostname):
        self._execute_rpc_in_callback_task(
                                callback_api, [hostname], "core",
                                "safe_stop_puppet",
                                timeout=1800)
        self._execute_rpc_in_callback_task(
                                callback_api, [hostname], "core",
                                "set_chkconfig",
                                {'service_name': 'puppet', 'enable': 'off'})

    def _enable_puppet(self, callback_api, hostname):
        self._execute_rpc_in_callback_task(
                                callback_api, [hostname], "core",
                                "set_chkconfig",
                                {'service_name': 'puppet', 'enable': 'on'})

        call_args = ['service', 'puppet', 'start', '-y']
        callback_api.rpc_application([hostname], call_args)

    def _remove_lvm_filter(self, callback_api, hostname):
        self._lvm_filter_action(callback_api, hostname, 'off')

    def _add_lvm_filter(self, callback_api, hostname):
        self._lvm_filter_action(callback_api, hostname, 'on')

    def _lvm_filter_action(self, callback_api, hostname, action):
        self._execute_rpc_in_callback_task(
            callback_api, [hostname], "dmp", "lvm_filter", {'action': action})
        self._postlvm_filter_checks(callback_api, hostname)

    def _reboot_node_and_wait(self, callback_api, hostname, loose,
                              wait_based_on_puppet=True):
        # LITPCDS-9454 stop puppet before rebooting
        call_args = ['service', 'puppet', 'stop', '-y']
        callback_api.rpc_application([hostname], call_args)

        self._execute_rpc_in_callback_task(
                                callback_api, [hostname], "core", "reboot")
        time_at_reboot = time.time()
        wait_for_node_down(callback_api, [hostname], True)

        wait_for_node_timestamp(callback_api, [hostname], time_at_reboot, True)
        if wait_based_on_puppet:
            PuppetMcoProcessor().enable_puppet([hostname])
            wait_for_node_puppet_applying_catalog_valid(
                callback_api, [hostname], True, loose=loose)
        else:
            self.wait_for_vcs(callback_api, hostname)

        node = callback_api.query('node', hostname=hostname)[0]
        node.query('upgrade')[0].reboot_performed = 'true'

    def _postlvm_filter_checks(self, callback_api, hostname):
        # check pvs, vgs and lvs and check mirate_native
        err_msg = "No root volumes listed in {0}. Please contact your local "\
                "Ericsson support team to prevent volume corruption."
        out, _ = self._execute_rpc_and_get_output(
            callback_api, [hostname], 'lv', 'pvs')
        if not 'vg_root' in out.get(hostname, '').split():
            raise CallbackExecutionException(err_msg.format('pvs'))
        out, _ = self._execute_rpc_and_get_output(
            callback_api, [hostname], 'lv', 'vgs')
        if not 'vg_root' in out.get(hostname, '').split():
            raise CallbackExecutionException(err_msg.format('vgs'))
        lv_root_path = re.compile("/dev/vg_root/vg(.*)_root")
        out, _ = self._execute_rpc_and_get_output(
            callback_api, [hostname], 'lv', 'lvs')
        if not any(lv_root_path.match(res) for res in
                   out.get(hostname, '').split()):
            raise CallbackExecutionException(err_msg.format('lvs'))
        self._execute_rpc_in_callback_task(
            callback_api, [hostname], 'dmp',
            'check_migrate_native_exists_and_remove')

    def _execute_rpc_and_get_output(self, context_api, nodes, agent, action,
                                    action_kwargs=None, timeout=None,
                                    tolerate_warnings=False):
        if agent == 'yum' and action == 'upgrade_all_packages':
            processor = YumErrCheckRpcCommandProcessor()
        else:
            if tolerate_warnings:
                processor = RpcCommandOutputProcessor()
            else:
                processor = RpcCommandOutputNoStderrProcessor()

        try:
            return processor.execute_rpc_and_process_result(
             context_api, nodes, agent, action, action_kwargs, timeout=timeout)
        except RpcExecutionException as e:
            raise PluginError(e)

    def _execute_rpc_in_callback_task(self, cb_api, nodes, agent, action,
                                      action_kwargs=None, timeout=None,
                                      allowed_errors=None):
        try:
            bcp = RpcCommandProcessorBase()
            _, errors = bcp.execute_rpc_and_process_result(
                    cb_api, nodes, agent, action, action_kwargs, timeout)
        except RpcExecutionException as e:
            raise CallbackExecutionException(e)

        if errors:
            clean_errors = [str(err.strip()) for err in reduce_errs(errors)]
            skip_errors = False
            if allowed_errors and \
               all(any(err == aerr for aerr in allowed_errors)
                   for err in clean_errors):
                skip_errors = True
            if not skip_errors:
                raise CallbackExecutionException(','.join(clean_errors))

    def _execute_rpc_dmp_command(self, cb_api, nodes, agent, action,
                                      action_kwargs=None, timeout=None,
                                      retries=10):
        for ntime in xrange(retries + 1):
            log.trace.debug("Running DMP command for {0} time out of {1}".
                            format(ntime + 1, retries + 1))
            try:
                bcp = NoStandardErrorRpcCommandProcessor()
                _, errors = bcp.execute_rpc_and_process_result(
                    cb_api, nodes, agent, action, action_kwargs, timeout
                                                               )
            except RpcExecutionException as e:
                raise CallbackExecutionException(e)
            if errors and not self._msg_to_ignore_in_errs(errors,
                                                          DMP_MSG_to_IGNORE):
                # an actual error
                raise CallbackExecutionException(','.join(reduce_errs(errors)))
            elif self._msg_to_ignore_in_errs(errors, DMP_MSG_to_IGNORE):
                # retry after a couple of seconds
                time.sleep(2)
            elif not errors:
                # nothing bad happened, no need to retry the command
                break
        if errors:
            raise CallbackExecutionException("Attempted {0} retries, but "
            "received this error: {1}".format(retries,
                                              ','.join(reduce_errs(errors))))

    def _msg_to_ignore_in_errs(self, errors, ignore_str):
        # helper method used by _execute_rpc_dmp_command. Will return True if
        # the message to ignore is present in any of the errors
        if not ignore_str:
            # nothing to ignore, nothing to do
            return False
        # errors is a dictionary of lists, so flatten it into a list of str
        return any(ignore_str in err for err in
                   itertools.chain.from_iterable(errors.itervalues()))

    def _is_yum_pending_error(self, error_dict, node):
        # Returns True if the error dictionary consists of exactly
        # one error from the specifiied node, and the error is one that
        # says unfinished yum transactions exist.
        if error_dict.keys() == [node]:
            errors = error_dict[node]
            if len(errors) == 1 and YUM_PENDING_ERROR in errors[0]:
                return True
        return False

    def _has_veritas_upgrade_errors(self, results, node):
        # returns True if the yum transaction found a Veritas error that
        # requires a node reboot. It will also filter out that error
        if results and VERITAS_UG_ERR in results.get(node, []):
            results[node] = [e for e in results[node] if e != VERITAS_UG_ERR]
            if not results[node]:
                del results[node]
            return True
        return False

    def _upgrade_callback_task(self, cb_api, node, cluster, veritas_upgrade,
                                                       wait_based_on_puppet):
        log.trace.info(
            "A command to upgrade the system will be run on node \"{0}\"."
            " To check"
            " the result of this operation log onto the node and run the"
            " command 'yum history info'".format(node))
        _, error_dict = self._execute_rpc_and_get_output(cb_api,
                [node],
                'yum',
                'upgrade_all_packages',
                timeout=1860,    # One minute more than value in DDL
                tolerate_warnings=True
        )
        veritas_err_msg = "Veritas drivers not loaded after VRTSvxvm upgrade."\
            "Node {0} will be rebooted to load them".format(node)
        if self._has_veritas_upgrade_errors(error_dict, node):
            log.trace.info(veritas_err_msg)
            self._reboot_node_and_wait(cb_api, node, False,
                                       wait_based_on_puppet)
        if error_dict:
            if self._is_yum_pending_error(error_dict, node):
                log.trace.info("An incomplete yum transaction exists; "
                               "attempting to complete it.")
                _, error_dict = self._execute_rpc_and_get_output(cb_api,
                        [node],
                        'yum',
                        'complete_transaction',
                        timeout=1860,
                        tolerate_warnings=True
                )
                if error_dict:
                    log.trace.debug("yum-complete-transaction failed.")
                else:
                    log.trace.info("yum-complete-transaction worked. " \
                                    "Retrying upgrade.")
                    _, error_dict = self._execute_rpc_and_get_output(cb_api,
                            [node],
                            'yum',
                            'upgrade_all_packages',
                            timeout=1860,
                            tolerate_warnings=True
                    )
                    if self._has_veritas_upgrade_errors(error_dict, node):
                        log.trace.info(veritas_err_msg)
                        self._reboot_node_and_wait(cb_api, node, False,
                                                   wait_based_on_puppet)
            else:
                # TORF-480317 MCO can report a false negative in some cases
                # so we try again with a shorter timeout to check that there
                # are no packages marked for update
                log.trace.info("Failed to upgrade all packages. Trying again "
                               "to check if yum completed successfully")
                _, error_dict = self._execute_rpc_and_get_output(cb_api,
                        [node],
                        'yum',
                        'upgrade_all_packages',
                        timeout=60,
                        tolerate_warnings=True
                )
            if error_dict:
                raise CallbackExecutionException(
                        ','.join(reduce_errs(error_dict)))

        self.remove_vrts_debuginfo(cb_api, node, cluster, veritas_upgrade)

    def remove_vrts_debuginfo(self, cb_api, node, cluster, veritas_upgrade):
        pkgs = ['VRTSvxvm', 'VRTSaslapm']
        greps = ["/opt", ".debug"]
        log.trace.info('Removing VRTS debuginfo files')
        if cluster == 'sfha' and veritas_upgrade:
            for pkg in pkgs:
                rpm_contents = vcs_ext.VcsExtension.get_package_file_info(
                                                                       cb_api,
                                                                       node,
                                                                       pkg,
                                                                       greps)
                vcs_ext.VcsExtension.remove_unused_vrts_debug_files(cb_api,
                                                                node,
                                                                rpm_contents)

    def get_current_time(self):
        return int(time.time())

    def wait_for_vcs(self, callback_api, hostname):
        max_wait = 1800   # 30mins
        epoch = self.get_current_time()

        while not self.vcs_responding(hostname):
            if not callback_api.is_running():
                raise PlanStoppedException("Plan execution has been stopped.")

            counter = self.get_current_time() - epoch
            if counter % 60 == 0:
                log.trace.info("Waiting for VCS on node %s" % hostname)

            if counter >= max_wait:
                raise CallbackExecutionException(
                    "VCS has not come up within {0} seconds".format(max_wait))

            time.sleep(1.0)

        log.trace.info("VCS has come up on %s" % hostname)

    def vcs_responding(self, hostname):
        result = run_rpc_command([hostname], "yum", "vcs_status")

        if not result[hostname]['data'] or \
           result[hostname]['errors']:
            return False

        return not bool(result[hostname]['data']['status'])

    def mco_responding(self, hostname):
        result = run_rpc_command([hostname], "rpcutil", "ping", timeout=10)

        if "pong" in result[hostname]['data']:
            return True
        return False
