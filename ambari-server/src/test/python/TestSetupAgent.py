'''
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''
import subprocess
from mock.mock import MagicMock
from unittest import TestCase
from mock.mock import patch
import sys
setup_agent = __import__('setupAgent')

class TestSetupAgent(TestCase):

  @patch("sys.exit")
  @patch("socket.socket")
  def test_checkServerReachability(self, socket_mock, exit_mock):
      setup_agent.checkServerReachability("localhost", 8080)
      self.assertTrue(socket_mock.called)
      s = socket_mock.return_value
      s.connect = MagicMock()
      def side_effect():
          raise Exception(1, "socket is closed")
      s.connect.side_effect = side_effect
      try:
          setup_agent.checkServerReachability("localhost", 8080)
          self.fail("Should throw exception because port is closed")
      except Exception:
      # Expected
          self.assertTrue(exit_mock.called)
          pass


  @patch.object(setup_agent, 'execOsCommand')
  def test_configureAgent(self, execOsCommand_mock):
    # Test if expected_hostname is passed
    hostname = "test.hst"
    setup_agent.configureAgent(hostname)
    cmdStr = str(execOsCommand_mock.call_args_list[0][0])
    self.assertTrue(hostname in cmdStr)


  @patch.object(setup_agent, 'execOsCommand')
  @patch("os.environ")
  @patch("subprocess.call")
  @patch("time.sleep")
  def test_runAgent(self, sleep_mock, call_mock, environ_mock, execOsCommand_mock):
    expected_hostname = "test.hst"
    passphrase = "passphrase"
    call_mock.return_value = 0
    execOsCommand_mock.return_value = {'log': 'log', 'exitstatus': 0}
    # Test if expected_hostname is passed
    ret = setup_agent.runAgent(passphrase, expected_hostname)
    cmdStr = str(call_mock.call_args_list[0][0])
    self.assertTrue(expected_hostname in cmdStr)
    self.assertEqual(ret, 0)
    self.assertTrue(sleep_mock.called)
    # Key 'log' not found
    execOsCommand_mock.return_value = None
    ret = setup_agent.runAgent(passphrase, expected_hostname)
    cmdStr = str(call_mock.call_args_list[0][0])
    self.assertTrue(expected_hostname in cmdStr)
    self.assertEqual(ret, 1)
    # Retcode id not 0
    execOsCommand_mock.return_value = {'log': 'log', 'exitstatus': 2}
    ret = setup_agent.runAgent(passphrase, expected_hostname)
    cmdStr = str(call_mock.call_args_list[0][0])
    self.assertTrue(expected_hostname in cmdStr)
    self.assertEqual(ret, 2)


  @patch.object(setup_agent, 'getAvaliableAgentPackageVersions')
  @patch.object(setup_agent, 'is_suse')
  @patch.object(setup_agent, 'is_ubuntu')
  @patch.object(setup_agent, 'findNearestAgentPackageVersion')
  def test_returned_optimal_version_is_initial_on_suse(self, findNearestAgentPackageVersion_method, is_ubuntu_mock,
                                                       is_suse_method, getAvaliableAgentPackageVersions_method):
    getAvaliableAgentPackageVersions_method.return_value = {"exitstatus": 0, "log": "1.1.1"}
    is_suse_method.return_value = True
    is_ubuntu_mock.return_value = False

    projectVersion = "1.1.1"
    result_version = setup_agent.getOptimalVersion(projectVersion)
    self.assertTrue(findNearestAgentPackageVersion_method.called)
    self.assertTrue(result_version["exitstatus"] == 1)
    pass

  @patch.object(setup_agent, 'getAvaliableAgentPackageVersions')
  @patch.object(setup_agent, 'is_suse')
  @patch.object(setup_agent, 'is_ubuntu')
  @patch.object(setup_agent, 'findNearestAgentPackageVersion')
  def test_returned_optimal_version_is_initial_on_ubuntu(self, findNearestAgentPackageVersion_method, is_ubuntu_mock,
                                                       is_suse_method, getAvaliableAgentPackageVersions_method):
    getAvaliableAgentPackageVersions_method.return_value = {"exitstatus": 0, "log": "1.1.1"}
    is_suse_method.return_value = False
    is_ubuntu_mock.return_value = True

    projectVersion = "1.1.1"
    result_version = setup_agent.getOptimalVersion(projectVersion)
    self.assertTrue(findNearestAgentPackageVersion_method.called)
    self.assertTrue(result_version["exitstatus"] == 1)
    pass

  @patch.object(setup_agent, 'is_suse')
  @patch.object(setup_agent, 'is_ubuntu')
  @patch.object(setup_agent, 'findNearestAgentPackageVersion')
  def test_returned_optimal_version_is_nearest_on_suse(self, findNearestAgentPackageVersion_method,
                                                       is_ubuntu_method,
                                                       is_suse_method):
    is_suse_method.return_value = True
    is_ubuntu_method.return_value = False

    projectVersion = ""
    nearest_version = projectVersion + "1.1.1"
    findNearestAgentPackageVersion_method.return_value = {
      "exitstatus" : 0,
      "log": [nearest_version, ""]
    }

    result_version = setup_agent.getOptimalVersion(projectVersion)
    self.assertTrue(findNearestAgentPackageVersion_method.called)
    self.assertTrue(result_version["exitstatus"] == 1)
    pass

  @patch.object(setup_agent, 'is_suse')
  @patch.object(setup_agent, 'is_ubuntu')
  @patch.object(setup_agent, 'findNearestAgentPackageVersion')
  def test_returned_optimal_version_is_nearest_on_ubuntu(self, findNearestAgentPackageVersion_method,
                                                       is_ubuntu_method,
                                                       is_suse_method):
    is_suse_method.return_value = False
    is_ubuntu_method.return_value = True

    projectVersion = ""
    nearest_version = projectVersion + "1.1.1"
    findNearestAgentPackageVersion_method.return_value = {
      "exitstatus" : 0,
      "log": [nearest_version, ""]
    }

    result_version = setup_agent.getOptimalVersion(projectVersion)
    self.assertTrue(findNearestAgentPackageVersion_method.called)
    self.assertTrue(result_version["exitstatus"] == 1)
    pass

  @patch.object(setup_agent, 'getAvaliableAgentPackageVersions')
  @patch.object(setup_agent, 'is_suse')
  @patch.object(setup_agent, 'is_ubuntu')
  @patch.object(setup_agent, 'findNearestAgentPackageVersion')
  def test_returned_optimal_version_is_initial(self, findNearestAgentPackageVersion_method,
                                               is_ubuntu_method,
                                               is_suse_method, getAvaliableAgentPackageVersions_method):
    getAvaliableAgentPackageVersions_method.return_value = {"exitstatus": 0, "log": "1.1.1"}
    is_suse_method.return_value = False
    is_ubuntu_method.return_value = False

    projectVersion = "1.1.1"
    result_version = setup_agent.getOptimalVersion(projectVersion)
    self.assertTrue(findNearestAgentPackageVersion_method.called)
    self.assertTrue(result_version["log"] == projectVersion)
    pass


  @patch.object(setup_agent, 'getAvaliableAgentPackageVersions')
  @patch.object(setup_agent, 'is_suse')
  @patch.object(setup_agent, 'is_ubuntu')
  @patch.object(setup_agent, 'findNearestAgentPackageVersion')
  def test_returned_optimal_version_is_default(self, findNearestAgentPackageVersion_method,
                                               is_ubuntu_method,
                                               is_suse_method, getAvaliableAgentPackageVersions_method):
    getAvaliableAgentPackageVersions_method.return_value = {"exitstatus": 0, "log": "1.1.1"}
    is_suse_method.return_value = False
    is_ubuntu_method.return_value = False
    findNearestAgentPackageVersion_method.return_value = {
      "exitstatus" : 0,
      "log": ["1.1.1.1", ""]
    }

    projectVersion = "1.1.1"
    result_version = setup_agent.getOptimalVersion(projectVersion)

    self.assertTrue(findNearestAgentPackageVersion_method.called)
    self.assertTrue(result_version["exitstatus"] == 1)

  @patch.object(subprocess, 'Popen')
  def test_execOsCommand(self, Popen_mock):
    self.assertFalse(setup_agent.execOsCommand("hostname -f") == None)

  @patch("os.path.isfile")
  @patch("__builtin__.open")
  def test_is_suse(self, open_mock, isfile_mock):
    self.assertFalse(setup_agent.is_suse())
    isfile_mock.return_value = True
    f = open_mock.return_value
    f.read.return_value = " suse "
    self.assertTrue(setup_agent.is_suse())

  @patch("os.path.isfile")
  @patch("__builtin__.open")
  def test_is_ubuntu(self, open_mock, isfile_mock):
    isfile_mock.return_value = True
    f = open_mock.return_value
    f.read.return_value = " ubuntu "
    self.assertTrue(setup_agent.is_ubuntu())

  @patch.object(setup_agent, 'isAgentPackageAlreadyInstalled')
  @patch.object(setup_agent, 'runAgent')
  @patch.object(setup_agent, 'configureAgent')
  @patch.object(setup_agent, 'installAgent')
  @patch.object(setup_agent, 'is_suse')
  @patch.object(setup_agent, 'is_ubuntu')
  @patch.object(setup_agent, 'getOptimalVersion')
  @patch.object(setup_agent, 'checkServerReachability')
  @patch("sys.exit")
  @patch("os.path.dirname")
  @patch("os.path.realpath")
  def test_setup_agent_main(self, dirname_mock, realpath_mock, exit_mock, checkServerReachability_mock,
                            getOptimalVersion_mock, is_ubuntu_mock, is_suse_mock,
                            installAgent_mock, configureAgent_mock, runAgent_mock,
                            isAgentPackageAlreadyInstalled_mock):
    installAgent_mock.return_value = {'log': 'log', 'exitstatus': 0}
    runAgent_mock.return_value = 0
    getOptimalVersion_mock.return_value = {'log': '1.1.2, 1.1.3, ', 'exitstatus': 1}
    setup_agent.main(("setupAgent.py","agents_host","password", "server_hostname","1.1.1","8080"))
    self.assertTrue(exit_mock.called)
    self.assertTrue(getOptimalVersion_mock.called)
    exit_mock.reset_mock()
    getOptimalVersion_mock.reset_mock()

    getOptimalVersion_mock.return_value = {'log': '1.1.1', 'exitstatus': 0}
    isAgentPackageAlreadyInstalled_mock.return_value = False
    is_suse_mock.return_value = True
    is_ubuntu_mock.return_value = False
    setup_agent.main(("setupAgent.py","agents_host","password", "server_hostname","1.1.1","8080"))
    self.assertTrue(exit_mock.called)
    self.assertTrue(getOptimalVersion_mock.called)
    self.assertTrue(isAgentPackageAlreadyInstalled_mock.called)
    self.assertTrue(installAgent_mock.called)
    self.assertFalse(is_suse_mock.called)
    self.assertFalse(is_ubuntu_mock.called)
    exit_mock.reset_mock()
    getOptimalVersion_mock.reset_mock()
    isAgentPackageAlreadyInstalled_mock.reset_mock()
    is_suse_mock.reset_mock()
    is_ubuntu_mock.reset_mock()
    installAgent_mock.reset_mock()

    getOptimalVersion_mock.return_value = {'log': '', 'exitstatus': 0}
    setup_agent.main(("setupAgent.py","agents_host","password", "server_hostname","1.1.1","8080"))
    self.assertTrue(exit_mock.called)
    self.assertTrue(getOptimalVersion_mock.called)
    self.assertFalse(isAgentPackageAlreadyInstalled_mock.called)
    self.assertFalse(is_suse_mock.called)
    self.assertFalse(is_ubuntu_mock.called)

    exit_mock.reset_mock()
    getOptimalVersion_mock.reset_mock()
    isAgentPackageAlreadyInstalled_mock.reset_mock()
    is_suse_mock.reset_mock()
    is_ubuntu_mock.reset_mock()
    installAgent_mock.reset_mock()

    is_suse_mock.return_value = False
    is_ubuntu_mock.return_value = False
    getOptimalVersion_mock.return_value = {'log': '1.1.1', 'exitstatus': 0}
    setup_agent.main(("setupAgent.py","agents_host","password", "server_hostname","1.1.1","8080"))
    self.assertTrue(exit_mock.called)
    self.assertTrue(getOptimalVersion_mock.called)
    self.assertTrue(isAgentPackageAlreadyInstalled_mock.called)
    self.assertTrue(installAgent_mock.called)
    self.assertFalse(is_suse_mock.called)
    self.assertFalse(is_ubuntu_mock.called)
    exit_mock.reset_mock()
    getOptimalVersion_mock.reset_mock()
    isAgentPackageAlreadyInstalled_mock.reset_mock()
    exit_mock.reset_mock()
    getOptimalVersion_mock.reset_mock()
    isAgentPackageAlreadyInstalled_mock.reset_mock()
    is_suse_mock.reset_mock()
    is_ubuntu_mock.reset_mock()
    installAgent_mock.reset_mock()

    setup_agent.main(("setupAgent.py","agents_host","password", "server_hostname","{ambariVersion}","8080"))
    self.assertTrue(getOptimalVersion_mock.called)
    self.assertTrue(exit_mock.called)
    exit_mock.reset_mock()
    getOptimalVersion_mock.reset_mock()
    setup_agent.main(("setupAgent.py","agents_host","password", "server_hostname","null","8080"))
    self.assertTrue(exit_mock.called)
    self.assertTrue(getOptimalVersion_mock.called)
    exit_mock.reset_mock()
    is_suse_mock.return_value = False
    is_ubuntu_mock.return_value = False
    setup_agent.main(("setupAgent.py","agents_host","password", "server_hostname","null","null"))
    self.assertTrue(exit_mock.called)
    exit_mock.reset_mock()
    def side_effect(retcode):
      raise Exception(retcode, "sys.exit")
    exit_mock.side_effect = side_effect
    #if "yum -y install --nogpgcheck ambari-agent" return not 0 result
    installAgent_mock.return_value = {'log': 'log', 'exitstatus': 1}
    try:
        setup_agent.main(("setupAgent.py","agents_host","password", "server_hostname","1.1.1","8080"))
        self.fail("Should throw exception")
    except Exception:
        # Expected
        pass
    self.assertTrue(exit_mock.called)
    installAgent_mock.reset_mock()
    exit_mock.reset_mock()
    #if suse
    is_suse_mock.return_value = True
    is_ubuntu_mock.return_value = False
    #if "zypper install -y ambari-agent" return not 0 result
    installAgent_mock.return_value = {'log': 'log', 'exitstatus': 1}
    try:
        setup_agent.main(("setupAgent.py","agents_host","password", "server_hostname","1.1.1","8080"))
        self.fail("Should throw exception")
    except Exception:
        # Expected
        pass
    self.assertTrue(exit_mock.called)
    exit_mock.reset_mock()
    #if ubuntu
    is_suse_mock.return_value = False
    is_ubuntu_mock.return_value = True

    installAgent_mock.return_value = {'log': 'log', 'exitstatus': 1}
    try:
        setup_agent.main(("setupAgent.py","agents_host","password", "server_hostname","1.1.1","8080"))
        self.fail("Should throw exception")
    except Exception:
        # Expected
        pass
    self.assertTrue(exit_mock.called)

  @patch.object(setup_agent, 'execOsCommand')
  def test_findNearestAgentPackageVersion(self, execOsCommand_mock):
      setup_agent.findNearestAgentPackageVersion("1.1.1")
      self.assertTrue(execOsCommand_mock.called)
      execOsCommand_mock.reset_mock()
      setup_agent.findNearestAgentPackageVersion("")
      self.assertTrue(execOsCommand_mock.called)

  @patch.object(setup_agent, 'execOsCommand')
  def test_isAgentPackageAlreadyInstalled(self, execOsCommand_mock):
      execOsCommand_mock.return_value = {"exitstatus": 0, "log": "1.1.1"}
      self.assertTrue(setup_agent.isAgentPackageAlreadyInstalled("1.1.1"))
      self.assertTrue(execOsCommand_mock.called)
      execOsCommand_mock.reset_mock()
      execOsCommand_mock.return_value = {"exitstatus": 1, "log": "1.1.1"}
      self.assertFalse(setup_agent.isAgentPackageAlreadyInstalled("1.1.1"))
      self.assertTrue(execOsCommand_mock.called)

  @patch.object(setup_agent, 'execOsCommand')
  def test_getAvaliableAgentPackageVersions(self, execOsCommand_mock):
      setup_agent.getAvaliableAgentPackageVersions()
      self.assertTrue(execOsCommand_mock.called)

  @patch.object(setup_agent, 'execOsCommand')
  def test_installAgent(self, execOsCommand_mock):
    setup_agent.installAgent("1.1.1")
    self.assertTrue(execOsCommand_mock.called)
