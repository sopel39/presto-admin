# -*- coding: utf-8 -*-

#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os

from tests.product.base_product_case import BaseProductTestCase, PRESTO_RPM, \
    LOCAL_RESOURCES_DIR


class TestPackageInstall(BaseProductTestCase):
    def test_package_install(self):
        self.install_presto_admin()
        self.upload_topology()
        self.copy_presto_rpm_to_master()
        self.run_prestoadmin('package install /mnt/presto-admin/%s'
                             % PRESTO_RPM)
        for container in self.all_hosts():
            self.assert_installed(container)

    def assert_installed(self, container):
        check_rpm = self.exec_create_start(container, 'rpm -q presto')
        self.assertEqual(PRESTO_RPM[:-4] + '\n', check_rpm)

    def assert_uninstalled(self, container):
        self.assertRaisesRegexp(OSError, 'package presto is not installed',
                                self.exec_create_start,
                                container, 'rpm -q presto')

    def test_install_coord_using_h(self):
        self.install_presto_admin()
        self.upload_topology()
        self.copy_presto_rpm_to_master()
        self.run_prestoadmin('package install /mnt/presto-admin/%s -H master'
                             % PRESTO_RPM)
        self.assert_installed(self.master)
        for slave in self.slaves:
            self.assert_uninstalled(slave)

    def test_install_worker_using_h(self):
        self.install_presto_admin()
        self.upload_topology()
        self.copy_presto_rpm_to_master()
        self.run_prestoadmin('package install /mnt/presto-admin/%s '
                             '-H slave1' % PRESTO_RPM)

        self.assert_installed(self.slaves[0])
        self.assert_uninstalled(self.master)
        self.assert_uninstalled(self.slaves[1])
        self.assert_uninstalled(self.slaves[2])

    def test_install_workers_using_h(self):
        self.install_presto_admin()
        self.upload_topology()
        self.copy_presto_rpm_to_master()
        self.run_prestoadmin('package install /mnt/presto-admin/%s '
                             '-H slave1,slave2' % PRESTO_RPM)

        self.assert_installed(self.slaves[0])
        self.assert_installed(self.slaves[1])
        self.assert_uninstalled(self.master)
        self.assert_uninstalled(self.slaves[2])

    def test_install_exclude_coord(self):
        self.install_presto_admin()
        self.upload_topology()
        self.copy_presto_rpm_to_master()
        self.run_prestoadmin('package install /mnt/presto-admin/%s -x master'
                             % PRESTO_RPM)

        self.assert_uninstalled(self.master)
        for slave in self.slaves:
            self.assert_installed(slave)

    def test_install_exclude_worker(self):
        self.install_presto_admin()
        self.upload_topology()
        self.copy_presto_rpm_to_master()
        self.run_prestoadmin('package install /mnt/presto-admin/%s -x slave1'
                             % PRESTO_RPM)
        self.assert_uninstalled(self.slaves[0])
        self.assert_installed(self.slaves[1])
        self.assert_installed(self.master)
        self.assert_installed(self.slaves[2])

    def test_install_exclude_workers(self):
        self.install_presto_admin()
        self.upload_topology()
        self.copy_presto_rpm_to_master()
        self.run_prestoadmin('package install /mnt/presto-admin/%s '
                             '-x slave1,slave2' % PRESTO_RPM)

        self.assert_uninstalled(self.slaves[0])
        self.assert_uninstalled(self.slaves[1])
        self.assert_installed(self.master)
        self.assert_installed(self.slaves[2])

    def test_install_invalid_path(self):
        self.install_presto_admin()
        self.upload_topology()
        self.copy_presto_rpm_to_master()
        self.assertRaisesRegexp(OSError,
                                'Fatal error: error: '
                                '/mnt/presto-admin/invalid-path/presto.rpm: '
                                'open failed: No such file or directory',
                                self.run_prestoadmin,
                                'package install '
                                '/mnt/presto-admin/invalid-path/presto.rpm')

    def test_install_no_path_arg(self):
        self.install_presto_admin()
        self.upload_topology()
        self.copy_presto_rpm_to_master()
        self.assertRaisesRegexp(OSError,
                                'Fatal error: Missing argument local_path: '
                                'Absolute path to the rpm to be installed',
                                self.run_prestoadmin, 'package install')

    def test_install_already_installed(self):
        self.install_presto_admin()
        self.upload_topology()
        self.copy_presto_rpm_to_master()
        self.run_prestoadmin(
            'package install /mnt/presto-admin/%s -H master' % PRESTO_RPM)
        self.assert_installed(self.master)
        cmd_output = self.run_prestoadmin(
            'package install /mnt/presto-admin/%s -H master' % PRESTO_RPM)
        expected = ['Deploying rpm...',
                    'Package deployed successfully on: master',
                    "Warning: [master] sudo() received nonzero return code 1 "
                    "while executing 'rpm -i "
                    "/opt/prestoadmin/packages/presto-0.101-1.0.x86_64.rpm'!",
                    '', '', '[master] out: ',
                    '[master] out: \tpackage presto-0.101-1.0.x86_64 is '
                    'already installed']

        actual = cmd_output.splitlines()
        self.assertEqual(sorted(expected), sorted(actual))

    def test_install_not_an_rpm(self):
        self.install_presto_admin()
        self.upload_topology()
        self.assertRaisesRegexp(OSError,
                                'Fatal error: error: not an rpm package',
                                self.run_prestoadmin,
                                'package install '
                                '/etc/opt/prestoadmin/config.json')

    def test_install_rpm_with_missing_jdk(self):
        self.install_presto_admin()
        self.upload_topology()
        self.copy_presto_rpm_to_master()
        self.exec_create_start(self.master, 'rpm -e jdk1.8.0_40-1.8.0_40-fcs')
        self.assertRaisesRegexp(OSError,
                                'package jdk1.8.0_40-1.8.0_40-fcs is not '
                                'installed',
                                self.exec_create_start,
                                self.master, 'rpm -q jdk1.8.0_40-1.8.0_40-fcs')

        cmd_output = self.run_prestoadmin(
            'package install /mnt/presto-admin/%s -H master' % PRESTO_RPM)
        self.assertEqualIgnoringOrder(
            self.jdk_not_found_error_message(), cmd_output)

    def jdk_not_found_error_message(self):
        with open(os.path.join(LOCAL_RESOURCES_DIR, 'jdk_not_found.txt')) as f:
            jdk_not_found_error = f.read()
        return jdk_not_found_error

    def test_install_rpm_missing_dependency(self):
        self.install_presto_admin()
        self.upload_topology()
        self.copy_presto_rpm_to_master()
        self.exec_create_start(self.master, 'rpm -e --nodeps python-2.6.6')
        self.assertRaisesRegexp(OSError,
                                'package python-2.6.6 is not installed',
                                self.exec_create_start,
                                self.master, 'rpm -q python-2.6.6')

        cmd_output = self.run_prestoadmin(
            'package install /mnt/presto-admin/%s -H master'
            % PRESTO_RPM)
        expected = 'Deploying rpm...\n\nWarning: [master] sudo() received ' \
                   'nonzero return code 1 while executing ' \
                   '\'rpm -i /opt/prestoadmin/packages/' \
                   'presto-0.101-1.0.x86_64.rpm\'!\n\nPackage deployed ' \
                   'successfully on: master\n[master] out: error: ' \
                   'Failed dependencies:\n[master] out: 	python >= 2.6 is ' \
                   'needed by presto-0.101-1.0.x86_64\n[master] out: 	' \
                   'python <= 2.7 is needed by presto-0.101-1.0.x86_64\n' \
                   '[master] out: '
        self.assertEqualIgnoringOrder(expected, cmd_output)

    def test_install_rpm_with_nodeps(self):
        self.install_presto_admin()
        self.upload_topology()
        self.copy_presto_rpm_to_master()
        self.exec_create_start(self.master, 'rpm -e --nodeps python-2.6.6')
        self.assertRaisesRegexp(OSError,
                                'package python-2.6.6 is not installed',
                                self.exec_create_start,
                                self.master, 'rpm -q python-2.6.6')

        cmd_output = self.run_prestoadmin(
            'package install /mnt/presto-admin/%s -H master --nodeps'
            % PRESTO_RPM)
        expected = 'Deploying rpm...\nPackage deployed successfully on: master' \
                   '\nPackage installed successfully on: master'

        self.assertEqualIgnoringOrder(expected, cmd_output)