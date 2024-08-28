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
            if node == 'node1':
                # VRTSvxvm, no kernel
                result[node] = {'data': {'out': "VRTSvxvm 7.3.1.3308 RHEL7 x86_64\nbind-libs 9.8.2 0.17.rc1.el6_4.6 x86_64\nbind-utils 9.8.2 0.17.rc1.el6_4.6 x86_64\nchkconfig 1.3.49.3 2.el6_4.1 x86_64\ncoreutils 8.4 19.el6_4.2 x86_64\ncoreutils-libs 8.4 19.el6_4.2 x86_64\ncurl 7.19.7 37.el6_4 x86_64\ndb4 4.7.25 18.el6_4 x86_64\ndb4-utils 4.7.25 18.el6_4 x86_64\ndbus-glib 0.86 6.el6_4 x86_64\ndevice-mapper 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-event 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-event-libs 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-libs 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-multipath 0.4.9 64.el6_4.2 x86_64\ndevice-mapper-multipath-libs 0.4.9 64.el6_4.2 x86_64\ndhclient 4.1.1 34.P1.el6_4.1 x86_64\ne2fsprogs 1.41.12 14.el6_4.4 x86_64\ne2fsprogs-libs 1.41.12 14.el6_4.4 x86_64\nethtool 3.5 1.1.el6_4 x86_64\nglibc-common 2.12 1.107.el6_4.5 x86_64\ngnupg2 2.0.14 6.el6_4 x86_64\ngnutls 2.8.5 10.el6_4.2 x86_64\ngnutls-utils 2.8.5 10.el6_4.2 x86_64\ngzip 1.3.12 19.el6_4 x86_64\ninitscripts 9.03.38 1.el6_4.2 x86_64\nipmitool 1.8.11 14.el6_4.1 x86_64\niputils 20071127 17.el6_4.2 x86_64\nkexec-tools 2.0.0 258.el6_4.2 x86_64\nkpartx 0.4.9 64.el6_4.2 x86_64\nkrb5-libs 1.10.3 10.el6_4.6 x86_64\nlibblkid 2.17.2 12.9.el6_4.3 x86_64\nlibcgroup 0.37 7.2.el6_4 x86_64\nlibcom_err 1.41.12 14.el6_4.4 x86_64\nlibcurl 7.19.7 37.el6_4 x86_64\nlibgcrypt 1.4.5 11.el6_4 x86_64\nlibgudev1 147 2.46.el6_4.2 x86_64\nlibnl 1.1.4 1.el6_4 x86_64\nlibselinux 2.0.94 5.3.el6_4.1 x86_64\nlibselinux-python 2.0.94 5.3.el6_4.1 x86_64\nlibselinux-ruby 2.0.94 5.3.el6_4.1 x86_64\nlibselinux-utils 2.0.94 5.3.el6_4.1 x86_64\nlibss 1.41.12 14.el6_4.4 x86_64\nlibtirpc 0.2.1 6.el6_4 x86_64\nlibudev 147 2.46.el6_4.2 x86_64\nlibuuid 2.17.2 12.9.el6_4.3 x86_64\nlibvirt-client 0.10.2 18.el6_4.15 x86_64\nlibvirt-python 0.10.2 18.el6_4.15 x86_64\nlibxml2 2.7.6 12.el6_4.1 x86_64\nlibxml2-python 2.7.6 12.el6_4.1 x86_64\nlvm2 2.02.98 9.el6_4.3 x86_64\nlvm2-libs 2.02.98 9.el6_4.3 x86_64\nmdadm 3.2.5 4.el6_4.3 x86_64\nmodule-init-tools 3.9 21.el6_4 x86_64\nmysql-libs 5.1.69 1.el6_4 x86_64\nnet-snmp 5.5 44.el6_4.4 x86_64\nnet-snmp-libs 5.5 44.el6_4.4 x86_64\nnet-snmp-utils 5.5 44.el6_4.4 x86_64\nnspr 4.9.5 2.el6_4 x86_64\nnss 3.14.3 5.el6_4 x86_64\nnss-softokn 3.14.3 3.el6_4 x86_64\nnss-sysinit 3.14.3 5.el6_4 x86_64\nnss-tools 3.14.3 5.el6_4 x86_64\nnss-util 3.14.3 3.el6_4 x86_64\nopenldap 2.4.23 32.el6_4.1 x86_64\nopenssl 1.0.0 27.el6_4.2 x86_64\nperl 5.10.1 131.el6_4 x86_64\nperl-Module-Pluggable 3.90 131.el6_4 x86_64\nperl-Pod-Escapes 1.04 131.el6_4 x86_64\nperl-Pod-Simple 3.13 131.el6_4 x86_64\nperl-libs 5.10.1 131.el6_4 x86_64\nperl-version 0.77 131.el6_4 x86_64\npixman 0.26.2 5.el6_4 x86_64\npolkit 0.96 5.el6_4 x86_64\npython 2.6.6 37.el6_4 x86_64\npython-dmidecode 3.10.13 3.el6_4 x86_64\npython-libs 2.6.6 37.el6_4 x86_64\npython-rhsm 1.8.17 1.el6_4 x86_64\nqemu-img 0.12.1.2 2.355.el6_4.9 x86_64\nqemu-kvm 0.12.1.2 2.355.el6_4.9 x86_64\nrhn-check 1.0.0.1 8.el6 noarch\nrhn-client-tools 1.0.0.1 8.el6 noarch\nrhn-setup 1.0.0.1 8.el6 noarch\nrhnlib 2.5.22 15.el6 noarch\nrsyslog 5.8.10 7.el6_4 x86_64\nruby 1.8.7.352 13.el6_4 x86_64\nruby-irb 1.8.7.352 13.el6_4 x86_64\nruby-libs 1.8.7.352 13.el6_4 x86_64\nruby-rdoc 1.8.7.352 13.el6_4 x86_64\nselinux-policy 3.7.19 195.el6_4.18 noarch\nselinux-policy-targeted 3.7.19 195.el6_4.18 noarch\nsetup 2.8.14 20.el6_4.1 noarch\nspice-server 0.12.0 12.el6_4.5 x86_64\nsubscription-manager 1.8.22 1.el6_4 x86_64\nudev 147 2.46.el6_4.2 x86_64\nupstart 0.6.5 12.el6_4.1 x86_64\nutil-linux-ng 2.17.2 12.9.el6_4.3 x86_64\nyum-rhn-plugin 0.9.1 49.el6 noarch",
                                     'status': 0,
                                     'err': ''},
                            'errors': ''}
                # no VRTSvxvm, kernel
            elif node == 'node2':
                result[node] = {'data': {'out': "bind-libs 9.8.2 0.17.rc1.el6_4.6 x86_64\nbind-utils 9.8.2 0.17.rc1.el6_4.6 x86_64\nchkconfig 1.3.49.3 2.el6_4.1 x86_64\ncoreutils 8.4 19.el6_4.2 x86_64\ncoreutils-libs 8.4 19.el6_4.2 x86_64\ncurl 7.19.7 37.el6_4 x86_64\ndb4 4.7.25 18.el6_4 x86_64\ndb4-utils 4.7.25 18.el6_4 x86_64\ndbus-glib 0.86 6.el6_4 x86_64\ndevice-mapper 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-event 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-event-libs 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-libs 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-multipath 0.4.9 64.el6_4.2 x86_64\ndevice-mapper-multipath-libs 0.4.9 64.el6_4.2 x86_64\ndhclient 4.1.1 34.P1.el6_4.1 x86_64\ne2fsprogs 1.41.12 14.el6_4.4 x86_64\ne2fsprogs-libs 1.41.12 14.el6_4.4 x86_64\nethtool 3.5 1.1.el6_4 x86_64\nglibc-common 2.12 1.107.el6_4.5 x86_64\ngnupg2 2.0.14 6.el6_4 x86_64\ngnutls 2.8.5 10.el6_4.2 x86_64\ngnutls-utils 2.8.5 10.el6_4.2 x86_64\ngzip 1.3.12 19.el6_4 x86_64\ninitscripts 9.03.38 1.el6_4.2 x86_64\nipmitool 1.8.11 14.el6_4.1 x86_64\niputils 20071127 17.el6_4.2 x86_64\nkernel 2.6.32 358.32.3.el6 x86_64\nkexec-tools 2.0.0 258.el6_4.2 x86_64\nkpartx 0.4.9 64.el6_4.2 x86_64\nkrb5-libs 1.10.3 10.el6_4.6 x86_64\nlibblkid 2.17.2 12.9.el6_4.3 x86_64\nlibcgroup 0.37 7.2.el6_4 x86_64\nlibcom_err 1.41.12 14.el6_4.4 x86_64\nlibcurl 7.19.7 37.el6_4 x86_64\nlibgcrypt 1.4.5 11.el6_4 x86_64\nlibgudev1 147 2.46.el6_4.2 x86_64\nlibnl 1.1.4 1.el6_4 x86_64\nlibselinux 2.0.94 5.3.el6_4.1 x86_64\nlibselinux-python 2.0.94 5.3.el6_4.1 x86_64\nlibselinux-ruby 2.0.94 5.3.el6_4.1 x86_64\nlibselinux-utils 2.0.94 5.3.el6_4.1 x86_64\nlibss 1.41.12 14.el6_4.4 x86_64\nlibtirpc 0.2.1 6.el6_4 x86_64\nlibudev 147 2.46.el6_4.2 x86_64\nlibuuid 2.17.2 12.9.el6_4.3 x86_64\nlibvirt-client 0.10.2 18.el6_4.15 x86_64\nlibvirt-python 0.10.2 18.el6_4.15 x86_64\nlibxml2 2.7.6 12.el6_4.1 x86_64\nlibxml2-python 2.7.6 12.el6_4.1 x86_64\nlvm2 2.02.98 9.el6_4.3 x86_64\nlvm2-libs 2.02.98 9.el6_4.3 x86_64\nmdadm 3.2.5 4.el6_4.3 x86_64\nmodule-init-tools 3.9 21.el6_4 x86_64\nmysql-libs 5.1.69 1.el6_4 x86_64\nnet-snmp 5.5 44.el6_4.4 x86_64\nnet-snmp-libs 5.5 44.el6_4.4 x86_64\nnet-snmp-utils 5.5 44.el6_4.4 x86_64\nnspr 4.9.5 2.el6_4 x86_64\nnss 3.14.3 5.el6_4 x86_64\nnss-softokn 3.14.3 3.el6_4 x86_64\nnss-sysinit 3.14.3 5.el6_4 x86_64\nnss-tools 3.14.3 5.el6_4 x86_64\nnss-util 3.14.3 3.el6_4 x86_64\nopenldap 2.4.23 32.el6_4.1 x86_64\nopenssl 1.0.0 27.el6_4.2 x86_64\nperl 5.10.1 131.el6_4 x86_64\nperl-Module-Pluggable 3.90 131.el6_4 x86_64\nperl-Pod-Escapes 1.04 131.el6_4 x86_64\nperl-Pod-Simple 3.13 131.el6_4 x86_64\nperl-libs 5.10.1 131.el6_4 x86_64\nperl-version 0.77 131.el6_4 x86_64\npixman 0.26.2 5.el6_4 x86_64\npolkit 0.96 5.el6_4 x86_64\npython 2.6.6 37.el6_4 x86_64\npython-dmidecode 3.10.13 3.el6_4 x86_64\npython-libs 2.6.6 37.el6_4 x86_64\npython-rhsm 1.8.17 1.el6_4 x86_64\nqemu-img 0.12.1.2 2.355.el6_4.9 x86_64\nqemu-kvm 0.12.1.2 2.355.el6_4.9 x86_64\nrhn-check 1.0.0.1 8.el6 noarch\nrhn-client-tools 1.0.0.1 8.el6 noarch\nrhn-setup 1.0.0.1 8.el6 noarch\nrhnlib 2.5.22 15.el6 noarch\nrsyslog 5.8.10 7.el6_4 x86_64\nruby 1.8.7.352 13.el6_4 x86_64\nruby-irb 1.8.7.352 13.el6_4 x86_64\nruby-libs 1.8.7.352 13.el6_4 x86_64\nruby-rdoc 1.8.7.352 13.el6_4 x86_64\nselinux-policy 3.7.19 195.el6_4.18 noarch\nselinux-policy-targeted 3.7.19 195.el6_4.18 noarch\nsetup 2.8.14 20.el6_4.1 noarch\nspice-server 0.12.0 12.el6_4.5 x86_64\nsubscription-manager 1.8.22 1.el6_4 x86_64\nudev 147 2.46.el6_4.2 x86_64\nupstart 0.6.5 12.el6_4.1 x86_64\nutil-linux-ng 2.17.2 12.9.el6_4.3 x86_64\nyum-rhn-plugin 0.9.1 49.el6 noarch",
                                     'status': 0,
                                     'err': ''},
                            'errors': ''}
            else:
                # VRTSvxvm, kernel
                result[node] = {'data': {'out': "VRTSvxvm 7.3.1.3308 RHEL7 x86_64\nbind-libs 9.8.2 0.17.rc1.el6_4.6 x86_64\nbind-utils 9.8.2 0.17.rc1.el6_4.6 x86_64\nchkconfig 1.3.49.3 2.el6_4.1 x86_64\ncoreutils 8.4 19.el6_4.2 x86_64\ncoreutils-libs 8.4 19.el6_4.2 x86_64\ncurl 7.19.7 37.el6_4 x86_64\ndb4 4.7.25 18.el6_4 x86_64\ndb4-utils 4.7.25 18.el6_4 x86_64\ndbus-glib 0.86 6.el6_4 x86_64\ndevice-mapper 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-event 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-event-libs 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-libs 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-multipath 0.4.9 64.el6_4.2 x86_64\ndevice-mapper-multipath-libs 0.4.9 64.el6_4.2 x86_64\ndhclient 4.1.1 34.P1.el6_4.1 x86_64\ne2fsprogs 1.41.12 14.el6_4.4 x86_64\ne2fsprogs-libs 1.41.12 14.el6_4.4 x86_64\nethtool 3.5 1.1.el6_4 x86_64\nglibc-common 2.12 1.107.el6_4.5 x86_64\ngnupg2 2.0.14 6.el6_4 x86_64\ngnutls 2.8.5 10.el6_4.2 x86_64\ngnutls-utils 2.8.5 10.el6_4.2 x86_64\ngzip 1.3.12 19.el6_4 x86_64\ninitscripts 9.03.38 1.el6_4.2 x86_64\nipmitool 1.8.11 14.el6_4.1 x86_64\niputils 20071127 17.el6_4.2 x86_64\nkernel 2.6.32 358.32.3.el6 x86_64\nkexec-tools 2.0.0 258.el6_4.2 x86_64\nkpartx 0.4.9 64.el6_4.2 x86_64\nkrb5-libs 1.10.3 10.el6_4.6 x86_64\nlibblkid 2.17.2 12.9.el6_4.3 x86_64\nlibcgroup 0.37 7.2.el6_4 x86_64\nlibcom_err 1.41.12 14.el6_4.4 x86_64\nlibcurl 7.19.7 37.el6_4 x86_64\nlibgcrypt 1.4.5 11.el6_4 x86_64\nlibgudev1 147 2.46.el6_4.2 x86_64\nlibnl 1.1.4 1.el6_4 x86_64\nlibselinux 2.0.94 5.3.el6_4.1 x86_64\nlibselinux-python 2.0.94 5.3.el6_4.1 x86_64\nlibselinux-ruby 2.0.94 5.3.el6_4.1 x86_64\nlibselinux-utils 2.0.94 5.3.el6_4.1 x86_64\nlibss 1.41.12 14.el6_4.4 x86_64\nlibtirpc 0.2.1 6.el6_4 x86_64\nlibudev 147 2.46.el6_4.2 x86_64\nlibuuid 2.17.2 12.9.el6_4.3 x86_64\nlibvirt-client 0.10.2 18.el6_4.15 x86_64\nlibvirt-python 0.10.2 18.el6_4.15 x86_64\nlibxml2 2.7.6 12.el6_4.1 x86_64\nlibxml2-python 2.7.6 12.el6_4.1 x86_64\nlvm2 2.02.98 9.el6_4.3 x86_64\nlvm2-libs 2.02.98 9.el6_4.3 x86_64\nmdadm 3.2.5 4.el6_4.3 x86_64\nmodule-init-tools 3.9 21.el6_4 x86_64\nmysql-libs 5.1.69 1.el6_4 x86_64\nnet-snmp 5.5 44.el6_4.4 x86_64\nnet-snmp-libs 5.5 44.el6_4.4 x86_64\nnet-snmp-utils 5.5 44.el6_4.4 x86_64\nnspr 4.9.5 2.el6_4 x86_64\nnss 3.14.3 5.el6_4 x86_64\nnss-softokn 3.14.3 3.el6_4 x86_64\nnss-sysinit 3.14.3 5.el6_4 x86_64\nnss-tools 3.14.3 5.el6_4 x86_64\nnss-util 3.14.3 3.el6_4 x86_64\nopenldap 2.4.23 32.el6_4.1 x86_64\nopenssl 1.0.0 27.el6_4.2 x86_64\nperl 5.10.1 131.el6_4 x86_64\nperl-Module-Pluggable 3.90 131.el6_4 x86_64\nperl-Pod-Escapes 1.04 131.el6_4 x86_64\nperl-Pod-Simple 3.13 131.el6_4 x86_64\nperl-libs 5.10.1 131.el6_4 x86_64\nperl-version 0.77 131.el6_4 x86_64\npixman 0.26.2 5.el6_4 x86_64\npolkit 0.96 5.el6_4 x86_64\npython 2.6.6 37.el6_4 x86_64\npython-dmidecode 3.10.13 3.el6_4 x86_64\npython-libs 2.6.6 37.el6_4 x86_64\npython-rhsm 1.8.17 1.el6_4 x86_64\nqemu-img 0.12.1.2 2.355.el6_4.9 x86_64\nqemu-kvm 0.12.1.2 2.355.el6_4.9 x86_64\nrhn-check 1.0.0.1 8.el6 noarch\nrhn-client-tools 1.0.0.1 8.el6 noarch\nrhn-setup 1.0.0.1 8.el6 noarch\nrhnlib 2.5.22 15.el6 noarch\nrsyslog 5.8.10 7.el6_4 x86_64\nruby 1.8.7.352 13.el6_4 x86_64\nruby-irb 1.8.7.352 13.el6_4 x86_64\nruby-libs 1.8.7.352 13.el6_4 x86_64\nruby-rdoc 1.8.7.352 13.el6_4 x86_64\nselinux-policy 3.7.19 195.el6_4.18 noarch\nselinux-policy-targeted 3.7.19 195.el6_4.18 noarch\nsetup 2.8.14 20.el6_4.1 noarch\nspice-server 0.12.0 12.el6_4.5 x86_64\nsubscription-manager 1.8.22 1.el6_4 x86_64\nudev 147 2.46.el6_4.2 x86_64\nupstart 0.6.5 12.el6_4.1 x86_64\nutil-linux-ng 2.17.2 12.9.el6_4.3 x86_64\nyum-rhn-plugin 0.9.1 49.el6 noarch",
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
