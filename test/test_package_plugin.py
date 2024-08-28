##############################################################################
# COPYRIGHT Ericsson AB 2013
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

import mock
import time
from unittest import TestCase
from nose.tools import nottest
from mock import Mock, MagicMock, call, patch
from litp.core.execution_manager import ExecutionManager, \
    CallbackExecutionException
from litp.extensions.core_extension import CoreExtension
from litp.core.model_manager import ModelManager
from litp.core.puppet_manager import PuppetManager
from litp.core.plugin_manager import PluginManager
from litp.core.model_manager import QueryItem

from package_plugin.package_plugin import PackagePlugin, \
    DMP_MSG_to_IGNORE, VERITAS_UG_ERR, YUM_PENDING_ERROR, \
    YumErrCheckRpcCommandProcessor, EXTRSERVERJRE_PKG_NAME, \
    EXTRLITPMCOLLECTIVE_PKG_NAME, EXTRLITPMCOCOMMON_PKG_NAME, \
    YUM_MCO_AGENT, YUM_UPGRADE_PACKAGE_ACTION, \
    YUM_SET_STATE_VCS_SERVICES_ACTION
from package_extension.package_extension import PackageExtension
from litp.core.plugin_context_api import PluginApiContext
from litp.core.callback_api import CallbackApi
from litp.core.execution_manager import ConfigTask, PlanStoppedException
from litp.core.rpc_commands import RpcExecutionException
from litp.core.plugin import PluginError
from litp.core.model_type import ItemType, Property, PropertyType
from litp.core.model_type import Child
from litp.core.model_type import Collection
from litp.core.validators import ValidationError

mco_output_get_pkgs_withkernel = {'node1': {
    "errors": "",
    "data": {
      "status": 0,
      "err": "",
      "out": "bind-libs 9.8.2 0.17.rc1.el6_4.6 x86_64\nbind-utils 9.8.2 0.17.rc1.el6_4.6 x86_64\nchkconfig 1.3.49.3 2.el6_4.1 x86_64\ncoreutils 8.4 19.el6_4.2 x86_64\ncoreutils-libs 8.4 19.el6_4.2 x86_64\ncurl 7.19.7 37.el6_4 x86_64\ndb4 4.7.25 18.el6_4 x86_64\ndb4-utils 4.7.25 18.el6_4 x86_64\ndbus-glib 0.86 6.el6_4 x86_64\ndevice-mapper 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-event 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-event-libs 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-libs 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-multipath 0.4.9 64.el6_4.2 x86_64\ndevice-mapper-multipath-libs 0.4.9 64.el6_4.2 x86_64\ndhclient 4.1.1 34.P1.el6_4.1 x86_64\ne2fsprogs 1.41.12 14.el6_4.4 x86_64\ne2fsprogs-libs 1.41.12 14.el6_4.4 x86_64\nethtool 3.5 1.1.el6_4 x86_64\nglibc-common 2.12 1.107.el6_4.5 x86_64\ngnupg2 2.0.14 6.el6_4 x86_64\ngnutls 2.8.5 10.el6_4.2 x86_64\ngnutls-utils 2.8.5 10.el6_4.2 x86_64\ngzip 1.3.12 19.el6_4 x86_64\ninitscripts 9.03.38 1.el6_4.2 x86_64\nipmitool 1.8.11 14.el6_4.1 x86_64\niputils 20071127 17.el6_4.2 x86_64\nkernel 2.6.32 358.32.3.el6 x86_64\nkexec-tools 2.0.0 258.el6_4.2 x86_64\nkpartx 0.4.9 64.el6_4.2 x86_64\nkrb5-libs 1.10.3 10.el6_4.6 x86_64\nlibblkid 2.17.2 12.9.el6_4.3 x86_64\nlibcgroup 0.37 7.2.el6_4 x86_64\nlibcom_err 1.41.12 14.el6_4.4 x86_64\nlibcurl 7.19.7 37.el6_4 x86_64\nlibgcrypt 1.4.5 11.el6_4 x86_64\nlibgudev1 147 2.46.el6_4.2 x86_64\nlibnl 1.1.4 1.el6_4 x86_64\nlibselinux 2.0.94 5.3.el6_4.1 x86_64\nlibselinux-python 2.0.94 5.3.el6_4.1 x86_64\nlibselinux-ruby 2.0.94 5.3.el6_4.1 x86_64\nlibselinux-utils 2.0.94 5.3.el6_4.1 x86_64\nlibss 1.41.12 14.el6_4.4 x86_64\nlibtirpc 0.2.1 6.el6_4 x86_64\nlibudev 147 2.46.el6_4.2 x86_64\nlibuuid 2.17.2 12.9.el6_4.3 x86_64\nlibvirt-client 0.10.2 18.el6_4.15 x86_64\nlibvirt-python 0.10.2 18.el6_4.15 x86_64\nlibxml2 2.7.6 12.el6_4.1 x86_64\nlibxml2-python 2.7.6 12.el6_4.1 x86_64\nlvm2 2.02.98 9.el6_4.3 x86_64\nlvm2-libs 2.02.98 9.el6_4.3 x86_64\nmdadm 3.2.5 4.el6_4.3 x86_64\nmodule-init-tools 3.9 21.el6_4 x86_64\nmysql-libs 5.1.69 1.el6_4 x86_64\nnet-snmp 5.5 44.el6_4.4 x86_64\nnet-snmp-libs 5.5 44.el6_4.4 x86_64\nnet-snmp-utils 5.5 44.el6_4.4 x86_64\nnspr 4.9.5 2.el6_4 x86_64\nnss 3.14.3 5.el6_4 x86_64\nnss-softokn 3.14.3 3.el6_4 x86_64\nnss-sysinit 3.14.3 5.el6_4 x86_64\nnss-tools 3.14.3 5.el6_4 x86_64\nnss-util 3.14.3 3.el6_4 x86_64\nopenldap 2.4.23 32.el6_4.1 x86_64\nopenssl 1.0.0 27.el6_4.2 x86_64\nperl 5.10.1 131.el6_4 x86_64\nperl-Module-Pluggable 3.90 131.el6_4 x86_64\nperl-Pod-Escapes 1.04 131.el6_4 x86_64\nperl-Pod-Simple 3.13 131.el6_4 x86_64\nperl-libs 5.10.1 131.el6_4 x86_64\nperl-version 0.77 131.el6_4 x86_64\npixman 0.26.2 5.el6_4 x86_64\npolkit 0.96 5.el6_4 x86_64\npython 2.6.6 37.el6_4 x86_64\npython-dmidecode 3.10.13 3.el6_4 x86_64\npython-libs 2.6.6 37.el6_4 x86_64\npython-rhsm 1.8.17 1.el6_4 x86_64\nqemu-img 0.12.1.2 2.355.el6_4.9 x86_64\nqemu-kvm 0.12.1.2 2.355.el6_4.9 x86_64\nrhn-check 1.0.0.1 8.el6 noarch\nrhn-client-tools 1.0.0.1 8.el6 noarch\nrhn-setup 1.0.0.1 8.el6 noarch\nrhnlib 2.5.22 15.el6 noarch\nrsyslog 5.8.10 7.el6_4 x86_64\nruby 1.8.7.352 13.el6_4 x86_64\nruby-irb 1.8.7.352 13.el6_4 x86_64\nruby-libs 1.8.7.352 13.el6_4 x86_64\nruby-rdoc 1.8.7.352 13.el6_4 x86_64\nselinux-policy 3.7.19 195.el6_4.18 noarch\nselinux-policy-targeted 3.7.19 195.el6_4.18 noarch\nsetup 2.8.14 20.el6_4.1 noarch\nspice-server 0.12.0 12.el6_4.5 x86_64\nsubscription-manager 1.8.22 1.el6_4 x86_64\nudev 147 2.46.el6_4.2 x86_64\nupstart 0.6.5 12.el6_4.1 x86_64\nutil-linux-ng 2.17.2 12.9.el6_4.3 x86_64\nyum-rhn-plugin 0.9.1 49.el6 noarch"
    },
  }}

mco_output_get_pkgs_withoutkernel = {'node1': {
    "errors": "",
    "data": {
      "status": 0,
      "err": "",
      "out": "bind-libs 9.8.2 0.17.rc1.el6_4.6 x86_64\nbind-utils 9.8.2 0.17.rc1.el6_4.6 x86_64\nchkconfig 1.3.49.3 2.el6_4.1 x86_64\ncoreutils 8.4 19.el6_4.2 x86_64\ncoreutils-libs 8.4 19.el6_4.2 x86_64\ncurl 7.19.7 37.el6_4 x86_64\ndb4 4.7.25 18.el6_4 x86_64\ndb4-utils 4.7.25 18.el6_4 x86_64\ndbus-glib 0.86 6.el6_4 x86_64\ndevice-mapper 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-event 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-event-libs 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-libs 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-multipath 0.4.9 64.el6_4.2 x86_64\ndevice-mapper-multipath-libs 0.4.9 64.el6_4.2 x86_64\ndhclient 4.1.1 34.P1.el6_4.1 x86_64\ne2fsprogs 1.41.12 14.el6_4.4 x86_64\ne2fsprogs-libs 1.41.12 14.el6_4.4 x86_64\nethtool 3.5 1.1.el6_4 x86_64\nglibc-common 2.12 1.107.el6_4.5 x86_64\ngnupg2 2.0.14 6.el6_4 x86_64\ngnutls 2.8.5 10.el6_4.2 x86_64\ngnutls-utils 2.8.5 10.el6_4.2 x86_64\ngzip 1.3.12 19.el6_4 x86_64\ninitscripts 9.03.38 1.el6_4.2 x86_64\nipmitool 1.8.11 14.el6_4.1 x86_64\niputils 20071127 17.el6_4.2 x86_64\nkexec-tools 2.0.0 258.el6_4.2 x86_64\nkpartx 0.4.9 64.el6_4.2 x86_64\nkrb5-libs 1.10.3 10.el6_4.6 x86_64\nlibblkid 2.17.2 12.9.el6_4.3 x86_64\nlibcgroup 0.37 7.2.el6_4 x86_64\nlibcom_err 1.41.12 14.el6_4.4 x86_64\nlibcurl 7.19.7 37.el6_4 x86_64\nlibgcrypt 1.4.5 11.el6_4 x86_64\nlibgudev1 147 2.46.el6_4.2 x86_64\nlibnl 1.1.4 1.el6_4 x86_64\nlibselinux 2.0.94 5.3.el6_4.1 x86_64\nlibselinux-python 2.0.94 5.3.el6_4.1 x86_64\nlibselinux-ruby 2.0.94 5.3.el6_4.1 x86_64\nlibselinux-utils 2.0.94 5.3.el6_4.1 x86_64\nlibss 1.41.12 14.el6_4.4 x86_64\nlibtirpc 0.2.1 6.el6_4 x86_64\nlibudev 147 2.46.el6_4.2 x86_64\nlibuuid 2.17.2 12.9.el6_4.3 x86_64\nlibvirt-client 0.10.2 18.el6_4.15 x86_64\nlibvirt-python 0.10.2 18.el6_4.15 x86_64\nlibxml2 2.7.6 12.el6_4.1 x86_64\nlibxml2-python 2.7.6 12.el6_4.1 x86_64\nlvm2 2.02.98 9.el6_4.3 x86_64\nlvm2-libs 2.02.98 9.el6_4.3 x86_64\nmdadm 3.2.5 4.el6_4.3 x86_64\nmodule-init-tools 3.9 21.el6_4 x86_64\nmysql-libs 5.1.69 1.el6_4 x86_64\nnet-snmp 5.5 44.el6_4.4 x86_64\nnet-snmp-libs 5.5 44.el6_4.4 x86_64\nnet-snmp-utils 5.5 44.el6_4.4 x86_64\nnspr 4.9.5 2.el6_4 x86_64\nnss 3.14.3 5.el6_4 x86_64\nnss-softokn 3.14.3 3.el6_4 x86_64\nnss-sysinit 3.14.3 5.el6_4 x86_64\nnss-tools 3.14.3 5.el6_4 x86_64\nnss-util 3.14.3 3.el6_4 x86_64\nopenldap 2.4.23 32.el6_4.1 x86_64\nopenssl 1.0.0 27.el6_4.2 x86_64\nperl 5.10.1 131.el6_4 x86_64\nperl-Module-Pluggable 3.90 131.el6_4 x86_64\nperl-Pod-Escapes 1.04 131.el6_4 x86_64\nperl-Pod-Simple 3.13 131.el6_4 x86_64\nperl-libs 5.10.1 131.el6_4 x86_64\nperl-version 0.77 131.el6_4 x86_64\npixman 0.26.2 5.el6_4 x86_64\npolkit 0.96 5.el6_4 x86_64\npython 2.6.6 37.el6_4 x86_64\npython-dmidecode 3.10.13 3.el6_4 x86_64\npython-libs 2.6.6 37.el6_4 x86_64\npython-rhsm 1.8.17 1.el6_4 x86_64\nqemu-img 0.12.1.2 2.355.el6_4.9 x86_64\nqemu-kvm 0.12.1.2 2.355.el6_4.9 x86_64\nrhn-check 1.0.0.1 8.el6 noarch\nrhn-client-tools 1.0.0.1 8.el6 noarch\nrhn-setup 1.0.0.1 8.el6 noarch\nrhnlib 2.5.22 15.el6 noarch\nrsyslog 5.8.10 7.el6_4 x86_64\nruby 1.8.7.352 13.el6_4 x86_64\nruby-irb 1.8.7.352 13.el6_4 x86_64\nruby-libs 1.8.7.352 13.el6_4 x86_64\nruby-rdoc 1.8.7.352 13.el6_4 x86_64\nselinux-policy 3.7.19 195.el6_4.18 noarch\nselinux-policy-targeted 3.7.19 195.el6_4.18 noarch\nsetup 2.8.14 20.el6_4.1 noarch\nspice-server 0.12.0 12.el6_4.5 x86_64\nsubscription-manager 1.8.22 1.el6_4 x86_64\nudev 147 2.46.el6_4.2 x86_64\nupstart 0.6.5 12.el6_4.1 x86_64\nutil-linux-ng 2.17.2 12.9.el6_4.3 x86_64\nyum-rhn-plugin 0.9.1 49.el6 noarch"
    },
  }}

mco_output_get_pkgs_with_vxvm_and_puppet_and_kernel = {'node1': {
    "errors": "",
    "data": {
      "status": 0,
      "err": "",
      "out": "EXTRlitppuppet_CXP9030746 2.4.1 1 noarch\nkernel 3.10.0 1160.83.1.el7 x86_64\nVRTSamf 7.3.1.3500 RHEL7 x86_64\nVRTSaslapm 7.3.1.3300 RHEL7 x86_64\nVRTSdbac 7.3.1.2400 RHEL7 x86_64\nVRTSgab 7.3.1.2500 RHEL7 x86_64\nVRTSglm 7.3.1.1500 RHEL7 x86_64\nVRTSgms 7.3.1.1500 RHEL7 x86_64\nVRTSllt 7.3.1.4500 RHEL7 x86_64\nVRTSodm 7.3.1.2800 RHEL7 x86_64\nVRTSvxfen 7.3.1.3500 RHEL7 x86_64\nVRTSvxfs 7.3.1.3200 RHEL7 x86_64\nVRTSvxvm 7.3.1.3308 RHEL7 x86_64"
      },
  }}

mco_output_get_pkgs_with_puppet_mcollective = {'node1': {
    "errors": "",
    "data": {
      "status": 0,
      "err": "",
      "out": "EXTRlitppuppet_CXP9030746 1.6.1 1 noarch\nEXTRlitpfacter_CXP9031032 1.4.1 1 x86_64\nEXTRlitpmcollective_CXP9031034 1.1.7 1 noarch\nEXTRlitpmcollectivecommon_CXP9031353 1.1.7 1 noarch"
      },
  }}

mco_output_get_pkgs_withpuppet = {'node1': {
    "errors": "",
    "data": {
      "status": 0,
      "err": "",
      "out": "EXTRlitppuppet_CXP9030746 1.6.1 1 noarch\nbind-libs 9.8.2 0.17.rc1.el6_4.6 x86_64\nbind-utils 9.8.2 0.17.rc1.el6_4.6 x86_64\nchkconfig 1.3.49.3 2.el6_4.1 x86_64\ncoreutils 8.4 19.el6_4.2 x86_64\ncoreutils-libs 8.4 19.el6_4.2 x86_64\ncurl 7.19.7 37.el6_4 x86_64\ndb4 4.7.25 18.el6_4 x86_64\ndb4-utils 4.7.25 18.el6_4 x86_64\ndbus-glib 0.86 6.el6_4 x86_64\ndevice-mapper 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-event 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-event-libs 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-libs 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-multipath 0.4.9 64.el6_4.2 x86_64\ndevice-mapper-multipath-libs 0.4.9 64.el6_4.2 x86_64\ndhclient 4.1.1 34.P1.el6_4.1 x86_64\ne2fsprogs 1.41.12 14.el6_4.4 x86_64\ne2fsprogs-libs 1.41.12 14.el6_4.4 x86_64\nethtool 3.5 1.1.el6_4 x86_64\nglibc-common 2.12 1.107.el6_4.5 x86_64\ngnupg2 2.0.14 6.el6_4 x86_64\ngnutls 2.8.5 10.el6_4.2 x86_64\ngnutls-utils 2.8.5 10.el6_4.2 x86_64\ngzip 1.3.12 19.el6_4 x86_64\ninitscripts 9.03.38 1.el6_4.2 x86_64\nipmitool 1.8.11 14.el6_4.1 x86_64\niputils 20071127 17.el6_4.2 x86_64\nkexec-tools 2.0.0 258.el6_4.2 x86_64\nkpartx 0.4.9 64.el6_4.2 x86_64\nkrb5-libs 1.10.3 10.el6_4.6 x86_64\nlibblkid 2.17.2 12.9.el6_4.3 x86_64\nlibcgroup 0.37 7.2.el6_4 x86_64\nlibcom_err 1.41.12 14.el6_4.4 x86_64\nlibcurl 7.19.7 37.el6_4 x86_64\nlibgcrypt 1.4.5 11.el6_4 x86_64\nlibgudev1 147 2.46.el6_4.2 x86_64\nlibnl 1.1.4 1.el6_4 x86_64\nlibselinux 2.0.94 5.3.el6_4.1 x86_64\nlibselinux-python 2.0.94 5.3.el6_4.1 x86_64\nlibselinux-ruby 2.0.94 5.3.el6_4.1 x86_64\nlibselinux-utils 2.0.94 5.3.el6_4.1 x86_64\nlibss 1.41.12 14.el6_4.4 x86_64\nlibtirpc 0.2.1 6.el6_4 x86_64\nlibudev 147 2.46.el6_4.2 x86_64\nlibuuid 2.17.2 12.9.el6_4.3 x86_64\nlibvirt-client 0.10.2 18.el6_4.15 x86_64\nlibvirt-python 0.10.2 18.el6_4.15 x86_64\nlibxml2 2.7.6 12.el6_4.1 x86_64\nlibxml2-python 2.7.6 12.el6_4.1 x86_64\nlvm2 2.02.98 9.el6_4.3 x86_64\nlvm2-libs 2.02.98 9.el6_4.3 x86_64\nmdadm 3.2.5 4.el6_4.3 x86_64\nmodule-init-tools 3.9 21.el6_4 x86_64\nmysql-libs 5.1.69 1.el6_4 x86_64\nnet-snmp 5.5 44.el6_4.4 x86_64\nnet-snmp-libs 5.5 44.el6_4.4 x86_64\nnet-snmp-utils 5.5 44.el6_4.4 x86_64\nnspr 4.9.5 2.el6_4 x86_64\nnss 3.14.3 5.el6_4 x86_64\nnss-softokn 3.14.3 3.el6_4 x86_64\nnss-sysinit 3.14.3 5.el6_4 x86_64\nnss-tools 3.14.3 5.el6_4 x86_64\nnss-util 3.14.3 3.el6_4 x86_64\nopenldap 2.4.23 32.el6_4.1 x86_64\nopenssl 1.0.0 27.el6_4.2 x86_64\nperl 5.10.1 131.el6_4 x86_64\nperl-Module-Pluggable 3.90 131.el6_4 x86_64\nperl-Pod-Escapes 1.04 131.el6_4 x86_64\nperl-Pod-Simple 3.13 131.el6_4 x86_64\nperl-libs 5.10.1 131.el6_4 x86_64\nperl-version 0.77 131.el6_4 x86_64\npixman 0.26.2 5.el6_4 x86_64\npolkit 0.96 5.el6_4 x86_64\npython 2.6.6 37.el6_4 x86_64\npython-dmidecode 3.10.13 3.el6_4 x86_64\npython-libs 2.6.6 37.el6_4 x86_64\npython-rhsm 1.8.17 1.el6_4 x86_64\nqemu-img 0.12.1.2 2.355.el6_4.9 x86_64\nqemu-kvm 0.12.1.2 2.355.el6_4.9 x86_64\nrhn-check 1.0.0.1 8.el6 noarch\nrhn-client-tools 1.0.0.1 8.el6 noarch\nrhn-setup 1.0.0.1 8.el6 noarch\nrhnlib 2.5.22 15.el6 noarch\nrsyslog 5.8.10 7.el6_4 x86_64\nruby 1.8.7.352 13.el6_4 x86_64\nruby-irb 1.8.7.352 13.el6_4 x86_64\nruby-libs 1.8.7.352 13.el6_4 x86_64\nruby-rdoc 1.8.7.352 13.el6_4 x86_64\nselinux-policy 3.7.19 195.el6_4.18 noarch\nselinux-policy-targeted 3.7.19 195.el6_4.18 noarch\nsetup 2.8.14 20.el6_4.1 noarch\nspice-server 0.12.0 12.el6_4.5 x86_64\nsubscription-manager 1.8.22 1.el6_4 x86_64\nudev 147 2.46.el6_4.2 x86_64\nupstart 0.6.5 12.el6_4.1 x86_64\nutil-linux-ng 2.17.2 12.9.el6_4.3 x86_64\nyum-rhn-plugin 0.9.1 49.el6 noarch"
    },
  }}

mco_output_get_veritas_pkgs = {'node1': {
    "errors": "",
    "data": {
      "status": 0,
      "err": "",
      "out": "VRTSamf 6.1.1.200 RHEL6.x86_64"
    },
  }}

mco_output_get_pkgs_withvxvm_nokernel = {'node1': {
    "errors": "",
    "data": {
      "status": 0,
      "err": "",
      "out": "VRTSvxvm 7.3.1.3308 RHEL7 x86_64\nbind-libs 9.8.2 0.17.rc1.el6_4.6 x86_64\nbind-utils 9.8.2 0.17.rc1.el6_4.6 x86_64\nchkconfig 1.3.49.3 2.el6_4.1 x86_64\ncoreutils 8.4 19.el6_4.2 x86_64\ncoreutils-libs 8.4 19.el6_4.2 x86_64\ncurl 7.19.7 37.el6_4 x86_64\ndb4 4.7.25 18.el6_4 x86_64\ndb4-utils 4.7.25 18.el6_4 x86_64\ndbus-glib 0.86 6.el6_4 x86_64\ndevice-mapper 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-event 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-event-libs 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-libs 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-multipath 0.4.9 64.el6_4.2 x86_64\ndevice-mapper-multipath-libs 0.4.9 64.el6_4.2 x86_64\ndhclient 4.1.1 34.P1.el6_4.1 x86_64\ne2fsprogs 1.41.12 14.el6_4.4 x86_64\ne2fsprogs-libs 1.41.12 14.el6_4.4 x86_64\nethtool 3.5 1.1.el6_4 x86_64\nglibc-common 2.12 1.107.el6_4.5 x86_64\ngnupg2 2.0.14 6.el6_4 x86_64\ngnutls 2.8.5 10.el6_4.2 x86_64\ngnutls-utils 2.8.5 10.el6_4.2 x86_64\ngzip 1.3.12 19.el6_4 x86_64\ninitscripts 9.03.38 1.el6_4.2 x86_64\nipmitool 1.8.11 14.el6_4.1 x86_64\niputils 20071127 17.el6_4.2 x86_64\nkexec-tools 2.0.0 258.el6_4.2 x86_64\nkpartx 0.4.9 64.el6_4.2 x86_64\nkrb5-libs 1.10.3 10.el6_4.6 x86_64\nlibblkid 2.17.2 12.9.el6_4.3 x86_64\nlibcgroup 0.37 7.2.el6_4 x86_64\nlibcom_err 1.41.12 14.el6_4.4 x86_64\nlibcurl 7.19.7 37.el6_4 x86_64\nlibgcrypt 1.4.5 11.el6_4 x86_64\nlibgudev1 147 2.46.el6_4.2 x86_64\nlibnl 1.1.4 1.el6_4 x86_64\nlibselinux 2.0.94 5.3.el6_4.1 x86_64\nlibselinux-python 2.0.94 5.3.el6_4.1 x86_64\nlibselinux-ruby 2.0.94 5.3.el6_4.1 x86_64\nlibselinux-utils 2.0.94 5.3.el6_4.1 x86_64\nlibss 1.41.12 14.el6_4.4 x86_64\nlibtirpc 0.2.1 6.el6_4 x86_64\nlibudev 147 2.46.el6_4.2 x86_64\nlibuuid 2.17.2 12.9.el6_4.3 x86_64\nlibvirt-client 0.10.2 18.el6_4.15 x86_64\nlibvirt-python 0.10.2 18.el6_4.15 x86_64\nlibxml2 2.7.6 12.el6_4.1 x86_64\nlibxml2-python 2.7.6 12.el6_4.1 x86_64\nlvm2 2.02.98 9.el6_4.3 x86_64\nlvm2-libs 2.02.98 9.el6_4.3 x86_64\nmdadm 3.2.5 4.el6_4.3 x86_64\nmodule-init-tools 3.9 21.el6_4 x86_64\nmysql-libs 5.1.69 1.el6_4 x86_64\nnet-snmp 5.5 44.el6_4.4 x86_64\nnet-snmp-libs 5.5 44.el6_4.4 x86_64\nnet-snmp-utils 5.5 44.el6_4.4 x86_64\nnspr 4.9.5 2.el6_4 x86_64\nnss 3.14.3 5.el6_4 x86_64\nnss-softokn 3.14.3 3.el6_4 x86_64\nnss-sysinit 3.14.3 5.el6_4 x86_64\nnss-tools 3.14.3 5.el6_4 x86_64\nnss-util 3.14.3 3.el6_4 x86_64\nopenldap 2.4.23 32.el6_4.1 x86_64\nopenssl 1.0.0 27.el6_4.2 x86_64\nperl 5.10.1 131.el6_4 x86_64\nperl-Module-Pluggable 3.90 131.el6_4 x86_64\nperl-Pod-Escapes 1.04 131.el6_4 x86_64\nperl-Pod-Simple 3.13 131.el6_4 x86_64\nperl-libs 5.10.1 131.el6_4 x86_64\nperl-version 0.77 131.el6_4 x86_64\npixman 0.26.2 5.el6_4 x86_64\npolkit 0.96 5.el6_4 x86_64\npython 2.6.6 37.el6_4 x86_64\npython-dmidecode 3.10.13 3.el6_4 x86_64\npython-libs 2.6.6 37.el6_4 x86_64\npython-rhsm 1.8.17 1.el6_4 x86_64\nqemu-img 0.12.1.2 2.355.el6_4.9 x86_64\nqemu-kvm 0.12.1.2 2.355.el6_4.9 x86_64\nrhn-check 1.0.0.1 8.el6 noarch\nrhn-client-tools 1.0.0.1 8.el6 noarch\nrhn-setup 1.0.0.1 8.el6 noarch\nrhnlib 2.5.22 15.el6 noarch\nrsyslog 5.8.10 7.el6_4 x86_64\nruby 1.8.7.352 13.el6_4 x86_64\nruby-irb 1.8.7.352 13.el6_4 x86_64\nruby-libs 1.8.7.352 13.el6_4 x86_64\nruby-rdoc 1.8.7.352 13.el6_4 x86_64\nselinux-policy 3.7.19 195.el6_4.18 noarch\nselinux-policy-targeted 3.7.19 195.el6_4.18 noarch\nsetup 2.8.14 20.el6_4.1 noarch\nspice-server 0.12.0 12.el6_4.5 x86_64\nsubscription-manager 1.8.22 1.el6_4 x86_64\nudev 147 2.46.el6_4.2 x86_64\nupstart 0.6.5 12.el6_4.1 x86_64\nutil-linux-ng 2.17.2 12.9.el6_4.3 x86_64\nyum-rhn-plugin 0.9.1 49.el6 noarch"
    },
  }}

mco_output_get_pkgs_withvxvm_and_kernel = {'node1': {
    "errors": "",
    "data": {
      "status": 0,
      "err": "",
      "out": "VRTSvxvm 7.3.1.3308 RHEL7 x86_64\nkernel 3.10.0 1160.83.1.el7 x86_64\nbind-libs 9.8.2 0.17.rc1.el6_4.6 x86_64\nbind-utils 9.8.2 0.17.rc1.el6_4.6 x86_64\nchkconfig 1.3.49.3 2.el6_4.1 x86_64\ncoreutils 8.4 19.el6_4.2 x86_64\ncoreutils-libs 8.4 19.el6_4.2 x86_64\ncurl 7.19.7 37.el6_4 x86_64\ndb4 4.7.25 18.el6_4 x86_64\ndb4-utils 4.7.25 18.el6_4 x86_64\ndbus-glib 0.86 6.el6_4 x86_64\ndevice-mapper 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-event 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-event-libs 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-libs 1.02.77 9.el6_4.3 x86_64\ndevice-mapper-multipath 0.4.9 64.el6_4.2 x86_64\ndevice-mapper-multipath-libs 0.4.9 64.el6_4.2 x86_64\ndhclient 4.1.1 34.P1.el6_4.1 x86_64\ne2fsprogs 1.41.12 14.el6_4.4 x86_64\ne2fsprogs-libs 1.41.12 14.el6_4.4 x86_64\nethtool 3.5 1.1.el6_4 x86_64\nglibc-common 2.12 1.107.el6_4.5 x86_64\ngnupg2 2.0.14 6.el6_4 x86_64\ngnutls 2.8.5 10.el6_4.2 x86_64\ngnutls-utils 2.8.5 10.el6_4.2 x86_64\ngzip 1.3.12 19.el6_4 x86_64\ninitscripts 9.03.38 1.el6_4.2 x86_64\nipmitool 1.8.11 14.el6_4.1 x86_64\niputils 20071127 17.el6_4.2 x86_64\nkexec-tools 2.0.0 258.el6_4.2 x86_64\nkpartx 0.4.9 64.el6_4.2 x86_64\nkrb5-libs 1.10.3 10.el6_4.6 x86_64\nlibblkid 2.17.2 12.9.el6_4.3 x86_64\nlibcgroup 0.37 7.2.el6_4 x86_64\nlibcom_err 1.41.12 14.el6_4.4 x86_64\nlibcurl 7.19.7 37.el6_4 x86_64\nlibgcrypt 1.4.5 11.el6_4 x86_64\nlibgudev1 147 2.46.el6_4.2 x86_64\nlibnl 1.1.4 1.el6_4 x86_64\nlibselinux 2.0.94 5.3.el6_4.1 x86_64\nlibselinux-python 2.0.94 5.3.el6_4.1 x86_64\nlibselinux-ruby 2.0.94 5.3.el6_4.1 x86_64\nlibselinux-utils 2.0.94 5.3.el6_4.1 x86_64\nlibss 1.41.12 14.el6_4.4 x86_64\nlibtirpc 0.2.1 6.el6_4 x86_64\nlibudev 147 2.46.el6_4.2 x86_64\nlibuuid 2.17.2 12.9.el6_4.3 x86_64\nlibvirt-client 0.10.2 18.el6_4.15 x86_64\nlibvirt-python 0.10.2 18.el6_4.15 x86_64\nlibxml2 2.7.6 12.el6_4.1 x86_64\nlibxml2-python 2.7.6 12.el6_4.1 x86_64\nlvm2 2.02.98 9.el6_4.3 x86_64\nlvm2-libs 2.02.98 9.el6_4.3 x86_64\nmdadm 3.2.5 4.el6_4.3 x86_64\nmodule-init-tools 3.9 21.el6_4 x86_64\nmysql-libs 5.1.69 1.el6_4 x86_64\nnet-snmp 5.5 44.el6_4.4 x86_64\nnet-snmp-libs 5.5 44.el6_4.4 x86_64\nnet-snmp-utils 5.5 44.el6_4.4 x86_64\nnspr 4.9.5 2.el6_4 x86_64\nnss 3.14.3 5.el6_4 x86_64\nnss-softokn 3.14.3 3.el6_4 x86_64\nnss-sysinit 3.14.3 5.el6_4 x86_64\nnss-tools 3.14.3 5.el6_4 x86_64\nnss-util 3.14.3 3.el6_4 x86_64\nopenldap 2.4.23 32.el6_4.1 x86_64\nopenssl 1.0.0 27.el6_4.2 x86_64\nperl 5.10.1 131.el6_4 x86_64\nperl-Module-Pluggable 3.90 131.el6_4 x86_64\nperl-Pod-Escapes 1.04 131.el6_4 x86_64\nperl-Pod-Simple 3.13 131.el6_4 x86_64\nperl-libs 5.10.1 131.el6_4 x86_64\nperl-version 0.77 131.el6_4 x86_64\npixman 0.26.2 5.el6_4 x86_64\npolkit 0.96 5.el6_4 x86_64\npython 2.6.6 37.el6_4 x86_64\npython-dmidecode 3.10.13 3.el6_4 x86_64\npython-libs 2.6.6 37.el6_4 x86_64\npython-rhsm 1.8.17 1.el6_4 x86_64\nqemu-img 0.12.1.2 2.355.el6_4.9 x86_64\nqemu-kvm 0.12.1.2 2.355.el6_4.9 x86_64\nrhn-check 1.0.0.1 8.el6 noarch\nrhn-client-tools 1.0.0.1 8.el6 noarch\nrhn-setup 1.0.0.1 8.el6 noarch\nrhnlib 2.5.22 15.el6 noarch\nrsyslog 5.8.10 7.el6_4 x86_64\nruby 1.8.7.352 13.el6_4 x86_64\nruby-irb 1.8.7.352 13.el6_4 x86_64\nruby-libs 1.8.7.352 13.el6_4 x86_64\nruby-rdoc 1.8.7.352 13.el6_4 x86_64\nselinux-policy 3.7.19 195.el6_4.18 noarch\nselinux-policy-targeted 3.7.19 195.el6_4.18 noarch\nsetup 2.8.14 20.el6_4.1 noarch\nspice-server 0.12.0 12.el6_4.5 x86_64\nsubscription-manager 1.8.22 1.el6_4 x86_64\nudev 147 2.46.el6_4.2 x86_64\nupstart 0.6.5 12.el6_4.1 x86_64\nutil-linux-ng 2.17.2 12.9.el6_4.3 x86_64\nyum-rhn-plugin 0.9.1 49.el6 noarch"
    },
  }}

mco_output_get_pkgs_multiple_vrts_packages = {'node1': {
    "errors": "",
    "data": {
      "status": 0,
      "err": "",
      "out": "VRTSamf 7.3.1.3500 RHEL7 x86_64\nVRTSaslapm 7.3.1.3300 RHEL7 x86_64\nVRTSdbac 7.3.1.2400 RHEL7 x86_64\nVRTSgab 7.3.1.2500 RHEL7 x86_64\nVRTSglm 7.3.1.1500 RHEL7 x86_64\nVRTSgms 7.3.1.1500 RHEL7 x86_64\nVRTSllt 7.3.1.4500 RHEL7 x86_64\nVRTSodm 7.3.1.2800 RHEL7 x86_64\nVRTSvxfen 7.3.1.3500 RHEL7 x86_64\nVRTSvxfs 7.3.1.3200 RHEL7 x86_64\nVRTSvxvm 7.3.1.3308 RHEL7 x86_64"
   },
 }}

mco_output_no_pkgs = {'node1': {
    "errors": "",
    "data": {
      "status": 0,
      "err": "",
      "out": ""
    },
  }}

error_mco_output = {'node1': {
    "errors": "execution expired",
    "data": {
      "status": "no output",
      "err": "",
      "out": ""
    },
  }}

dmp_error_mco_output = {'node1': {
    "errors": "",
    "data": {
      "status": "0",
      "err": """VxVM vxdmpadm ERROR V-5-1-15690 Operation failed for one or more volume groups

VxVM vxdmpadm ERROR V-5-1-15686 The following vgs could not be migrated as they are in use -

  vg_app
VxVM vxdmpadm ERROR V-5-1-15686 The following vgs could not be migrated due to unknown error -

  vg_app""",
      "out": ""
    },
  }}

dmp_actual_error_mco_output = {'node1': {
    "errors": "",
    "data": {
      "status": "0",
      "err": "Something really bad happened",
      "out": ""
    },
  }}

positive_mco_ping_response = {'node1': {
            'errors': '',
            'data': {
                'pong': 160036345
            }
        }
    }

negative_mco_ping_response = {'node1': {
            'errors': 'No answer from node node1',
            'data': ''
            }
        }


class PkgMock(Mock):

    def __init__(self,
                 item_type_id,
                 item_id):

        super(PkgMock, self).__init__(item_id=item_id,
                                      item_type_id=item_type_id)

        self.properties = {}
        self.applied_properties = {}
        self.property_names = []
        self.get_vpath = lambda: "/%s/%s" % (self.item_type_id, self.item_id)
        self.get_source = lambda: self
        self.vpath = self.get_vpath()
        self.collections = {}
        self.subitems = {}


class PkgMockNode(PkgMock):

    def __init__(self, item_id, hostname, item_type_id='node', is_ms=False):
        super(PkgMockNode, self).__init__(item_id=item_id,
                                          item_type_id=item_type_id)

        self.item_type_id = item_type_id
        self.item_id = item_id
        self.hostname = hostname
        self.property_names = ['hostname']
        self._model_item = "/" + item_id
        self.is_ms = lambda: is_ms

    def query(self, type):

        def for_removal_side_effect():
            return False

        pkg1 = Mock(version=None, repository=None, config=None,
                    requires=None, replaces=None,
                    get_vpath=lambda: 'pkg1_vpath')
        pkg1.is_initial.return_value = True
        pkg1.is_for_removal.return_value = False
        pkg1.name = 'pkg1'

        pkg2 = Mock(version=None, repository=None, config=None,
                    requires=None, replaces=None,
                    get_vpath=lambda: 'pkg2_vpath')
        pkg2.name = 'pkg2'
        pkg2.is_initial.return_value = True
        pkg2.is_for_removal.return_value = False

        return [pkg1, pkg2]


class PkgMockVCSCluster(PkgMock):

    def __init__(self,
                 item_id,
                 cluster_type='',
                 item_type_id='cluster'):

        super(PkgMockVCSCluster, self).__init__(item_type_id=item_type_id,
                                                item_id=item_id)

        self.cluster_type = cluster_type
        self.cluster_id = item_id
        self.property_names = ['cluster_type']
        self.nodes = []
        self.collections['node'] = 'nodes'

    def query(self, query_item_type, **kwargs):
        if 'node' == query_item_type:
            return self.nodes


class PackagePluginTest(TestCase):

    def setUp(self):
        self.plugin = PackagePlugin()
        self.model = ModelManager()
        self.puppet_manager = PuppetManager(self.model)
        self.plugin_manager = PluginManager(self.model)
        self.execution_manager = ExecutionManager(self.model,
                                        self.puppet_manager,
                                        self.plugin_manager)
        self.callback_api = CallbackApi(self.execution_manager)
        self.model.register_property_types(
            CoreExtension().define_property_types())
        self.model.register_item_types(
            CoreExtension().define_item_types())

        self.model.register_property_types(
            PackageExtension().define_property_types())
        self.model.register_item_types(
            PackageExtension().define_item_types())

        self.model.register_item_type(
            ItemType(
                "mock_root",
                node1=Child("node"),
                packages=Collection("package"),
                repos=Collection("software-item"),
                services=Collection("service-base")
            )
        )

        self.model.register_property_type(
            PropertyType('boot_mode',
                         regex=r"^(uefi|bios)$")
        )

        self.model.create_root_item("mock_root")
        self.node1 = self.model.create_item(
            "node", "/node1", hostname="node1")
        self.model.create_item('upgrade', '/node1/upgrade', hash='blah')
        self._setUp_mocks()

    def setup_packages(self):
        self.package1 = self.model.create_item(
            "package", "/packages/package1", name="package1")
        self.package1._applied_properties = {'version': '',
                                           'release': ''}
        self.package2 = self.model.create_item(
            "package", "/packages/package2", name="package2")
        self.package2._applied_properties = {'version': '',
                                           'release': ''}
        self.package3 = self.model.create_item(
            "package", "/packages/package3", name="package3")
        self.package3._applied_properties = {'version': '',
                                           'release': ''}
        self.package4 = self.model.create_item(
            "package", "/packages/package4", name="package4")
        self.package4._applied_properties = {'version': '',
                                           'release': ''}
        self.model.create_inherited(
            self.package1.get_vpath(), "/node1/items/pkg1")
        self.node1.items.pkg1._applied_properties = {'version': '',
                                           'release': ''}
        self.model.create_inherited(
            self.package2.get_vpath(), "/node1/items/pkg2")
        self.node1.items.pkg2._applied_properties = {'version': '',
                                           'release': ''}

    def setup_packages_with_version(self):
        self.package1 = self.model.create_item(
            "package", "/packages/package1", name="package1", version='1-1')
        self.package1._applied_properties = {'version': '1-1',
                                           'release': ''}
        self.package2 = self.model.create_item(
            "package", "/packages/package2", name="package2", version='1-1')
        self.package2._applied_properties = {'version': '1-1',
                                           'release': ''}
        self.package3 = self.model.create_item(
            "package", "/packages/package3", name="package3", version='1-1')
        self.package3._applied_properties = {'version': '1-1',
                                           'release': ''}
        self.package4 = self.model.create_item(
            "package", "/packages/package4", name="package4", version='1-1')
        self.package4._applied_properties = {'version': '1-1',
                                           'release': ''}
        self.model.create_inherited(
            self.package1.get_vpath(), "/node1/items/pkg1")
        self.node1.items.pkg1._applied_properties = {'version': '',
                                           'release': ''}
        self.model.create_inherited(
            self.package2.get_vpath(), "/node1/items/pkg2")
        self.node1.items.pkg2._applied_properties = {'version': '',
                                           'release': ''}

    def setup_packages_states(self, version=False):
        if version:
            self.setup_packages_with_version()
        else:
            self.setup_packages()
        self.model.create_inherited(
            self.package3.get_vpath(), "/node1/items/pkg3")
        self.node1.items.pkg3._applied_properties = {'version': '',
                                           'release': ''}
        self.model.create_inherited(
            self.package4.get_vpath(), "/node1/items/pkg4")
        self.node1.items.pkg4._applied_properties = {'version': '',
                                           'release': ''}
        self.node1.items.pkg2.set_applied()
        self.node1.items.pkg3.set_updated()
        self.node1.items.pkg4.set_for_removal()

    def setup_cobbler_service(self, bootmode='bios'):
        self.model.register_item_type(
            ItemType(
                "cobbler-service",
                item_description=("This item type represents "
                                  "a Cobbler service."),
                extend_item="service-base",
                boot_mode=Property(
                    "boot_mode",
                    required=True,
                    default="bios",
                    prop_description="Boot mode (uefi|bios).",
                    site_specific=True
                )
            )
        )

        self.cobbler = self.model.create_item("cobbler-service",
                                              '/services/cobbler',
                                              boot_mode=bootmode)

    def test_plugin(self):
        self.setup_packages_with_version()
        self.node1.items.pkg2.set_applied()
        tasks = self.plugin.create_configuration(
            PluginApiContext(self.model)
        )

        node1 = QueryItem(self.model, self.node1)
        query2 = node1.query('package', name='package1')[0]

        task1_expected_props = [ConfigTask,
                                '/node1/items/pkg1',
                                'Initial',
                                'package',
                                'Install package "package1" on node "node1"',
                                'package1']

        task2_expected_props = [ConfigTask,
                                '/node1',
                                'Initial',
                                'litp::versionlock',
                                'Update versionlock file on node "node1"',
                                'node1']
        expected_props = [task1_expected_props, task2_expected_props]
        for task in tasks:
            if isinstance(task, ConfigTask):
                task_props = [type(task),
                                task.model_item.get_vpath(),
                                task.state,
                                task.call_type,
                                task.description,
                                task.call_id]
                self.assertTrue(any(prop == task_props for prop in expected_props))

    def test_versionlock_packages(self):
        self.setup_packages_with_version()
        node1 = QueryItem(self.model, self.node1)
        excluded_packages = self.plugin._versionlock_packages(PluginApiContext(self.model), node1)
        self.assertTrue(len(excluded_packages), 2)
        expected_excluded_packages = ['0:package2-1-1', '0:package1-1-1']
        for package in expected_excluded_packages:
            self.assertTrue(package in excluded_packages)

    def test_package_values(self):
        self.setup_packages_with_version()
        expected_package_values = {'require': [], 'ensure': '1-1'}
        pkg_item = self.model.query_by_vpath('/packages/package1')
        self.assertTrue(self.plugin._get_values(pkg_item) == expected_package_values)

    def test_package_with_repository(self):
        self.model.create_item(
            "package", "/packages/package1", name="package1", repository="REPO1")
        self.model.create_inherited(
            "/packages/package1", "/node1/items/pkg1")
        self.node1.items.pkg1._applied_properties = {'version': '',
                                           'release': ''}
        tasks = self.plugin.create_configuration(
                                PluginApiContext(self.model)
                )
        self.assertEquals(2, len(tasks))
        task = tasks[0]
        self.assertEquals("package", task.call_type)
        self.assertEquals("package1", task.call_id)
        self.assertEquals([{'type': 'Yumrepo', 'value': 'REPO1'}],
                           task.kwargs.get("require"))

    # Support for cluster starts here:
    def _setUp_mocks(self):
        # Controls what the mocks will return.
        self.package_mock = Mock()
        self.package_mock.is_initial.return_value = True
        self.package_mock.is_for_removal.return_value = False
        self.package_mock.version = 'self_package_mock version!'
        self.package_mock.release = 'self_package_mock release!'
        self.package_mock.name = 'self_package_mock name!'
        self.package_mock.get_vpath = Mock(return_value='self_package_mock vpath!')
        self.package_mock.applied_properties = {'version': 'self_package_mock version!',
                                           'release': 'self_package_mock release!'}
        self.package_mock.requires = ''
        self.package_mock.replaces = None
        self.package_mock.epoch = ''

        self.node_mock = Mock()
        self.node_mock.hostname = 'mn1'
        self.node_mock.query = MagicMock(return_value=[])
        self.node_mock.get_source = Mock(return_value=None)
        self.node_mock.is_for_removal.return_value = False

        self.service_mock = Mock()
        self.service_mock.runtimes.query.return_value = [self.package_mock]
        self.service_mock.applications.query.return_value = [self.package_mock]
        self.service_mock.nodes = [self.node_mock]

        self.vcs_cluster_mock = Mock()
        self.vcs_cluster_mock.services = [self.service_mock]

        self.api_context = Mock()
        self.api_context.query = Mock(return_value=[])

    def test_get_nodes_and_ms_one_for_removal(self):
        r_node_mock = Mock()
        r_node_mock.hostname = 'mn1'
        r_node_mock.query.side_effect = lambda x: []
        r_node_mock.get_source = Mock(return_value=None)
        r_node_mock.is_for_removal.return_value = True

        self.api_context.query.side_effect = [[self.node_mock], [r_node_mock]]

        package_obj = PackagePlugin()

        res = package_obj._get_nodes_and_ms(self.api_context)
        self.assertEquals(res, [self.node_mock])

    def test_get_nodes_and_ms(self):
        self.api_context.query.side_effect = lambda x: [self.node_mock]

        package_obj = PackagePlugin()

        res = package_obj._get_nodes_and_ms(self.api_context)
        self.assertEquals(res, [self.node_mock, self.node_mock])

    def test_get_cluster_services(self):
        self.api_context.query.side_effect = lambda x: [self.vcs_cluster_mock]

        package_obj = PackagePlugin()

        res = package_obj._get_cluster_services(self.api_context)
        self.assertEquals(res, [self.service_mock])

    def test_get_packages_for_node_in_cluster(self):
        package_obj = PackagePlugin()
        package_obj._get_cluster_services = Mock(return_value=[self.service_mock])

        res = package_obj._get_packages_for_node_in_cluster(self.node_mock, self.api_context)
        self.assertEquals(res, [self.package_mock, self.package_mock])

    @patch("package_plugin.package_plugin.PackagePlugin._is_package_new")
    def test__package_triggers_versionlock(self, patch_is_pkg_new):
        package_obj = PackagePlugin()
        node = Mock()
        package = MagicMock()
        package.applied_properties = {}
        package.version = '1.1'
        package.release = '1.1'
        package.is_for_removal = MagicMock(return_value=True)
        self.assertTrue(package_obj._package_triggers_versionlock(package, node))
        package.version = None
        package.release = None
        self.assertFalse(package_obj._package_triggers_versionlock(package, node))
        package.is_for_removal = MagicMock(return_value=False)
        package.version = '1.1'
        package.release = '1.1'
        patch_is_pkg_new.return_value = True
        self.assertTrue(package_obj._package_triggers_versionlock(package, node))
        package.version = None
        package.release = None
        package.epoch = None
        self.assertTrue(package_obj._package_triggers_versionlock(package, node))
        package.applied_properties = {'version': '1.1'}
        self.assertTrue(package_obj._package_triggers_versionlock(package, node))
        patch_is_pkg_new.return_value = False
        package.is_updated = MagicMock(return_value=True)
        package.version = '1.1'
        self.assertFalse(package_obj._package_triggers_versionlock(package, node))
        package.version = '1.2'
        self.assertTrue(package_obj._package_triggers_versionlock(package, node))

    def test_package_in_cluster(self):
        package_obj = PackagePlugin()
        package_obj._get_nodes_and_ms = Mock(return_value=[self.node_mock])
        package_obj._get_packages_for_node_in_cluster = Mock(return_value=[self.package_mock])
        package_obj._tasks_for_non_tree_pkgs = MagicMock(return_value={})
        tasks = package_obj.create_configuration(self.api_context)
        self.assertEqual(2, len(tasks))

    def test_verify_same_package_in_node_and_cluster_gives_error(self):
        # the package in a node:
        node_mock = Mock()
        node_mock.hostname = 'mn1'
        node_mock.query.side_effect = lambda x: [self.package_mock]

        # is the same package that the is in the cluster service:
        service_mock = Mock()
        service_mock.query.return_value = [self.package_mock]
        service_mock.nodes = [node_mock]

        vcs_cluster_mock = Mock()
        vcs_cluster_mock.services = [service_mock]

        api_context = Mock()
        api_context.query.return_value = [vcs_cluster_mock]

        package_obj = PackagePlugin()
        package_obj._get_nodes_and_ms = Mock(return_value=[node_mock])
        package_obj._get_packages_for_node_in_cluster = Mock(return_value=[self.package_mock])
        package_obj._validate_yum_repos = Mock(return_value=[])
        package_obj._validate_not_allowed_packages = Mock(return_value=[])

        package_obj._validate_name_and_arch = Mock(return_value=[])
        errors = package_obj.validate_model(api_context)
        self.assertEquals(str(errors),
        '[<self_package_mock vpath! - ValidationError - Package "self_package_mock name!" is duplicated for node "mn1">, <self_package_mock vpath! - ValidationError - Package "self_package_mock name!" is duplicated for node "mn1">]')

    @patch("package_plugin.package_plugin.PackagePlugin._is_upgrade_flag_set")
    def test_package_in_node_and_cluster(self, patch_is_upgrade_flag_set):

        patch_is_upgrade_flag_set.return_value = False
        node_package_mock = Mock()
        node_package_mock.is_initial.return_value = True
        node_package_mock.name = 'node_package_mock name!'
        node_package_mock.version = 'node_package_mock version!'
        node_package_mock.release = 'node_package_mock release!'
        node_package_mock.applied_properties = {'version': 'self_package_mock version!',
                                           'release': 'self_package_mock release!'}
        node_package_mock.requires = ''

        node_mock = Mock()
        node_mock.hostname.return_value = 'mn1'
        node_mock.query = MagicMock(return_value=[node_package_mock])

        service_mock = Mock()
        service_mock.query.return_value = [self.package_mock]
        service_mock.nodes = [node_mock]
        service_mock.is_updated = Mock(return_value=False)

        vcs_cluster_mock = Mock()
        vcs_cluster_mock.services = [service_mock]

        api_context = Mock()
        api_context.query.return_value = [vcs_cluster_mock]

        package_obj = PackagePlugin()
        package_obj._get_nodes_and_ms = Mock(return_value=[node_mock])
        package_obj._get_packages_for_node_in_cluster = Mock(return_value=[node_package_mock])

        package_obj._tasks_for_non_tree_pkgs = MagicMock(return_value={})
        tasks = package_obj.create_configuration(api_context)
        self.assertEqual(3, len(tasks))

    def test_node_marked_for_upgrade_reboot(self):
        # litpcds-5580
        api = PluginApiContext(self.model)
        node = api.query('node')[0]
        api.query('upgrade')[0].requires_reboot = 'true'
        api.query('upgrade')[0].reboot_performed = 'false'
        node._model_item.set_applied()
        api.query('upgrade')[0]._model_item.set_applied()
        self.assertTrue(self.plugin._node_marked_for_upgrade(node))
        api.query('upgrade')[0].reboot_performed = 'true'
        api.query('upgrade')[0]._model_item.set_applied()
        self.assertFalse(self.plugin._node_marked_for_upgrade(node))

    def test_rpc_correct_args_with_pkgs(self):
        self.setup_packages_states(version=True)
        self.plugin._node_marked_for_upgrade = MagicMock(return_value=True)
        self.plugin._execute_rpc_and_get_output = MagicMock(return_value=({}, []))
        api = PluginApiContext(self.model)
        self.plugin._get_dependent_packages = MagicMock(return_value='')
        self.plugin._tasks_for_non_tree_pkgs(api)
        self.plugin._execute_rpc_and_get_output.assert_called_with(
           api,
           ['node1'],
           'yum',
           'get_all_packages',)

    def test_rpc_correct_args_without_pkgs(self):
        self.setup_packages_states(version=False)
        self.plugin._node_marked_for_upgrade = MagicMock(return_value=True)
        self.plugin._execute_rpc_and_get_output = MagicMock(return_value=({}, []))
        api = PluginApiContext(self.model)
        self.plugin._get_dependent_packages = MagicMock(return_value='')
        self.plugin._tasks_for_non_tree_pkgs(api)
        self.plugin._execute_rpc_and_get_output.assert_called_with(
            api, ['node1'], 'yum', 'get_all_packages')

    def _process_mco_output(self, output):
        api = PluginApiContext(self.model)
        api.rpc_command = MagicMock(return_value=output)
        out, _ = self.plugin._execute_rpc_and_get_output(api,
                                                           [self.node1.hostname],
                                                           'yum',
                                                           'get_packages')
        return out

    def test_create_pkg_upgrade_tasks_with_kernel_on_sfha_cluster(self):
        cluster = Mock(cluster_type='sfha')
        upgrade = Mock(requires_reboot='', reboot_performed='')
        node = Mock(hostname='node1', query=Mock(return_value=[upgrade]))
        node.get_cluster = Mock(return_value=cluster)
        api = PluginApiContext(self.model)

        out = self._process_mco_output(mco_output_get_pkgs_withkernel)
        self.plugin._initial_or_updated_repos = MagicMock(return_value=[])
        tasks = self.plugin._create_pkg_upgrade_tasks(
                                 node, out[self.node1.hostname], api)
        self.assertEqual(3, len(tasks))
        self.assertEqual(tasks[0].description, 'Update packages on node "node1"')
        self.assertEqual(tasks[1].description, 'Re-enable VxDMP on node "node1"')  # Code should be updated to exclude this task from this scenario
        self.assertEqual(tasks[2].description, 'Reboot node "node1"')

    def test_create_pkg_upgrade_tasks_with_kernel_on_sfha_cluster_rack(self):
        cluster = Mock(cluster_type='sfha')
        upgrade = Mock(requires_reboot='', reboot_performed='')
        node = Mock(hostname='node1', query=Mock(return_value=[upgrade]))
        node.get_cluster = Mock(return_value=cluster)
        api = PluginApiContext(self.model)
        self.setup_cobbler_service(bootmode='uefi')

        out = self._process_mco_output(mco_output_get_pkgs_withkernel)
        self.plugin._initial_or_updated_repos = MagicMock(return_value=[])
        tasks = self.plugin._create_pkg_upgrade_tasks(
                                 node, out[self.node1.hostname], api)
        self.assertEqual(2, len(tasks))
        self.assertEqual(tasks[0].description, 'Update packages on node "node1"')
        self.assertEqual(tasks[1].description, 'Reboot node "node1"')

    def test_create_pkg_upgrade_tasks_with_kernel_on_vcs_cluster_disable_reboot_true(self):
        cluster = Mock(cluster_type='vcs')
        upgrade = Mock(requires_reboot='', reboot_performed='', disable_reboot='true')
        node = Mock(hostname='node1', query=Mock(return_value=[upgrade]))
        node.get_cluster = Mock(return_value=cluster)
        api = PluginApiContext(self.model)

        out = self._process_mco_output(mco_output_get_pkgs_withkernel)
        self.plugin._initial_or_updated_repos = MagicMock(return_value=[])
        tasks = self.plugin._create_pkg_upgrade_tasks(
                                 node, out[self.node1.hostname], api)
        self.assertEqual(1, len(tasks))
        self.assertEqual(tasks[0].description, 'Update packages on node "node1"')

    def test_create_pkg_upgrade_tasks_with_kernel_on_vcs_cluster_disable_reboot_false(self):
        cluster = Mock(cluster_type='vcs')
        upgrade = Mock(requires_reboot='', reboot_performed='', disable_reboot='false')
        node = Mock(hostname='node1', query=Mock(return_value=[upgrade]))
        node.get_cluster = Mock(return_value=cluster)
        api = PluginApiContext(self.model)

        out = self._process_mco_output(mco_output_get_pkgs_withkernel)
        self.plugin._initial_or_updated_repos = MagicMock(return_value=[])
        tasks = self.plugin._create_pkg_upgrade_tasks(
                                 node, out[self.node1.hostname], api)
        self.assertEqual(2, len(tasks))
        self.assertEqual(tasks[0].description, 'Update packages on node "node1"')
        self.assertEqual(tasks[1].description, 'Reboot node "node1"')

    def test_create_pkg_upgrade_tasks_with_kernel(self):
        api = PluginApiContext(self.model)
        out = self._process_mco_output(mco_output_get_pkgs_withkernel)
        tasks = self.plugin._create_pkg_upgrade_tasks(
                        api.query('node')[0], out[self.node1.hostname], api)
        self.assertEqual(2, len(tasks))
        self.assertEqual(tasks[0].description, 'Update packages on node "node1"')
        self.assertEqual(tasks[1].description, 'Reboot node "node1"')

    def test_create_pkg_no_upgrade_tasks_with_reboot(self):
        api = PluginApiContext(self.model)
        out = self._process_mco_output(mco_output_no_pkgs)
        self.plugin._upgrade_requires_reboot = MagicMock(return_value=True)
        tasks = self.plugin._create_pkg_upgrade_tasks(
                        api.query('node')[0], out[self.node1.hostname], api)
        self.assertEqual(1, len(tasks))
        self.assertEqual(tasks[0].description, 'Reboot node "node1"')

    def test_create_pkg_upgrade_tasks_without_kernel(self):
        api = PluginApiContext(self.model)
        out = self._process_mco_output(mco_output_get_pkgs_withoutkernel)
        # no kernel upgrade task and no reboot task
        tasks = self.plugin._create_pkg_upgrade_tasks(
                                api.query('node')[0], out[self.node1.hostname], api)
        self.assertEqual(1, len(tasks))
        self.assertEqual(tasks[0].description, 'Update packages on node "node1"')

    def test_create_pkg_upgrade_tasks_no_packages(self):
        api = PluginApiContext(self.model)
        out = self._process_mco_output(mco_output_no_pkgs)
        self.assertEqual(0, len(self.plugin._create_pkg_upgrade_tasks(
                        api.query('node')[0], out[self.node1.hostname], api))
                                                                  )
        self.plugin._initial_or_updated_repos = MagicMock(return_value=['a'])
        tasks = self.plugin._create_pkg_upgrade_tasks(
                        api.query('node')[0], out[self.node1.hostname], api)
        self.assertEqual(1, len(tasks))
        self.assertEqual(tasks[0].description, 'Update packages on node "node1"')

    def test_create_pkg_upgrade_tasks_error(self):
        api = PluginApiContext(self.model)
        self.plugin._get_dependent_packages = MagicMock(return_value='p1')
        api.rpc_command = MagicMock(return_value=error_mco_output)
        self.plugin._node_marked_for_upgrade = MagicMock(return_value=True)
        self.assertRaises(PluginError, self.plugin._tasks_for_non_tree_pkgs, api)

    def test_create_pkg_upgrade_tasks_with_puppet(self):
        cluster = Mock(cluster_type='sfha')
        upgrade = Mock(requires_reboot='', reboot_performed='')
        node = Mock(hostname='node1', query=Mock(return_value=[upgrade]))
        node.get_cluster = Mock(return_value=cluster)
        api = PluginApiContext(self.model)

        out = self._process_mco_output(mco_output_get_pkgs_withpuppet)
        self.plugin._initial_or_updated_repos = MagicMock(return_value=[])

        tasks = self.plugin._create_pkg_upgrade_tasks(node, out[self.node1.hostname], api)
        self.assertEqual(2, len(tasks))
        self.assertEqual(tasks[0].description, 'Update packages on node "node1"')
        self.assertEqual(tasks[1].description, 'Restart mcollective on node "node1"')

        # --- --- ---

        self.plugin._gen_all_pkg_upgrade_tasks = MagicMock(return_value=(None, MagicMock(), None))
        self.plugin._create_pkg_upgrade_tasks(node, out[self.node1.hostname], api)
        self.plugin._gen_all_pkg_upgrade_tasks.assert_called_once_with(node, True, False, True, False, False)

    def test_create_pkg_upgrade_tasks_without_puppet(self):
        api = PluginApiContext(self.model)
        cluster = Mock(cluster_type='sfha')
        upgrade = Mock(requires_reboot='', reboot_performed='')
        node = Mock(hostname='node1', query=Mock(return_value=[upgrade]))
        node.get_cluster = Mock(return_value=cluster)

        out = self._process_mco_output(mco_output_get_pkgs_withkernel)
        self.plugin._initial_or_updated_repos = MagicMock(return_value=[])
        tasks = self.plugin._create_pkg_upgrade_tasks(node, out[self.node1.hostname], api)
        self.assertEqual(3, len(tasks))
        self.assertEqual(tasks[0].description, 'Update packages on node "node1"')
        self.assertEqual(tasks[1].description, 'Re-enable VxDMP on node "node1"')  # Code should be updated to exclude this task from this scenario
        self.assertEqual(tasks[2].description, 'Reboot node "node1"')

        # --- --- ---

        self.plugin._gen_all_pkg_upgrade_tasks = MagicMock(return_value=(None, MagicMock(), None))
        self.plugin._create_pkg_upgrade_tasks(node, out[self.node1.hostname], api)
        self.plugin._gen_all_pkg_upgrade_tasks.assert_called_once_with(node, False, False, True, False, False)

    def test_create_pkg_upgrade_tasks_without_puppet_rack(self):
        api = PluginApiContext(self.model)
        cluster = Mock(cluster_type='sfha')
        upgrade = Mock(requires_reboot='', reboot_performed='')
        node = Mock(hostname='node1', query=Mock(return_value=[upgrade]))
        node.get_cluster = Mock(return_value=cluster)
        self.setup_cobbler_service(bootmode='uefi')

        out = self._process_mco_output(mco_output_get_pkgs_withkernel)
        self.plugin._initial_or_updated_repos = MagicMock(return_value=[])

        tasks = self.plugin._create_pkg_upgrade_tasks(node, out[self.node1.hostname], api)
        self.assertEqual(2, len(tasks))
        self.assertEqual(tasks[0].description, 'Update packages on node "node1"')
        self.assertEqual(tasks[1].description, 'Reboot node "node1"')

        # --- --- ---

        self.plugin._gen_all_pkg_upgrade_tasks = MagicMock(return_value=(None, MagicMock(), None))
        tasks = self.plugin._create_pkg_upgrade_tasks(node, out[self.node1.hostname], api)
        self.plugin._gen_all_pkg_upgrade_tasks.assert_called_once_with(node, False, False, True, False, False)
        self.assertEqual(2, len(tasks))
        self.assertEqual(tasks[1].description, 'Reboot node "node1"')

    def test_create_pkg_upgrade_tasks_with_mcollective(self):
        cluster = Mock(cluster_type='sfha')
        upgrade = Mock(requires_reboot='', reboot_performed='')
        node = Mock(hostname='node1', query=Mock(return_value=[upgrade]))
        node.get_cluster = Mock(return_value=cluster)
        api = PluginApiContext(self.model)

        out = self._process_mco_output(mco_output_get_pkgs_with_puppet_mcollective)
        self.plugin._initial_or_updated_repos = MagicMock(return_value=[])

        tasks = self.plugin._create_pkg_upgrade_tasks(node, out[self.node1.hostname], api)
        self.assertEqual(3, len(tasks))
        self.assertEqual(tasks[0].description, 'Update mcollective on node "node1"')
        self.assertEqual(tasks[1].description, 'Update packages on node "node1"')
        self.assertEqual(tasks[2].description, 'Restart mcollective on node "node1"')

        # --- --- ---

        self.plugin._gen_all_pkg_upgrade_tasks = MagicMock(return_value=(MagicMock(), MagicMock(), None))
        self.plugin._create_pkg_upgrade_tasks(node, out[self.node1.hostname], api)
        self.plugin._gen_all_pkg_upgrade_tasks.assert_called_once_with(node, True, True, True, False, False)

    def test_gen_mco_pkg_upgrade_task(self):
        upgrade = Mock(requires_reboot='', reboot_performed='', disable_reboot='false')
        node = Mock(hostname='node1', query=Mock(return_value=[upgrade]))

        tasks = self.plugin._gen_mco_pkg_upgrade_task(node)
        self.assertEqual(tasks.description, 'Update mcollective on node "node1"')

    @mock.patch('package_plugin.package_plugin.run_rpc_command')
    def test_upgrade_mco_and_wait(self, mock_run_rpc_command):
        allowed_error = "No answer from node node1"
        package = EXTRLITPMCOLLECTIVE_PKG_NAME + " " + \
                  EXTRLITPMCOCOMMON_PKG_NAME
        self.plugin._execute_rpc_in_callback_task = MagicMock()
        mock_run_rpc_command.return_value = positive_mco_ping_response

        self.plugin._upgrade_mco_and_wait(self.callback_api, "node1", package)
        self.plugin._execute_rpc_in_callback_task.assert_has_calls([
            call(self.callback_api, ["node1"], YUM_MCO_AGENT,
                 YUM_UPGRADE_PACKAGE_ACTION, package,
                 timeout=60, allowed_errors=[allowed_error])])

    @mock.patch('package_plugin.package_plugin.run_rpc_command')
    def test_restart_mco_and_wait(self, mock_run_rpc_command):
        allowed_error = "No answer from node node1"
        command = '/usr/bin/systemctl restart mcollective.service'
        self.plugin._execute_rpc_in_callback_task = MagicMock()
        mock_run_rpc_command.return_value = positive_mco_ping_response

        self.plugin._restart_mco_and_wait(self.callback_api, "node1", command)
        self.plugin._execute_rpc_in_callback_task.assert_has_calls([
            call(self.callback_api, ["node1"], YUM_MCO_AGENT,
                 YUM_SET_STATE_VCS_SERVICES_ACTION,
                 command,
                 timeout=7, allowed_errors=[allowed_error])])

    def test_torf_315432(self):
        api = PluginApiContext(self.model)
        wait_based_on_puppet = True
        hostname = 'node1'
        upgrade_item = Mock(requires_reboot='', reboot_performed='')
        node_item = Mock(hostname=hostname, query=Mock(return_value=[upgrade_item]))

        # Generate an upgrade-all task
        _, upgrade_task, _ = self.plugin._gen_all_pkg_upgrade_tasks(node_item, False, False,
                                                             wait_based_on_puppet, True, False)
        # Verify the wait-based-on-puppet argument on that upgrade task
        self.assertEqual(upgrade_task.kwargs.get('wait_based_on_puppet', None),
                                                 wait_based_on_puppet)

        self.plugin._execute_rpc_and_get_output = MagicMock(return_value=({}, []))
        # Emulate Veritas upgrade errors
        self.plugin._has_veritas_upgrade_errors = lambda x, y: True

        self.plugin._reboot_node_and_wait = MagicMock()

        # Invoke the task callback method
        upgrade_task.callback(api, **upgrade_task.kwargs)

        # Verify the callback method executed _reboot_node_and_wait with the correct parameters
        self.plugin._reboot_node_and_wait.assert_called_once_with(api, hostname,
                                                                  False,
                                                                  wait_based_on_puppet)

    def test_create_pkg_upgrade_tasks_with_vxvm_nokernel(self):
        cluster = Mock(cluster_type='sfha')
        upgrade = Mock(requires_reboot='', reboot_performed='')
        node = Mock(hostname='node1', query=Mock(return_value=[upgrade]))
        node.get_cluster = Mock(return_value=cluster)
        out = self._process_mco_output(mco_output_get_pkgs_withvxvm_nokernel)
        api = PluginApiContext(self.model)

        tasks = self.plugin._create_pkg_upgrade_tasks(node,
                                                      out[self.node1.hostname], api)
        # Note: The order of the tasks is the order which they are created by
        #       the code. The LITP plan tasks will be ordered differently
        #       depending on the requirements each tasks has for other tasks.
        self.assertEqual(10, len(tasks))
        self.assertEqual('Stop Puppet on node "node1"', tasks[0].description)
        self.assertEqual('Remove LVM filter on node "node1"', tasks[1].description)
        self.assertEqual('Disable VxDMP on node "node1"', tasks[2].description)
        self.assertEqual('Disable vxvm-boot.service on node "node1"', tasks[3].description)
        self.assertEqual('Reboot node "node1"', tasks[4].description)  # Reboot1
        self.assertEqual('Update packages on node "node1"', tasks[5].description)
        self.assertEqual('Re-enable VxDMP on node "node1"', tasks[6].description)
        self.assertEqual('Reboot node "node1"', tasks[7].description)  # Reboot2
        self.assertEqual('Start Puppet on node "node1"', tasks[8].description)
        self.assertEqual('Add LVM filter on node "node1"', tasks[9].description)

        # The TORF-152429 reboot1 and pre-boot tasks
        self.assertTrue(tasks[0] in tasks[1].requires)  # 'Remove LVM' requires 'Stop Puppet'
        self.assertTrue(tasks[0] in tasks[2].requires)  # 'Disable VxDMP' rquires 'Stop Puppet'
        self.assertTrue(tasks[1] in tasks[2].requires)  # 'Disable VxDMP' requires 'Remove LVM'
        self.assertTrue(tasks[2] in tasks[3].requires)  # 'Disable vxvm-boot' requires' Disable VxDMP'
        self.assertTrue(tasks[2] in tasks[4].requires)  # 'Reboot1' requires 'Disable VxDMP'
        self.assertTrue(tasks[3] in tasks[4].requires)  # 'Reboot1' requires 'Disable vxvm-boot'

        # The upgrade and add lvm tasks
        for idx in (0, 1, 2, 3, 4, 5, 6, 8):
            if 4 >= idx:
                self.assertTrue(tasks[idx] in tasks[5].requires)
            self.assertFalse(tasks[9] in tasks[idx].requires)

        # The upgrade and reboot2 tasks
        self.assertTrue(tasks[5] in tasks[7].requires)  # 'Reboot2' requires 'Update packages'
        self.assertTrue(tasks[5] in tasks[6].requires)  # 'Re-enable VxDMP' requires 'Update packages'

        self.assertTrue(tasks[6] in tasks[7].requires)  # 'Reboot2' requires 'Re-enable VxDMP'

        # The TORF-152429 reboot2 and post-boot tasks
        self.assertTrue(tasks[7] in tasks[8].requires)  # 'Start Puppet' requires 'Reboot2'
        self.assertTrue(tasks[9] in tasks[7].requires)  # 'Reboot2' requires 'Add LVM'
        self.assertTrue(tasks[5] in tasks[9].requires)  # 'Add LVM' requires 'Update packages'
        self.assertTrue(tasks[6] in tasks[9].requires)  # 'Add LVM' requires 'Re-enable VxDMP'

    def test_create_pkg_upgrade_tasks_with_vxvm_nokernel_rack(self):
        cluster = Mock(cluster_type='sfha')
        upgrade = Mock(requires_reboot='', reboot_performed='')
        node = Mock(hostname='node1', query=Mock(return_value=[upgrade]))
        node.get_cluster = Mock(return_value=cluster)
        out = self._process_mco_output(mco_output_get_pkgs_withvxvm_nokernel)
        api = PluginApiContext(self.model)
        self.setup_cobbler_service(bootmode='uefi')

        tasks = self.plugin._create_pkg_upgrade_tasks(node,
                                                      out[self.node1.hostname], api)
        self.assertEqual(6, len(tasks))
        print(tasks)
        self.assertEqual('Stop Puppet on node "node1"', tasks[0].description)
        self.assertEqual('Disable vxvm-boot.service on node "node1"', tasks[1].description)
        self.assertEqual('Reboot node "node1"', tasks[2].description) # Reboot1
        self.assertEqual('Update packages on node "node1"', tasks[3].description)
        self.assertEqual('Reboot node "node1"', tasks[4].description)  # Reboot2
        self.assertEqual('Start Puppet on node "node1"', tasks[5].description)

        self.assertTrue(tasks[0] in tasks[1].requires)  # 'Disable vxvm-boot' requires 'Stop Puppet'
        self.assertTrue(tasks[1] in tasks[2].requires)  # 'Reboot1' requires 'Disable vxvm-boot'
        self.assertTrue(tasks[2] in tasks[3].requires)  # 'Update packages' requires 'Reboot1'
        self.assertTrue(tasks[3] in tasks[4].requires)  # 'Reboot2' requires 'Update packages'

        # The TORF-152429 reboot2 and post-boot tasks
        self.assertTrue(tasks[4] in tasks[5].requires)  # 'Start Puppet' requires 'Reboot2'

    def test_create_pkg_upgrade_tasks_with_vxvm_and_puppet_and_kernel(self):
        cluster = Mock(cluster_type='sfha')
        upgrade = Mock(requires_reboot='', reboot_performed='')
        node = Mock(hostname='node1', query=Mock(return_value=[upgrade]))
        node.get_cluster = Mock(return_value=cluster)
        out = self._process_mco_output(mco_output_get_pkgs_with_vxvm_and_puppet_and_kernel)
        api = PluginApiContext(self.model)

        tasks = self.plugin._create_pkg_upgrade_tasks(node, out[self.node1.hostname], api)

        self.assertEqual(12, len(tasks))
        self.assertEqual('Stop Puppet on node "node1"', tasks[0].description)
        self.assertEqual('Remove LVM filter on node "node1"', tasks[1].description)
        self.assertEqual('Disable VxDMP on node "node1"', tasks[2].description)
        self.assertEqual('Disable vxvm-boot.service on node "node1"', tasks[3].description)
        self.assertEqual('Reboot node "node1"', tasks[4].description)  # Reboot1
        self.assertEqual('Update packages on node "node1"', tasks[5].description)
        self.assertEqual('Restart mcollective on node "node1"', tasks[6].description)
        self.assertEqual('Disable VCS services on node "node1"', tasks[7].description)
        self.assertEqual('Re-enable VxDMP on node "node1"', tasks[8].description)
        self.assertEqual('Reboot node "node1"', tasks[9].description)  # Reboot2
        self.assertEqual('Start Puppet on node "node1"', tasks[10].description)
        self.assertEqual('Add LVM filter on node "node1"', tasks[11].description)

        # Plan order is the following order. The number is the relative position in the "tasks" list.
        # 0  Stop Puppet on node "node1"
        # 1  Remove LVM filter on node "node1"
        # 2  Disable VxDMP on node "node1"
        # 3  Disable vxvm-boot.service on node "node1"
        # 4  Reboot node "node1"
        # 7  Disable VCS services on node "node1"
        # 5  Update packages on node "node1"
        # 6  Restart mcollective service
        # 8  Re-enable VxDMP on node "node1"
        # 11 Add LVM filter on node "node1"
        # 9  Reboot node "node1"
        # 10 Start Puppet on node "node1"

        self.assertTrue(tasks[0] in tasks[1].requires)  # 'Remove LVM' requires 'Stop Puppet'
        self.assertTrue(tasks[0] in tasks[2].requires)  # 'Disable VxDMP' rquires 'Stop Puppet'
        self.assertTrue(tasks[1] in tasks[2].requires)  # 'Disable VxDMP' requires 'Remove LVM'
        self.assertTrue(tasks[2] in tasks[3].requires)  # 'Disable vxvm-boot' requires 'Disable VxDMP'
        self.assertTrue(tasks[2] in tasks[4].requires)  # 'Reboot1' requires 'Disable VxDMP'
        self.assertTrue(tasks[3] in tasks[4].requires)  # 'Reboot1' requires 'Disable vxvm-boot'

        # The "Update" and "Add LVM" tasks
        for idx in range(0, 9):
            if 4 >= idx:
                self.assertTrue(tasks[idx] in tasks[5].requires)
            self.assertFalse(tasks[11] in tasks[idx].requires, "task 11 not in requires of %d" % idx)

        self.assertTrue(tasks[7] in tasks[5].requires)  # 'Update packages' requires 'Disable VCS services'
        self.assertTrue(tasks[6] in tasks[9].requires)  # 'Reboot2' requires 'Restart Mcollective'
        self.assertTrue(tasks[6] in tasks[8].requires)  # 'Re-enable VxDMP' requires 'Restart Mcollective'
        self.assertTrue(tasks[8] in tasks[9].requires)  # 'Reboot2' requires 'Re-enable VxDMP'
        self.assertTrue(tasks[9] in tasks[10].requires)  # 'Start Puppet' requires 'Reboot2'
        self.assertTrue(tasks[11] in tasks[9].requires)  # 'Reboot2' requires 'Add LVM'
        self.assertTrue(tasks[6] in tasks[11].requires)  # 'Add LVM filter' requires 'Restart Mcollective'
        self.assertTrue(tasks[8] in tasks[11].requires)  # 'Add LVM filter' requires 'Re-enable VxDMP'

    def test_create_pkg_upgrade_tasks_with_vxvm_and_puppet_and_kernel_rack(self):
        cluster = Mock(cluster_type='sfha')
        upgrade = Mock(requires_reboot='', reboot_performed='')
        node = Mock(hostname='node1', query=Mock(return_value=[upgrade]))
        node.get_cluster = Mock(return_value=cluster)
        out = self._process_mco_output(mco_output_get_pkgs_with_vxvm_and_puppet_and_kernel)
        api = PluginApiContext(self.model)
        self.setup_cobbler_service(bootmode='uefi')

        tasks = self.plugin._create_pkg_upgrade_tasks(node, out[self.node1.hostname], api)

        self.assertEqual(8, len(tasks))
        self.assertEqual('Stop Puppet on node "node1"', tasks[0].description)
        self.assertEqual('Disable vxvm-boot.service on node "node1"', tasks[1].description)
        self.assertEqual('Reboot node "node1"', tasks[2].description) # Reboot1
        self.assertEqual('Update packages on node "node1"', tasks[3].description)
        self.assertEqual('Restart mcollective on node "node1"', tasks[4].description)
        self.assertEqual('Disable VCS services on node "node1"', tasks[5].description)
        self.assertEqual('Reboot node "node1"', tasks[6].description) # Reboot2
        self.assertEqual('Start Puppet on node "node1"', tasks[7].description)

        # Plan order is the following order. The number is the relative position in the "tasks" list.
        # 0  Stop Puppet on node "node1"
        # 1  Disable vxvm-boot.service on node "node1"
        # 2  Reboot node "node1"
        # 5  Disable VCS services on node "node1"
        # 3  Update packages on node "node1"
        # 4  Restart mcollective service
        # 6  Reboot node "node1"
        # 7  Start Puppet on node "node1"

        self.assertTrue(tasks[0] in tasks[1].requires)  # 'Disable vxvm-boot' requires 'Stop Puppet'
        self.assertTrue(tasks[1] in tasks[2].requires)  # 'Reboot1' requires 'Disable vxvm-boot'
        self.assertTrue(tasks[2] in tasks[3].requires)  # 'Update packages' requires 'Disable vxvm-boot'
        self.assertTrue(tasks[3] in tasks[4].requires)  # 'Restart Mcollective requires 'Update packages'
        self.assertTrue(tasks[5] in tasks[3].requires)  # 'Update packages' requires 'Disable VCS services'
        self.assertTrue(tasks[4] in tasks[6].requires)  # 'Reboot2' requires 'Restart Mcollective'
        self.assertTrue(tasks[6] in tasks[7].requires)  # 'Start Puppet' requires 'Reboot2'

    def test_create_pkg_upgrade_tasks_with_puppet_and_mcollective(self):
        cluster = Mock(cluster_type='sfha')
        upgrade = Mock(requires_reboot='', reboot_performed='')
        node = Mock(hostname='node1', query=Mock(return_value=[upgrade]))
        node.get_cluster = Mock(return_value=cluster)
        out = self._process_mco_output(mco_output_get_pkgs_with_puppet_mcollective)
        api = PluginApiContext(self.model)

        tasks = self.plugin._create_pkg_upgrade_tasks(node, out[self.node1.hostname], api)

        # Plan order is the following order. The number is the relative position in the "tasks" list.
        # 0  Update mcollective on node "node1"
        # 1  Update packages on node "node1"
        # 2  Restart mcollective service

        self.assertEqual(3, len(tasks))
        self.assertEqual('Update mcollective on node "node1"', tasks[0].description)
        self.assertEqual('Update packages on node "node1"', tasks[1].description)
        self.assertEqual('Restart mcollective on node "node1"', tasks[2].description)

    def test_create_pkg_upgrade_tasks_vxvm_nokernel_vs_vxvm_with_kernel(self):
        cluster = Mock(cluster_type='sfha')
        upgrade = Mock(requires_reboot='', reboot_performed='')
        node = Mock(hostname='node1', query=Mock(return_value=[upgrade]))
        node.get_cluster = Mock(return_value=cluster)
        out = self._process_mco_output(mco_output_get_pkgs_withvxvm_nokernel)
        api = PluginApiContext(self.model)
        tasks_nokernel = self.plugin._create_pkg_upgrade_tasks(node,
                                                      out[self.node1.hostname], api)
        out = self._process_mco_output(mco_output_get_pkgs_withvxvm_and_kernel)
        tasks_kernel = self.plugin._create_pkg_upgrade_tasks(
            node, out[self.node1.hostname], api
        )
        self.assertEqual(tasks_kernel, tasks_nokernel)

    def test_create_pkg_upgrade_tasks_vxvm_nokernel_vs_vxvm_with_kernel_rack(self):
        cluster = Mock(cluster_type='sfha')
        upgrade = Mock(requires_reboot='', reboot_performed='')
        node = Mock(hostname='node1', query=Mock(return_value=[upgrade]))
        node.get_cluster = Mock(return_value=cluster)
        out = self._process_mco_output(mco_output_get_pkgs_withvxvm_nokernel)
        api = PluginApiContext(self.model)
        self.setup_cobbler_service(bootmode='uefi')
        tasks_nokernel = self.plugin._create_pkg_upgrade_tasks(node,
                                                      out[self.node1.hostname], api)
        out = self._process_mco_output(mco_output_get_pkgs_withvxvm_and_kernel)
        tasks_kernel = self.plugin._create_pkg_upgrade_tasks(
            node, out[self.node1.hostname], api
        )
        self.assertEqual(tasks_kernel, tasks_nokernel)

    def test__validate_yum_repos(self):
        node_mock = Mock()
        node_mock.hostname = 'mn1'
        node_mock.get_vpath = MagicMock(return_value='/mn1')
        api_context = Mock()
        api_context.query.return_value = [node_mock]
        yum_mock = MagicMock()
        yum_mock.name = 'test_repo'
        yum_mock.is_applied = MagicMock(return_value=True)
        yum_mock.is_initial = MagicMock(return_value=False)
        yum_mock.is_updated = MagicMock(return_value=False)
        yum_mock.is_for_removal = MagicMock(return_value=False)
        yum_mock.is_removed = MagicMock(return_value=False)
        node_mock.query.return_value = [yum_mock]
        package_obj = PackagePlugin()
        package_obj._node_marked_for_upgrade = Mock(return_value=True)
        self.assertEquals([], package_obj._validate_yum_repos(api_context))
        yum_mock.is_applied = MagicMock(return_value=False)
        yum_mock.is_initial = MagicMock(return_value=True)
        self.assertEquals([], package_obj._validate_yum_repos(api_context))
        yum_mock.is_applied = MagicMock(return_value=False)
        yum_mock.is_updated = MagicMock(return_value=False)
        yum_mock.is_for_removal = MagicMock(return_value=True)
        yum_mock.get_state = MagicMock(return_value="ForRemoval")
        self.assertEquals('[</mn1 - ValidationError - Create plan failed, an upgraded node "mn1" has a yum repository "test_repo" in "ForRemoval" state.>]'
            , str(package_obj._validate_yum_repos(api_context)))

    def test__item_updated_except(self):
        self.model.register_item_type(
            ItemType(
                "yum-repository",
                extend_item="software-item",
                name=Property(
                    "basic_string",
                    prop_description="Yum Repository Name.",
                    required=True,
                    updatable_plugin=False,
                    updatable_rest=False
                ),
                base_url=Property(
                    "basic_string",
                    prop_description="Yum Repository URL.",
                ),
                ms_url_path=Property(
                    "basic_string",
                    site_specific=True,
                    prop_description="Yum Repository Path on MS."
                ),
                cache_metadata=Property(
                    "basic_boolean",
                    prop_description="Enables Yum metadata caching. "
                    "If false, sets metadata_expire to 0 seconds, "
                    "if true the property "
                    "defaults to "
                    "the value in yum.conf ",
                    default="false",
                ),
                checksum=Property(
                    "basic_string",
                    prop_description="Checksum for yum repository",
                    updatable_plugin=True,
                    updatable_rest=False,
                ),
                item_description=(
                    "The client-side Yum repository configuration."
                ),
            )
        )
        # Change for LITPCDS-13781: Default of '' for checksum not currently in use
        repo = self.model.create_item(
            "yum-repository", "/repos/yum_repo1", name="repo1", ms_url_path='test1')
        repo.set_applied()
        self.model.update_item("/repos/yum_repo1", ms_url_path='test2')
        repo_item = QueryItem(self.model, repo)
        self.assertTrue(self.plugin._item_updated_except(repo_item, ['checksum']))
        repo.set_applied()
        self.model.update_item("/repos/yum_repo1", ms_url_path='test3', cache_metadata='true')
        repo_item = QueryItem(self.model, repo)
        self.assertTrue(self.plugin._item_updated_except(repo_item, ['checksum']))
        repo.set_applied()
        self.model.update_item("/repos/yum_repo1", ms_url_path='test4')
        repo_item = QueryItem(self.model, repo)
        self.assertTrue(self.plugin._item_updated_except(repo_item, []))
        repo.set_applied()
        self.model.update_item("/repos/yum_repo1", checksum='DEADBEEF', ms_url_path='test5')
        repo_item = QueryItem(self.model, repo)
        self.assertTrue(self.plugin._item_updated_except(repo_item, ['checksum']))
        repo.set_applied()
        self.model.update_item("/repos/yum_repo1", checksum='0x9999')
        repo_item = QueryItem(self.model, repo)
        self.assertFalse(self.plugin._item_updated_except(repo_item, ['checksum']))
        repo.set_applied()
        repo_item = QueryItem(self.model, repo)
        self.assertFalse(self.plugin._item_updated_except(repo_item, ['checksum']))
        self.assertFalse(self.plugin._item_updated_except(repo_item, []))
        self.assertFalse(self.plugin._item_updated_except(repo_item, ['checksum', 'ms_url_path', 'name', 'cache_metadata']))

    def test_reboot_does_not_go_away(self):
        api = PluginApiContext(self.model)
        self.assertEqual(None, api.query('upgrade')[0].requires_reboot)
        out = self._process_mco_output(mco_output_get_pkgs_withkernel)
        tasks = self.plugin._create_pkg_upgrade_tasks(api.query('node')[0],
                                                      out[self.node1.hostname], api)
        self.assertTrue('Reboot' in tasks[-1].description)
        self.assertEqual(2, len(tasks))
        # now get rid of the kernel pkg which is responsible for the reboot
        api = PluginApiContext(self.model)
        out = self._process_mco_output(mco_output_get_pkgs_withoutkernel)
        tasks = self.plugin._create_pkg_upgrade_tasks(api.query('node')[0],
                                                      out[self.node1.hostname], api)
        self.assertTrue('Reboot' in tasks[-1].description)
        self.assertEqual(2, len(tasks))
        self.assertEqual('true', api.query('upgrade')[0].requires_reboot)

    def test_is_replacement_package(self):

        not_replacement = self.model.create_item(
                    "package", "/packages/pkg1",
                    name="not_replacement"
                )

        self.assertEquals(False, self.plugin._is_replacement_package(not_replacement))

        replacement = self.model.create_item(
                    "package", "/packages/pkg2",
                    name="replacement",
                    replaces="some_package"
                )

        self.assertEquals(True, self.plugin._is_replacement_package(replacement))

    def test_generate_full_package_name(self):

        n_package = self.model.create_item(
                    "package", "/packages/pkg1",
                    name="pkg"
                )

        self.assertEqual(
                    self.plugin._generate_full_package_name(n_package),
                    "pkg"
                )

        nvr_package = self.model.create_item(
                    "package", "/packages/pkg4",
                    name="pkg",
                    version='8.4.1',
                    release='2.el6'
                )

        self.assertEqual(
                    self.plugin._generate_full_package_name(nvr_package),
                    "pkg-8.4.1-2.el6"
                )

        nevra_package = self.model.create_item(
                    "package", "/packages/pkg",
                    name="pkg",
                    epoch=2,
                    version="8.4.1",
                    release="2.el6",
                    arch="noarch"
                )

        self.assertEqual(
                    self.plugin._generate_full_package_name(nevra_package),
                    "pkg-2:8.4.1-2.el6.noarch"
                )

    def test_generate_replace_script_from_package(self):

        rsyslog8 = self.model.create_item(
                    "package", "/packages/rsyslog",
                    name="EXTRlitprsyslog8",
                    epoch='1',
                    version='2',
                    release='3',
                    arch='4',
                    replaces="rsyslog7"
                )

        expected = "set -e\nrpm -ev --nodeps rsyslog7\nyum "\
                   "-y install EXTRlitprsyslog8-1:2-3.4"

        actual = self.plugin._generate_replace_script_from_package(rsyslog8)

        self.assertEqual(expected, actual)

    def test_replace_package_task(self):
        package1 = MagicMock(replaces='pkg2', epoch='1', version='2',
                             release='0', arch='x86_64')
        package1.name = 'pkg1'
        node_packages = []
        node = MagicMock(hostname='n1')
        node.query.return_value = [MagicMock()]
        task = self.plugin._replace_package_task(node, package1, node_packages)
        self.assertEqual((['n1'], 'yum', 'replace_package',
                          {'replacement': 'pkg1-1:2-0.x86_64',
                           'replaced':'pkg2'}),
                         task.args)
        self.assertEqual({'timeout': 120}, task.kwargs)

    def test_validate_packages_replacements(self):

        api = PluginApiContext(self.model)

        self.package1 = self.model.create_item(
            "package",
            "/packages/i1",
            name="rsyslog7")

        self.model.create_inherited(
            self.package1.get_vpath(), "/node1/items/i1")

        self.model.set_all_applied()

        # Case 1: Trying to replace a package that exists on the model

        self.package2 = self.model.create_item(
            "package",
            "/packages/i2",
            name="rsyslog8",
            replaces="rsyslog7")

        self.model.create_inherited(
            self.package2.get_vpath(), "/node1/items/i2")

        errors = self.plugin._validate_packages_replacements(api)

        msg = 'Replacement of a modelled package "rsyslog7"' \
            ' with "rsyslog8" is not currently supported.'

        expected = ValidationError(item_path='/node1/items/i2',
                                   error_message=msg)

        self.assertEqual([expected], errors)

        self.model.remove_item('/packages/i2')

        # Case 2: Trying to replace a package that does not exist
        # on the model

        self.package3 = self.model.create_item(
            "package",
            "/packages/i2",
            name="rsyslog8",
            replaces="foo")

        self.model.create_inherited(
            self.package3.get_vpath(), "/node1/items/i2")

        errors = self.plugin._validate_packages_replacements(api)

        self.assertEqual([], errors)

        # Case 3: Trying to replace a package that does not exist
        # on the model, but more than once

        self.replacer1 = self.model.create_item(
            "package",
            "/packages/i3",
            name="rsyslog8",
            replaces="oldpackage")

        self.replacer2 = self.model.create_item(
            "package",
            "/packages/i4",
            name="rsyslog9",
            replaces="oldpackage")

        self.model.create_inherited(
            self.replacer1.get_vpath(), "/node1/items/i3")

        self.model.create_inherited(
            self.replacer2.get_vpath(), "/node1/items/i4")

        errors = self.plugin._validate_packages_replacements(api)

        expected = []

        msg = 'Package "oldpackage", being replaced by "rsyslog8", '\
              'may be replaced only once.'
        expected.append(ValidationError\
                        (item_path='/node1/items/i3',
                         error_message=msg))

        msg = 'Package "oldpackage", being replaced by "rsyslog9", '\
              'may be replaced only once.'
        expected.append(ValidationError\
                        (item_path='/node1/items/i4',
                         error_message=msg))

        self.assertEqual(expected, errors)

    def create_clustere_service_n1(self):
        n1_mock = Mock(item_id="n1",
                       get_source=Mock(return_value=None),
                       is_for_removal=Mock(return_value=False))
        n1_mock.query.return_value = []
        n2_mock = Mock(item_id="n2",
                       get_source=Mock(return_value=None),
                       is_for_removal=Mock(return_value=False))
        n2_mock.query.return_value = []
        n3_mock = Mock(item_id="n3",
                       get_source=Mock(return_value=None),
                       is_for_removal=Mock(return_value=False))
        n3_mock.query.return_value = []
        service_mock = Mock()
        service_mock.runtimes.query.return_value = [self.package_mock]
        service_mock.applications.query.return_value = []
        service_mock.applied_properties = {"node_list": "n1"}
        return n1_mock, n2_mock, n3_mock, service_mock

    def test_has_requires_dependencies(self):

        # Case 1. package has no requires info
        no_requires = self.model.create_item(
                    "package",
                    "/packages/pkg1",
                    name="no_requires"
                )

        # Case 2. package has requires info
        has_requires = self.model.create_item(
                    "package",
                    "/packages/pkg2",
                    name="replacement",
                    requires="some_package"
                )

        # check all properties are created correctly
        for item in (no_requires, has_requires):
            self.assertFalse(isinstance(item, list))

        self.assertFalse(self.plugin._has_requirements(no_requires))
        self.assertTrue(self.plugin._has_requirements(has_requires))

    def test_get_package_by_name(self):

        # Create a single node cluster with and api context
        api = PluginApiContext(self.model)

        package1 = self.model.create_item(
            "package",
            "/packages/rsyslog",
            name="EXTRlitprsyslog_CXP9032140")

        self.model.create_inherited(package1.get_vpath(),
                                    self.node1.get_vpath() + '/items/rsyslog')

        # self.node1 is a ModelItem,
        # we need a QueryItem for the Plugin - so do a "query"
        node = api.query('node')[0]

        # Case 0. how do to get all modelled packages on a node
        # there should be a single package on that node
        packages = self.plugin._all_model_packages_in_node(node, api)
        self.assertEqual(1, len(packages))
        self.assertEquals(package1.name, packages[0].name)

        # Case 1. target package with name is present
        retrieved = self.plugin._get_package_by_name(
                        package1.name, packages)

        self.assertNotEquals(None, retrieved)
        self.assertEqual(package1.name, retrieved.name)

        # Case 2. target package name not present
        retrieved = self.plugin._get_package_by_name(
                            'some_package_name_that_does_not_exist', packages
                        )
        self.assertEquals(None, retrieved)

    def test_requires_orders_tasks_correctly(self):

        # identify a task associated with a package
        def retrieve_task_for(tasks, package_name):
            for task in tasks:
                if hasattr(task.model_item, 'name') and \
                    task.model_item.name == package_name:
                    return task
            return None

        # Create a single node cluster with and api context
        api = PluginApiContext(self.model)

        package1 = self.model.create_item(
                    "package",
                    "/packages/rsyslog",
                    name="rsyslog7"
                )

        package2 = self.model.create_item(
                    "package",
                    "/packages/elasticsearch",
                    name="rsyslog7_elasticsearch",
                    requires="rsyslog7"
                )

        # check all properties are created correctly
        for item in (package1, package2):
            self.assertFalse(isinstance(item, list))

        self.model.create_inherited(
                    package1.get_vpath(),
                    self.node1.get_vpath() + '/items/rsyslog'
                )

        self.model.create_inherited(
                    package2.get_vpath(),
                    self.node1.get_vpath() + '/items/elasticsearch'
                )

        tasks = self.plugin.create_configuration(api)

        # Case 1: requires with package install
        package1_task = retrieve_task_for(tasks, package1.name)
        package2_task = retrieve_task_for(tasks, package2.name)

        # make sure the requires are set up correctly
        self.assertNotEquals(None, package1_task)
        self.assertNotEquals(None, package2_task)
        self.assertEquals(0, len(package1_task.requires))
        self.assertEquals(1, len(package2_task.requires))

        package2_task_requirement = list(package2_task.requires)[0]

        self.assertEquals(
                package1.name,
                package2_task_requirement.name
            )

        # Case 2: requires with package replace

        package3 = self.model.create_item(
                    "package",
                    "/packages/new_rsyslog",
                    name="rsyslog8",
                    replaces="rsyslog7"
                )

        package4 = self.model.create_item(
                    "package",
                    "/packages/new_elasticsearch",
                    name="rsyslog8_elasticsearch",
                    requires="rsyslog8"
                )

        # check all properties are created correctly
        for item in (package3, package4):
            self.assertFalse(isinstance(item, list))

        self.model.create_inherited(
                    package3.get_vpath(),
                    self.node1.get_vpath() + '/items/new_rsyslog'
                )

        self.model.create_inherited(
                    package4.get_vpath(),
                    self.node1.get_vpath() + '/items/new_elasticsearch'
                )

        # create the configuration tasks again
        tasks = self.plugin.create_configuration(api)

        # Case 1: requires with package install
        package3_task = retrieve_task_for(tasks, package3.name)
        package4_task = retrieve_task_for(tasks, package4.name)

        # make sure the requires are set up correctly
        self.assertNotEquals(None, package3_task)
        self.assertNotEquals(None, package4_task)
        self.assertEquals(0, len(package3_task.requires))
        self.assertEquals(1, len(package4_task.requires))

        package4_task_requirement = list(package4_task.requires)[0]

        self.assertEquals(
                package3.name,
                package4_task_requirement.name
            )

    def test_get_cs_expansion_packages_for_node(self):
        node = Mock(item_id='n3')
        pkg = Mock(is_for_removal=lambda: False)
        cs = Mock(applied_properties={'node_list': 'n1,n2'},
                  node_list='n1,n2,n3')
        cs.runtimes.query.return_value = []
        cs.applications.query.return_value = [pkg]

        packages = self.plugin._get_cs_expansion_packages_for_node(cs, node)
        self.assertEquals(1, len(packages))
        self.assertEquals(pkg, packages[0])

        cs = Mock(applied_properties={'node_list': 'n1,n2,n3'},
                  node_list='n1,n2,n3')
        packages = self.plugin._get_cs_expansion_packages_for_node(cs, node)
        self.assertEquals(0, len(packages))

    @patch("package_plugin.package_plugin.PackagePlugin._get_cluster_services")
    def test_get_packages_for_node_for_sg_contraction(self, patch_get_cs):
        node = Mock(item_id='n3')
        api = Mock()
        pkg = Mock(name='pkg', is_for_removal=lambda: False)
        cs = Mock(is_updated=lambda: True,
                  applied_properties={'node_list': 'n1,n2,n3'},
                  node_list='n1,n2')
        cs.runtimes.query.return_value = []
        cs.applications.query.return_value = [pkg]
        patch_get_cs.return_value = [cs]

        packages = self.plugin._get_packages_for_node_for_sg_contraction(node,
                                                                           api)
        self.assertEquals(1, len(packages))
        self.assertEquals(pkg, packages[0])

        cs = Mock(applied_properties={'node_list': 'n1,n2,n3'},
                  node_list='n1,n2,n3')
        packages = self.plugin._get_cs_expansion_packages_for_node(cs, node)
        self.assertEquals(0, len(packages))

    @patch("package_plugin.package_plugin.PackagePlugin._get_cs_expansion_packages_for_node")
    def test_is_packages_new(self, patch_get_expansion_pkgs):
        # node package initial
        node = Mock(item_id='n1')
        pkg = Mock(get_node=lambda: node,
                   is_initial=lambda: True)
        self.assertEquals(True, self.plugin._is_package_new(node, pkg))

        # node package not initial
        pkg.is_initial = lambda: False
        self.assertEquals(False, self.plugin._is_package_new(node, pkg))

        # cluster package initial
        cs = Mock(name='cs1')
        pkg = Mock(get_node=lambda: None,
                   get_ms=lambda: None,
                   is_initial=lambda: True,
                   get_ancestor=lambda item_type_id: cs)
        pkg.parent.parent.parent.parent = cs
        self.assertEquals(True, self.plugin._is_package_new(node, pkg))

        # cluster package applied, cluster initial
        pkg.is_initial = lambda: False
        cs.is_initial = lambda: True
        self.assertEquals(True, self.plugin._is_package_new(node, pkg))

        # cluster expansion package
        cs.is_initial = lambda: False
        cs.is_updated = lambda: True
        patch_get_expansion_pkgs.return_value = [pkg]
        self.assertEquals(True, self.plugin._is_package_new(node, pkg))

        # cluster package applied, cluster applied and not expansion package
        patch_get_expansion_pkgs.return_value = []
        self.assertEquals(False, self.plugin._is_package_new(node, pkg))

    @patch("package_plugin.package_plugin.PackagePlugin._get_packages_for_node_for_sg_contraction")
    def test_all_packages_to_remove_from_node(self, patch_get_contraction_pkgs):
        node = Mock()
        api = Mock()
        pkg1 = Mock(is_for_removal=lambda: False)
        pkg2 = Mock(is_for_removal=lambda: False)
        pkg3 = Mock(is_for_removal=lambda: True)
        pkg4 = Mock()
        pkg5 = Mock()
        node_packages = [pkg1, pkg2, pkg3]
        patch_get_contraction_pkgs.return_value = [pkg4, pkg5]
        packages = self.plugin._all_packages_to_remove_from_node(node,
                                                            node_packages, api)
        self.assertEquals(set([pkg3, pkg4, pkg5]), set(packages))

    @patch("package_plugin.package_plugin.PackagePlugin._is_upgrade_flag_set")
    @patch("package_plugin.package_plugin.PackagePlugin._tasks_for_non_tree_pkgs")
    @patch("package_plugin.package_plugin.PackagePlugin._get_nodes_and_ms")
    @patch("package_plugin.package_plugin.PackagePlugin._all_model_packages_in_node")
    @patch("package_plugin.package_plugin.PackagePlugin._all_packages_to_remove_from_node")
    @patch("package_plugin.package_plugin.PackagePlugin._is_package_new")
    def test_create_configuration(self, patch_is_pkg_new,
                 patch_removal_packages, patch_node_packages, patch_get_nodes,
                 patch_non_tree_pkg_tasks, patch_is_upgrade_flag_set):
        # pkg1 is in both node_packages and for_removal lists
        # pkg2 is on node_packages list only. is_package_new returns True
        api = Mock()
        upgrade = Mock()
        upgrade.is_initial = MagicMock(return_value=True)
        node1 = Mock(hostname='node1', is_ms=lambda: False)
        node1.query = MagicMock(return_value=[upgrade])
        pkg1 = Mock(version=None, repository=None, config=None,
                    requires=None, replaces=None,
                    get_vpath=lambda: 'pkg1_vpath')
        pkg1.name = 'pkg1'
        pkg2 = Mock(version=None, repository=None, config=None,
                    requires=None, replaces=None,
                    get_vpath=lambda: 'pkg2_vpath')
        pkg2.name = 'pkg2'
        patch_is_upgrade_flag_set.return_value = False
        patch_get_nodes.return_value = [node1]
        patch_node_packages.return_value = [pkg1, pkg2]
        patch_removal_packages.return_value = [pkg1]
        patch_is_pkg_new.return_value = True
        patch_non_tree_pkg_tasks.return_value = {}

        tasks = self.plugin.create_configuration(api)

        expected = set(['Install package "pkg2" on node "node1"',
                        'Update package "pkg1" on node "node1"'])
        self.assertEquals(len(tasks), 2)
        self.assertEquals(set([t.description for t in tasks]), expected)

        # is_new_package returns False
        # pkg1 is for removal. pkg2 is updated
        patch_node_packages.return_value = [pkg2]
        patch_removal_packages.return_value = [pkg1]
        patch_is_pkg_new.return_value = False
        pkg2.is_updated.return_value = True
        tasks = self.plugin.create_configuration(api)
        expected = set(['Update package "pkg2" on node "node1"',
                        'Remove package "pkg1" on node "node1"'])
        self.assertEquals(len(tasks), 2)
        self.assertEquals(set([t.description for t in tasks]), expected)

    def test_get_remove_vrtsfsadv_task(self):
        all_tasks = [Mock()]
        upgrade = Mock()
        upgrade.is_initial = MagicMock(return_value=True)
        upgrade.get_state = MagicMock(return_value="Updated")
        cluster = Mock()
        cluster.cluster_type = 'sfha'
        node1 = Mock(hostname='node1', is_ms=lambda: False)
        node1.get_cluster = MagicMock(return_value=cluster)
        node1.query = MagicMock(return_value=[upgrade])
        node1.get_state = MagicMock(return_value="Updated")
        self.plugin._get_remove_vrtsfsadv_task(node1, all_tasks)
        self.assertEquals(len(all_tasks), 2)
        self.assertEquals('Remove VRTSfsadv and reset vxfs_replication errors on node "node1"',
                          all_tasks[1].description)

    def test_do_not_get_remove_vrtsfsadv_task_non_sfha(self):
        api = Mock()
        upgrade = Mock()
        upgrade.is_initial = MagicMock(return_value=True)
        upgrade.get_state = MagicMock(return_value="Updated")
        upgrade.reboot_performed = 'false'
        vcs_cluster = Mock()
        vcs_cluster.cluster_type = 'vcs'
        vcs_service = Mock()
        vcs_service.is_updated = MagicMock(return_value=False)
        vcs_cluster.services = [vcs_service]
        scp_node = Mock(hostname='scp-1', is_ms=lambda: False)
        vcs_service.nodes = MagicMock(return_value=[scp_node])
        scp_node.get_cluster = MagicMock(return_value=vcs_cluster)
        package = Mock(name="mockpackage", version="1", release="1", arch="x86", requires="")
        package.name = MagicMock(return_value="mockpackage")
        yum_repo = Mock()

        def scp_get_query(value):
            if value == "upgrade":
                return [upgrade]
            if value == "package":
                return [package]
            if value == "yum-repository":
                return [yum_repo]
            return None

        scp_node.query = MagicMock(side_effect=scp_get_query)
        scp_node.get_state = MagicMock(return_value="Updated")
        scp_node.is_for_removal = MagicMock(return_value=False)
        db_yum_repo = Mock(is_updated=lambda: False, is_initial=lambda: False)

        def db_get_query(value):
            if value == "upgrade":
                return [upgrade]
            if value == "package":
                return []
            if value == "yum-repository":
                return [db_yum_repo]
            return None

        dbnode = Mock(hostname='db-1', cluster_type='sfha', is_ms=lambda: False)
        dbnode.query = MagicMock(side_effect=db_get_query)
        dbnode.is_for_removal = MagicMock(return_value=False)
        dbnode.get_state = MagicMock(return_value="Updated")

        ms = Mock(hostname='ms-1', is_ms=lambda: True)

        def get_query(value):
            if value == "ms":
                return [ms]
            if value == "node":
                return [scp_node, dbnode]
            if value == "vcs-cluster":
                return [vcs_cluster]
            return None

        api.query = MagicMock(side_effect=get_query)

        rpc_out = MagicMock()
        rpc_out.side_effect = [({'scp-1': 'mockpackage 1 1 x86_64'}, None),
                            ({'db-1': ''}, None),
                            ({'ms-1': ''}, None)]
        self.plugin._execute_rpc_and_get_output = rpc_out

        all_tasks = self.plugin.create_configuration(api)
        self.assertEquals(len(all_tasks), 3)
        for task in all_tasks:
            if hasattr(task, 'node'):
                self.assertEquals('scp-1', task.node.hostname)
            elif hasattr(task, 'kwargs'):
                self.assertEquals({'node': 'scp-1', 'cluster': 'vcs',
                                   'wait_based_on_puppet': True, 'veritas_upgrade': False},
                                  task.kwargs)

    def test_update_db_do_not_get_remove_vrtsfsadv_task(self):
        api = Mock()
        upgrade = Mock()
        upgrade.is_initial = MagicMock(return_value=True)
        upgrade.get_state = MagicMock(return_value="Initial")
        upgrade.reboot_performed = 'false'

        def get_query(value):
            if value == "upgrade":
                return [upgrade]
            return []

        dbnode = Mock(hostname='db-1', cluster_type='sfha', is_ms=lambda: False)
        dbnode.query = MagicMock(side_effect=get_query)
        dbnode.is_for_removal = MagicMock(return_value=False)
        dbnode.get_state = MagicMock(return_value="Updated")

        ms = Mock(hostname='ms-1', is_ms=lambda: True)

        def get_query(value):
            if value == "ms":
                return [ms]
            if value == "node":
                return [dbnode]
            return []

        api.query = MagicMock(side_effect=get_query)
        self.assertTrue(self.plugin._node_marked_for_upgrade(dbnode))

        rpc_out = MagicMock()
        rpc_out.side_effect = [({'db-1': ''}, None),
                               ({'ms-1': ''}, None)]
        self.plugin._execute_rpc_and_get_output = rpc_out

        all_tasks = self.plugin.create_configuration(api)
        self.assertEquals(len(all_tasks), 0)

    def test_set_versionlock_dependencies(self):
        n1, n2, n3 = MagicMock(hostname='n1'), MagicMock(hostname='n2'), MagicMock(hostname='n3')
        vtasks = [MagicMock(), MagicMock()]
        utasks = [MagicMock(requires=set()), MagicMock(requires=set()),
                  MagicMock(requires=set()), MagicMock(requires=set())]

        vlocked_tasks = {'n1': vtasks[0], 'n3': vtasks[1]}
        upgrade_tasks = {'n1': [utasks[3]],
                         'n2': [utasks[0]],
                         'n3': [utasks[1], utasks[2]]}
        self.plugin._set_versionlock_dependencies(vlocked_tasks, upgrade_tasks)
        self.assertEqual(set(), utasks[0].requires)
        self.assertEqual(set([vtasks[0]]), utasks[3].requires)
        self.assertEqual(set([vtasks[1]]), utasks[1].requires)
        self.assertEqual(set([vtasks[1]]), utasks[2].requires)

    def test_msg_to_ignore_in_errs(self):
        errors = {'n1': ['one error', 'another error'],
                  'n2': ['VxVM vxdmpadm ERROR V-5-1-15690 Operation failed '
                         'for one or more volume groups\nVxVM vxdmpadm ERROR'
                         'V-5-1-15686 The following vgs could not be migrated '
                         'as they are in use -\n  vg_app\n'
                         'VxVM vxdmpadm ERROR V-5-1-15686 The following vgs '
                         'could not be migrated due to unknown error -\n'
                         '  vg_app ']}
        self.assertTrue(
            self.plugin._msg_to_ignore_in_errs(errors, DMP_MSG_to_IGNORE)
        )

        errors['n2'] = ['trololo']
        self.assertFalse(
            self.plugin._msg_to_ignore_in_errs(errors, DMP_MSG_to_IGNORE)
        )
        errors['n1'] = errors['n2'] = \
            ['VxVM vxdmpadm ERROR V-5-1-15690 Operation failed '
             'for one or more volume groups\nVxVM vxdmpadm ERROR'
             'V-5-1-15686 The following vgs could not be migrated '
             'as they are in use -\n  vg_app\n'
             'VxVM vxdmpadm ERROR V-5-1-15686 The following vgs '
             'could not be migrated due to unknown error -\n'
             '  vg_app ']
        self.assertTrue(
            self.plugin._msg_to_ignore_in_errs(errors, DMP_MSG_to_IGNORE)
        )

    @patch('package_plugin.package_plugin.time.sleep')
    def test_execute_rpc_dmp_command(self, ts):
        api = PluginApiContext(self.model)
        api.rpc_command = MagicMock(return_value=dmp_error_mco_output)

        # task fails after all retries have been attempted
        self.assertRaises(CallbackExecutionException,
            self.plugin._execute_rpc_dmp_command,
            api, ['node1'], 'dmp', 'dmpthings', retries=5
        )
        # the expected number of retries were performed
        ts.assert_has_calls([mock.call(2)] * 5)

        ts.reset_mock()
        # all ok, no retries or errors
        api.rpc_command.return_value = mco_output_no_pkgs
        self.assertEqual(None,
                         self.plugin._execute_rpc_dmp_command(
                             api, ['node1'], 'dmp', 'dmpthings')
                         )

        # actual error
        api.rpc_command.return_value = dmp_actual_error_mco_output
        self.assertRaises(CallbackExecutionException,
            self.plugin._execute_rpc_dmp_command,
            api, ['node1'], 'dmp', 'dmpthings', retries=5
        )
        # and no retries
        ts.assert_has_calls([])

        # couple of retries, then it's all good
        api.rpc_command.side_effect = [dmp_error_mco_output,
                                       dmp_error_mco_output,
                                       mco_output_no_pkgs]
        self.assertEqual(None,
                         self.plugin._execute_rpc_dmp_command(
                             api, ['node1'], 'dmp', 'dmpthings')
                         )
        ts.assert_has_calls([mock.call(2)] * 2)

    def test_upgrade_callback_task(self):
        m_cb_api = MagicMock()
        mock_erago = MagicMock()
        mock_node = MagicMock()
        mock_erago.side_effect = \
            [([], {mock_node: [VERITAS_UG_ERR, YUM_PENDING_ERROR]}),
             ([], {}),
             ([], {})]
        self.plugin._execute_rpc_and_get_output = mock_erago
        self.plugin._has_veritas_upgrade_errors = MagicMock()
        self.plugin._has_veritas_upgrade_errors.side_effect = [True, False]
        self.plugin._is_yum_pending_error = MagicMock(return_value=True)
        self.plugin._reboot_node_and_wait = MagicMock()

        self.plugin._upgrade_callback_task(m_cb_api, mock_node, MagicMock(), True, True)

        self.plugin._reboot_node_and_wait.assert_called_once_with(
            m_cb_api, mock_node, False, True)

    @mock.patch('package_plugin.package_plugin.RpcCommandProcessorBase')
    def test_execute_rpc_in_callback_task(self, rcpb):
        rcpb().execute_rpc_and_process_result.side_effect = RpcExecutionException('err')
        self.assertRaises(CallbackExecutionException,
                         self.plugin._execute_rpc_in_callback_task,
                             MagicMock(), ['n1'], 'yum', 'install', {}, 60
                         )
        rcpb().execute_rpc_and_process_result.return_value = (None, ['errs'])
        self.assertRaises(CallbackExecutionException,
                         self.plugin._execute_rpc_in_callback_task,
                             MagicMock(), ['n1'], 'yum', 'install', {}, 60
                         )

    @mock.patch('package_plugin.package_plugin.vcs_ext.VcsExtension')
    def test_remove_vrts_debug_call(self, m_ext):

        # Test removal is called when cluster is SFHA and VRTS packages are upgraded.
        mock_erago, cb_api = MagicMock(), MagicMock()
        mock_erago.side_effect = [(None, {'node': ['err']}), (None, None), (None, None)]
        self.plugin._execute_rpc_and_get_output = mock_erago
        self.plugin._upgrade_callback_task(cb_api, 'ms1', 'sfha', True, True)

        self.assertTrue(m_ext.get_package_file_info.called)
        self.assertTrue(m_ext.remove_unused_vrts_debug_files.called)

    @mock.patch('package_plugin.package_plugin.vcs_ext.VcsExtension')
    def test_remove_vrts_debug_removal(self, m_ext):

        vxvm_debug_list = ['foo1.debug', 'foo2.debug', 'foo3.debug']
        aslapm_debug_list = ['bar4.debug', 'bar5.debug']
        mock_erago, cb_api = MagicMock(), MagicMock()
        mock_erago.side_effect = [(None, {'node': ['err']}), (None, None), (None, None)]
        self.plugin._execute_rpc_and_get_output = mock_erago
        self.plugin._upgrade_callback_task(cb_api, 'ms1', 'sfha', True, True)
        m_ext.get_package_file_info.side_effect = [vxvm_debug_list, aslapm_debug_list]
        m_ext.remove_unused_vrts_debug_files.return_value = []

        self.plugin.remove_vrts_debuginfo(cb_api, 'ms1', 'sfha', True)

        m_ext.get_package_file_info.assert_has_calls(
            [mock.call(cb_api, 'ms1', 'VRTSvxvm', ["/opt", ".debug"]),
             mock.call(cb_api, 'ms1', 'VRTSaslapm', ["/opt", ".debug"])])

        m_ext.remove_unused_vrts_debug_files.assert_has_calls(
            [mock.call(cb_api, 'ms1', vxvm_debug_list),
             mock.call(cb_api, 'ms1', aslapm_debug_list)])

    @mock.patch('package_plugin.package_plugin.vcs_ext.VcsExtension')
    def test_remove_vrts_debug_not_called_cluster_type(self, m_ext):

        # Test removal is not called when cluster is not SFHA but VRTS packages are upgraded.
        mock_erago, cb_api = MagicMock(), MagicMock()
        mock_erago.side_effect = [(None, {'node': ['err']}), (None, None), (None, None)]
        self.plugin._execute_rpc_and_get_output = mock_erago
        self.plugin._upgrade_callback_task(cb_api, 'ms1', 'foo', True, True)

        self.assertFalse(m_ext.get_package_file_info.called)
        self.assertFalse(m_ext.remove_unused_vrts_debug_files.called)

    @mock.patch('package_plugin.package_plugin.vcs_ext.VcsExtension')
    def test_remove_vrts_debug_not_call_no_vrts_upgrd(self, m_ext):

        # Test removal is not called when cluster is SFHA but VRTS packages are not upgraded.
        mock_erago, cb_api = MagicMock(), MagicMock()
        mock_erago.side_effect = [(None, {'node': ['err']}), (None, None), (None, None)]
        self.plugin._execute_rpc_and_get_output = mock_erago
        self.plugin._upgrade_callback_task(cb_api, 'ms1', 'sfha', False, True)

        self.assertFalse(m_ext.get_package_file_info.called)
        self.assertFalse(m_ext.remove_unused_vrts_debug_files.called)

    def test_reboot_ran_with_veritas_error(self):
        mock_erago, cb_api = MagicMock(), MagicMock()
        mock_erago.return_value = ([], {'ms1': [VERITAS_UG_ERR]})
        self.plugin._execute_rpc_and_get_output = mock_erago
        self.plugin._reboot_node_and_wait = MagicMock()

        self.plugin._upgrade_callback_task(cb_api, 'ms1', None, True, True)
        self.plugin._reboot_node_and_wait.assert_called_once_with(
            cb_api, 'ms1', False, True)

    def test_ug_with_veritas_and_yum_errors_type1(self):
        mock_erago, cb_api = MagicMock(), MagicMock()
        # both Veritas and yum pending stuff errors
        mock_erago.side_effect = \
            [([], {'ms1': [VERITAS_UG_ERR, YUM_PENDING_ERROR]}),
             ([], {}),
             ([], {})]
        self.plugin._execute_rpc_and_get_output = mock_erago
        self.plugin._reboot_node_and_wait = MagicMock()

        self.plugin._upgrade_callback_task(cb_api, 'ms1', None, True, True)
        # calls upgrade, reboots node to clear veritas issue, completes pending
        # yum transaction and runs upgrade again
        self.plugin._reboot_node_and_wait.assert_called_once_with(
            cb_api, 'ms1', False, True)
        mock_erago.assert_has_calls(
            [call(cb_api, ['ms1'], 'yum', 'upgrade_all_packages', timeout=1860, tolerate_warnings=True),
             call(cb_api, ['ms1'], 'yum', 'complete_transaction', timeout=1860, tolerate_warnings=True),
             call(cb_api, ['ms1'], 'yum', 'upgrade_all_packages', timeout=1860, tolerate_warnings=True)])

    def test_ug_with_veritas_and_yum_errors_type2(self):
        mock_erago, cb_api = MagicMock(), MagicMock()
        # both Veritas and yum pending stuff errors
        mock_erago.side_effect = \
            [([], {'ms1': [YUM_PENDING_ERROR]}),
             ([], {}),
             ([], {'ms1': [VERITAS_UG_ERR]})]
        self.plugin._execute_rpc_and_get_output = mock_erago
        self.plugin._reboot_node_and_wait = MagicMock()

        self.plugin._upgrade_callback_task(cb_api, 'ms1', None, True, True)
        # calls upgrade, completes pending yum transaction, runs upgrade again
        # and reboots node to clear veritas issue
        self.plugin._reboot_node_and_wait.assert_called_once_with(
            cb_api, 'ms1', False, True)
        mock_erago.assert_has_calls(
            [call(cb_api, ['ms1'], 'yum', 'upgrade_all_packages', timeout=1860, tolerate_warnings=True),
             call(cb_api, ['ms1'], 'yum', 'complete_transaction', timeout=1860, tolerate_warnings=True),
             call(cb_api, ['ms1'], 'yum', 'upgrade_all_packages', timeout=1860, tolerate_warnings=True)])

    def test_ug_with_veritas_and_yum_errors_type3(self):
        mock_erago, cb_api = MagicMock(), MagicMock()
        # both Veritas and yum pending stuff errors
        mock_erago.side_effect = \
            [([], {'ms1': [YUM_PENDING_ERROR, VERITAS_UG_ERR]}),
             ([], {}),
             ([], {'ms1': [VERITAS_UG_ERR]})]
        self.plugin._execute_rpc_and_get_output = mock_erago
        self.plugin._reboot_node_and_wait = MagicMock()

        self.plugin._upgrade_callback_task(cb_api, 'ms1', None, True, True)
        # calls upgrade, reboots node to clear veritas issue, completes pending
        # yum transaction, runs upgrade again
        # and reboots node to clear veritas issue
        self.plugin._reboot_node_and_wait.assert_has_calls(
            [call(cb_api, 'ms1', False, True),
             call(cb_api, 'ms1', False, True)])
        mock_erago.assert_has_calls(
            [call(cb_api, ['ms1'], 'yum', 'upgrade_all_packages', timeout=1860, tolerate_warnings=True),
             call(cb_api, ['ms1'], 'yum', 'complete_transaction', timeout=1860, tolerate_warnings=True),
             call(cb_api, ['ms1'], 'yum', 'upgrade_all_packages', timeout=1860, tolerate_warnings=True)])

    def test_postlvm_filter_checks_bad_pvs(self):
        mock_erago, cb_api = MagicMock(), MagicMock()
        bad_pvs = "  /dev/vx/dmp/emc_clariion0_23            lvm2 ---  150.00g 150.00g\n/dev/vx/dmp/emc_clariion0_24s2          lvm2 ---   49.51g  49.51g\n  /dev/vx/dmp/emc_clariion0_79   neo4j_vg lvm2 a--  450.00g 100.00g"
        mock_erago.side_effect = [({'node1': bad_pvs}, {})]
        self.plugin._execute_rpc_and_get_output = mock_erago

        self.assertRaises(CallbackExecutionException,
                          self.plugin._postlvm_filter_checks,
                          cb_api, 'node1')

    def test_postlvm_filter_checks_bad_vgs(self):
        mock_erago, cb_api = MagicMock(), MagicMock()
        good_pvs = "  /dev/vx/dmp/vmdk0_0s2 vg_root lvm2 a--  39.51g 5.51g"
        bad_vgs = "neo4j_vg   1   1   0 wz--n- 450.00g 100.00g"
        mock_erago.side_effect = [({'node1': good_pvs}, {}),
                                  ({'node1': bad_vgs}, {}), ]
        self.plugin._execute_rpc_and_get_output = mock_erago

        self.assertRaises(CallbackExecutionException,
                          self.plugin._postlvm_filter_checks,
                          cb_api, 'node1')
        mock_erago.assert_has_calls([call(cb_api, ['node1'], 'lv', 'pvs'),
                                     call(cb_api, ['node1'], 'lv', 'vgs')])

    def test_postlvm_filter_checks_bad_lvs(self):
        mock_erago, cb_api = MagicMock(), MagicMock()
        good_pvs = "  /dev/vx/dmp/vmdk0_0s2 vg_root lvm2 a--  39.51g 5.51g"
        good_vgs = "neo4j_vg   1   1   0 wz--n- 450.00g 100.00g\nvg_app     1   3   0 wz--n- 150.00g  45.00g\nvg_root    1   3   0 wz--n-  49.51g  14.51g"
        bad_lvs = "/dev/vg_other/L_vg1_other_ 17179869184B swi-a-s--- [NOT-MOUNTED]\n/dev/vg_other/vg1_swap     2147483648B -wi-ao---- [SWAP]"
        mock_erago.side_effect = [({'node1': good_pvs}, {}),
                                  ({'node1': good_vgs}, {}),
                                  ({'node1': bad_lvs}, {}), ]
        self.plugin._execute_rpc_and_get_output = mock_erago

        self.assertRaises(CallbackExecutionException,
                          self.plugin._postlvm_filter_checks,
                          cb_api, 'node1')
        mock_erago.assert_has_calls([call(cb_api, ['node1'], 'lv', 'pvs'),
                                     call(cb_api, ['node1'], 'lv', 'vgs'),
                                     call(cb_api, ['node1'], 'lv', 'lvs')])

    @mock.patch('package_plugin.package_plugin.RpcCommandProcessorBase')
    def test_postlvm_filter_checks_bad_migrate_native(self, rcpb):
        mock_erago, cb_api = MagicMock(), MagicMock()
        good_pvs = "  /dev/vx/dmp/vmdk0_0s2 vg_root lvm2 a--  39.51g 5.51g"
        good_vgs = "neo4j_vg   1   1   0 wz--n- 450.00g 100.00g\nvg_app     1   3   0 wz--n- 150.00g  45.00g\nvg_root    1   3   0 wz--n-  49.51g  14.51g"
        good_lvs = "/dev/vg_root/L_vg1_root_ 17179869184B swi-a-s--- [NOT-MOUNTED]\n/dev/vg_root/vg1_root    17179869184B owi-aos--- /\n/dev/vg_root/vg1_swap     2147483648B -wi-ao---- [SWAP]"
        mock_erago.side_effect = [({'node1': good_pvs}, {}),
                                  ({'node1': good_vgs}, {}),
                                  ({'node1': good_lvs}, {})]
        rcpb().execute_rpc_and_process_result.return_value = ({},
            {'node1': ['node1 failed with message: /bin/ls: cannot access /etc/vx/.migrate_native: No such file or directory']}
                                   )
        self.plugin._execute_rpc_and_get_output = mock_erago
        self.assertRaises(CallbackExecutionException,
                          self.plugin._postlvm_filter_checks,
                          cb_api, 'node1')
        mock_erago.assert_has_calls([call(cb_api, ['node1'], 'lv', 'pvs'),
                                     call(cb_api, ['node1'], 'lv', 'vgs'),
                                     call(cb_api, ['node1'], 'lv', 'lvs')])
        rcpb().execute_rpc_and_process_result.assert_has_calls(
            [call(cb_api, ['node1'], 'dmp', 'check_migrate_native_exists_and_remove', None, None)],
            [call(cb_api, ['ms1'], 'yum', 'upgrade_all_packages', timeout=1860, tolerate_warnings=True)])

    def test_has_veritas_upgrade_errors(self):
        results = {'n1': ['something else', VERITAS_UG_ERR]}
        self.assertFalse(self.plugin._has_veritas_upgrade_errors(results, 'n2'))
        self.assertEqual({'n1': ['something else', VERITAS_UG_ERR]}, results)
        self.assertTrue(self.plugin._has_veritas_upgrade_errors(results, 'n1'))
        self.assertEqual({'n1': ['something else']}, results)
        self.assertFalse(self.plugin._has_veritas_upgrade_errors(results, 'n1'))

    def test_YumErrCheckRpcCommandProcessor(self):
        stoff = {
            "agent": "snapshot",
            "data": {
                "status": 0,
                "err": "",
                "path": "/trololo",
                "out": """--> Running transaction check
                ---> Package VRTSvxvm.x86_64 0:6.1.1.506-RHEL6 will be updated
                ---> Package VRTSvxvm.x86_64 0:6.1.1.507-RHEL6 will be an update
                --> Finished Dependency Resolution
                There are unfinished transactions remaining. You might consider running yum-complete-transaction first to finish them.
                Dependencies Resolved
                Updated:
                  VRTSvxvm.x86_64 0:6.1.1.507-RHEL6
                Complete!
                Installing file /etc/init.d/vxvm-boot
                creating VxVM device nodes under /dev
                FATAL: Module vxspec not found.
                FATAL: Module vxio not found.
                FATAL: Module vxdmp not found.
                ERROR: No appropriate modules found. Error in loading module \"vxdmp\". See documentation.
                WARNING: Unable to load new drivers.
                You should reboot the system to ensure that new drivers
                get loaded."""
            },
            "sender": "ms1",
            "statuscode": 0,
            "action": "create",
            "statusmsg": "OK"
        }
        yep = YumErrCheckRpcCommandProcessor()
        self.assertEqual(['ERROR: No appropriate modules found. '
                          'Error in loading module "vxdmp". '
                          'See documentation.'],
                         yep._errors_in_agent('ms1', stoff))

    def test_packages_require_services_restart(self):
        out = self._process_mco_output(mco_output_get_veritas_pkgs)
        packages = out[self.node1.hostname]
        upgrade_packages_data = self.plugin._packages_from_output(packages)
        restart_services, stop_commands, start_commands = self.plugin._packages_require_services_restart(self.node1, upgrade_packages_data)
        self.assertEqual(True, restart_services)
        self.assertEqual(['/bin/systemctl stop amf.service'], stop_commands)
        self.assertEqual(['/bin/systemctl start amf.service'], start_commands)

        # ----

        out = self._process_mco_output(mco_output_get_pkgs_multiple_vrts_packages)
        packages = out[self.node1.hostname]
        upgrade_packages_data = self.plugin._packages_from_output(packages)
        restart_services, stop_commands, start_commands = self.plugin._packages_require_services_restart(self.node1, upgrade_packages_data)
        self.assertEqual(True, restart_services)
        self.assertEqual(['/opt/VRTSvcs/bin/haconf -dump -makero',
                          '/opt/VRTSvcs/bin/hastop -local -force',
                          '/bin/systemctl stop vcsmm.service',
                          '/opt/VRTSvcs/bin/CmdServer -stop',
                          '/bin/systemctl stop amf.service',
                          '/bin/systemctl stop vxfen.service',
                          '/bin/systemctl stop gab.service',
                          '/bin/systemctl stop llt.service'], stop_commands)
        self.assertEqual(['/bin/systemctl start llt.service',
                          '/bin/systemctl start gab.service',
                          '/bin/systemctl start vxfen.service',
                          '/bin/systemctl start amf.service',
                          '/bin/systemctl start vcsmm.service',
                          '/opt/VRTSvcs/bin/hastart',
                          '/opt/VRTSvcs/bin/CmdServer',
                          '/opt/VRTSvcs/bin/haconf -makerw'], start_commands)

    @mock.patch('package_plugin.package_plugin.RpcCommandProcessorBase')
    def test_disable_vcs_services(self, rcpb):
        rcpb().execute_rpc_and_process_result.side_effect = RpcExecutionException('err')
        self.assertRaises(CallbackExecutionException,
                         self.plugin._disable_vcs_services,
                             MagicMock(), 'n1', []
                         )
        rcpb().execute_rpc_and_process_result.return_value = (None, ['errs'])
        self.assertRaises(CallbackExecutionException,
                         self.plugin._disable_vcs_services,
                             MagicMock(), 'n1', []
                         )

    @mock.patch('package_plugin.package_plugin.RpcCommandProcessorBase')
    def test_enable_vcs_services_start_puppet(self, rcpb):
        rcpb().execute_rpc_and_process_result.side_effect = RpcExecutionException('err')
        self.assertRaises(CallbackExecutionException,
                         self.plugin._enable_vcs_services_start_puppet,
                             MagicMock(), 'n1', []
                         )
        rcpb().execute_rpc_and_process_result.return_value = (None, ['errs'])
        self.assertRaises(CallbackExecutionException,
                         self.plugin._enable_vcs_services_start_puppet,
                             MagicMock(), 'n1', []
                         )

    def test_create_stop_services_task(self):
        desc_disable_vcs = 'Disable VCS services on node "n1"'
        desc_stop_puppet = 'Stop Puppet and disable VCS services on node "n1"'
        node = MagicMock(hostname='n1')
        test_data = [{'vxvm_upgrade_tasks': ['foo1'], "exp_desc": desc_disable_vcs},
                     {'vxvm_upgrade_tasks': [], "exp_desc": desc_stop_puppet}]
        upgrade_task = MagicMock()

        for entry in test_data:
            res = self.plugin._create_stop_services_task(node,
                                                         upgrade_task,
                                                         entry['vxvm_upgrade_tasks'], [])
            self.assertEqual(res.description, entry["exp_desc"])
            self.assertEqual(res.requires, set(entry['vxvm_upgrade_tasks']))

    def test_create_start_services_task(self):

        desc_enable_vcs = 'Enable VCS services and start Puppet on "n1"'
        desc_start_puppet = 'Start Puppet on node "n1"'

        node = MagicMock(hostname='n1')
        upgrade_item = MagicMock(vpath="/deployments/d1/clusters/c1/nodes/c1/nodes/n1/upgrade")
        upgrade_task = MagicMock(model_item=upgrade_item)
        test_data = [{'will_reboot': True, 'vxvm_upgrade_tasks': False, "exp_desc": desc_start_puppet},
                     {'will_reboot': False, 'vxvm_upgrade_tasks': False, "exp_desc": desc_enable_vcs},
                     {'will_reboot': False, 'vxvm_upgrade_tasks': True, "exp_desc": ''},
                     {'will_reboot': False, 'vxvm_upgrade_tasks': False, "exp_desc": desc_enable_vcs},
                     {'will_reboot': False, 'vxvm_upgrade_tasks': False, "exp_desc": desc_enable_vcs}]

        for entry in test_data:
            res = self.plugin._create_start_services_task(node,
                                                          upgrade_task,
                                                          entry['will_reboot'],
                                                          entry['vxvm_upgrade_tasks'], [])
            if entry['vxvm_upgrade_tasks'] == True:
                self.assertEqual(res, None)
            else:
                self.assertEqual(res.description, entry["exp_desc"])
                self.assertEqual(res.requires, set([upgrade_task]))

    @patch("package_plugin.package_plugin.PackagePlugin._is_upgrade_flag_set")
    def test_infra_update(self, mock_is_upgrade_flag_set):

        def is_upgrade_flag_set_side_effect(*args, **kwargs):

            if 'infra_update' in args[1]:
                return True
            else:
                return False

        mock_is_upgrade_flag_set.side_effect = is_upgrade_flag_set_side_effect

        ms = PkgMockNode('ms', 'ms1', 'ms')
        n1 = PkgMockNode('n1', 'node1')
        n2 = PkgMockNode('n2', 'node2')
        c1 = PkgMockVCSCluster('c1', 'cluster1')
        c1.nodes.extend([n1, n2])

        def mock_query(query_item_type, **kwargs):
            if 'vcs-cluster' == query_item_type:
                return [c1]
            elif 'ms' == query_item_type:
                return [ms]
            elif 'node' == query_item_type:
                return [n1, n2]
            else:
                return []

        context = Mock(query=mock_query)

        tasks = self.plugin.create_configuration(context)
        self.assertEquals(0, len(tasks))

    @patch("package_plugin.package_plugin.PackagePlugin._is_upgrade_flag_set")
    def test_ha_mngr_upgrade_only(self, mock_is_upgrade_flag_set):

        def is_upgrade_flag_set_side_effect(*args, **kwargs):

            if 'ha_manager_only' in args[1]:
                return True
            else:
                return False

        mock_is_upgrade_flag_set.side_effect = is_upgrade_flag_set_side_effect

        ms = PkgMockNode('ms', 'ms1', 'ms')
        n1 = PkgMockNode('n1', 'node1')
        n2 = PkgMockNode('n2', 'node2')
        c1 = PkgMockVCSCluster('c1', 'cluster1')
        c1.nodes.extend([n1, n2])

        def mock_query(query_item_type, **kwargs):
            if 'vcs-cluster' == query_item_type:
                return [c1]
            elif 'ms' == query_item_type:
                return [ms]
            elif 'node' == query_item_type:
                return [n1, n2]
            else:
                return []

        context = Mock(query=mock_query)

        tasks = self.plugin.create_configuration(context)
        self.assertEquals(10, len(tasks))

        self.assertEquals(tasks[0].description, 'Freeze all service groups on cluster "c1"')
        self.assertEquals(tasks[1].description, 'Stop Puppet and disable VCS services on node "node1"')
        self.assertEquals(tasks[3].description, 'Updating HA software on node "node1"')
        self.assertEquals(tasks[5].description, 'Configure HA software on node "node1"')
        self.assertEquals(tasks[7].description, 'Enable VCS services and start Puppet on node "node1"')
        self.assertEquals(tasks[9].description, 'Unfreeze all service groups on cluster "c1"')

    @mock.patch('package_plugin.package_plugin.run_rpc_command')
    def test_wait_for_mco_connectivity(self, m_run_rpc_cmd):
        cb_api = MagicMock()
        m_run_rpc_cmd.return_value = negative_mco_ping_response
        self.assertRaises(CallbackExecutionException,
                          self.plugin.wait_for_mco_connectivity,
                          cb_api, 'node1', max_wait=3)

    @mock.patch('package_plugin.package_plugin.run_rpc_command')
    def test_wait_for_mco_connectivity_planstopped_exception(self,
                                                           m_run_rpc_cmd):
        cb_api = MagicMock()
        cb_api.is_running.return_value = False
        m_run_rpc_cmd.return_value = negative_mco_ping_response
        self.assertRaises(PlanStoppedException,
                          self.plugin.wait_for_mco_connectivity,
                          cb_api, 'node1', max_wait=3)

    @patch("package_plugin.package_plugin.PackagePlugin._is_upgrade_flag_set")
    def test_redeploy_ms_upgrade_only(self, mock_is_upgrade_flag_set):

        mock_is_upgrade_flag_set.return_value = True

        def is_upgrade_flag_set_side_effect(*args, **kwargs):

            if 'redeploy_ms' in args[1]:
                return True
            else:
                return False

        mock_is_upgrade_flag_set.side_effect = is_upgrade_flag_set_side_effect

        ms = PkgMockNode('ms', 'ms1', 'ms', True)
        n1 = PkgMockNode('n1', 'node1')
        n1.is_ms = lambda: False
        n2 = PkgMockNode('n2', 'node2')
        n2.is_ms = lambda: False
        c1 = PkgMockVCSCluster('c1', 'cluster1')
        c1.nodes.extend([n1, n2])

        def mock_query(query_item_type, **kwargs):
            if 'vcs-cluster' == query_item_type:
                return []
            elif 'ms' == query_item_type:
                return [ms]
            elif 'node' == query_item_type:
                return [n1, n2]
            else:
                return []

        context = Mock(query=mock_query)

        tasks = self.plugin.create_configuration(context)
        self.assertEquals(3, len(tasks))
        self.assertEquals(tasks[0].description, 'Install package "pkg1" on node "ms1"')
        self.assertEquals(tasks[1].description, 'Install package "pkg2" on node "ms1"')
        self.assertEquals(tasks[2].description, 'Update versionlock file on node "ms1"')

    def test_is_upgrade_flag_set_True(self):

        def mock_query(item_type):
            if item_type == 'node':
                node = mock.MagicMock()
                node.query = mock.MagicMock(
                    return_value=[mock.MagicMock(redeploy_ms='true')])
                return [node]

        api = mock.MagicMock()
        api.query = mock_query
        result = self.plugin._is_upgrade_flag_set(api, 'redeploy_ms')
        self.assertTrue(result)

    def test_is_upgrade_flag_set_False(self):

        def mock_query(item_type):
            if item_type == 'node':
                node = mock.MagicMock()
                node.query = mock.MagicMock(
                    return_value=[mock.MagicMock(redeploy_ms='false')])
                return [node]

        api = mock.MagicMock()
        api.query = mock_query
        result = self.plugin._is_upgrade_flag_set(api, 'redeploy_ms')
        self.assertFalse(result)

    @mock.patch('package_plugin.package_plugin.wait_for_node_down')
    @mock.patch('package_plugin.package_plugin.wait_for_node_timestamp')
    @mock.patch('package_plugin.package_plugin.wait_for_node_puppet_applying_catalog_valid')
    @mock.patch('package_plugin.package_plugin.PuppetMcoProcessor')
    def test_reboot_node_and_wait(self, mock_pmp,
                                  mock_wait_for_node_puppet_applying,
                                  mock_wait_for_node_timestamp,
                                  mock_wait_for_node_down):
        self.plugin._execute_rpc_in_callback_task = MagicMock()
        self.plugin.wait_for_vcs = MagicMock()

        self.plugin._reboot_node_and_wait(self.callback_api, 'node1', False)

        self.assertEqual(call(self.callback_api, ['node1'], 'core', 'reboot'),
                         self.plugin._execute_rpc_in_callback_task.call_args)
        self.assertEqual(call(self.callback_api, ['node1'], True),
                         mock_wait_for_node_down.call_args)
        self.assertEqual(call(self.callback_api, ['node1'], mock.ANY, True),
                         mock_wait_for_node_timestamp.call_args)
        self.assertEqual(call(self.callback_api, ['node1'], True, loose=False),
                         mock_wait_for_node_puppet_applying.call_args)
        self.assertFalse(self.plugin.wait_for_vcs.called)

    @mock.patch('package_plugin.package_plugin.wait_for_node_down')
    @mock.patch('package_plugin.package_plugin.wait_for_node_timestamp')
    @mock.patch('package_plugin.package_plugin.wait_for_node_puppet_applying_catalog_valid')
    @mock.patch('package_plugin.package_plugin.PuppetMcoProcessor')
    def test_reboot_node_and_wait_not_based_on_puppet(self, mock_pmp,
                                  mock_wait_for_node_puppet_applying,
                                  mock_wait_for_node_timestamp,
                                  mock_wait_for_node_down):
        self.plugin._execute_rpc_in_callback_task = MagicMock()
        self.plugin.wait_for_vcs = MagicMock()

        self.plugin._reboot_node_and_wait(self.callback_api, 'node1', False,
                                          wait_based_on_puppet=False)

        self.assertEqual(call(self.callback_api, ['node1'], 'core', 'reboot'),
                         self.plugin._execute_rpc_in_callback_task.call_args)
        self.assertEqual(call(self.callback_api, ['node1'], True),
                         mock_wait_for_node_down.call_args)
        self.assertEqual(call(self.callback_api, ['node1'], mock.ANY, True),
                         mock_wait_for_node_timestamp.call_args)
        self.assertFalse(mock_wait_for_node_puppet_applying.called)
        self.assertEqual(call(self.callback_api, 'node1'),
                              self.plugin.wait_for_vcs.call_args)

    @patch('package_plugin.package_plugin.log.trace.info')
    @patch('package_plugin.package_plugin.time.sleep')
    @mock.patch('package_plugin.package_plugin.run_rpc_command')
    def test_wait_for_vcs(self, mock_run_rpc_command, mock_sleep, mock_log):
        mock_run_rpc_command.side_effect = [{'node1': {'data': 0}},
                                            {'node1': {'data': {'status': 0},
                                                       'errors': []}}
                                           ]
        cb_api = MagicMock()
        cb_api.is_running.return_value = True
        expected_log_calls = [call('Waiting for VCS on node node1'),
                              call('VCS has come up on node1')]
        self.plugin.wait_for_vcs(cb_api, 'node1')
        self.assertEqual(1, mock_sleep.call_count)
        self.assertEqual(expected_log_calls,
                         mock_log.call_args_list)

    @mock.patch('package_plugin.package_plugin.run_rpc_command')
    def test_wait_for_vcs_plan_stopped(self, mock_run_rpc_command):
        mock_run_rpc_command.return_value = {'node1': {'data': 0}}
        cb_api = MagicMock()
        cb_api.is_running.return_value = False
        self.assertRaises(PlanStoppedException,
                          self.plugin.wait_for_vcs, cb_api, 'node1')

    @patch('package_plugin.package_plugin.log.trace.info')
    @mock.patch('package_plugin.package_plugin.run_rpc_command')
    def test_wait_for_vcs_wait_exceeded(self, mock_run_rpc_command, mock_log):
        mock_run_rpc_command.return_value = {'node1': {'data': 0}}
        now = time.time()
        self.plugin.get_current_time = MagicMock(side_effect=[now, now + 1800])
        cb_api = MagicMock()
        cb_api.is_running.return_value = True
        self.assertRaises(CallbackExecutionException,
                          self.plugin.wait_for_vcs, cb_api, 'node1')

    def test_get_frozen_status(self):
        node1_out = u"""#Group          Attribute             System     Value
Grp_CS_c1_cups  Frozen                global     0
Grp_CS_c1_httpd Frozen                global     0
Grp_NIC_c1_br0  Frozen                global     1
Grp_NIC_c1_br6  Frozen                global     0
Grp_NIC_c1_eth4 Frozen                global     0
Grp_NIC_c1_eth5 Frozen                global     1"""
        self.plugin._execute_rpc_and_get_output = \
            MagicMock(return_value=({'node1': node1_out}, None))
        expected_groups = ['Grp_CS_c1_cups', 'Grp_CS_c1_httpd',
                           'Grp_NIC_c1_br0', 'Grp_NIC_c1_br6',
                           'Grp_NIC_c1_eth4', 'Grp_NIC_c1_eth5']
        expected_values = ['0', '0', '1', '0', '0', '1']

        groups, values = self.plugin._get_frozen_status(self.callback_api,
                                                        'node1')
        self.assertEqual(expected_groups, groups)
        self.assertEqual(expected_values, values)

    def test_gen_full_pkg_name(self):
        pkg1 = {'name': 'pkg1', 'version': 2, 'release': 3, 'arch': 'noarch'}
        pkg2 = {'name': 'pkg2', 'version': 2, 'release': 'Linux', 'arch': ''}
        self.assertEqual('pkg1-2-3.noarch.rpm',
                         self.plugin._gen_full_pkg_name(pkg1))
        self.assertEqual('pkg2-2_Linux.rpm',
                         self.plugin._gen_full_pkg_name(pkg2))

    @patch('package_plugin.package_plugin.PackagePlugin._execute_rpc_in_callback_task')
    @patch('package_plugin.package_plugin.PackagePlugin._do_vrts_rpc')
    def test_ha_upgrd_only_cnfgr_ha_cb(self, mock_vrts_rpc,
                                       mock_cb_rpc):
        self.plugin._ha_upgrd_only_cnfgr_ha_cb(self.callback_api, 'node1')
        expected_cb_rpc_call = call(self.callback_api, ['node1'],
                    'packagesimport', 'save_version_file',
                    {'destination_path': '/etc/VRTSvcs/conf/config/types.cf',
                     'source_path': '/etc/VRTSvcs/conf/types.cf'})
        expected_vrts_rpc_call = call(self.callback_api, 'node1',
                                      'update_licence')
        self.assertEqual([expected_cb_rpc_call], mock_cb_rpc.call_args_list)
        self.assertEqual([expected_vrts_rpc_call], mock_vrts_rpc.call_args_list)
