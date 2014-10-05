__author__ = 'alexander'

import unittest
import mock
import urllib2
import socket

from source.lib.utils import daemonize, \
    create_pidfile, \
    parse_cmd_args, \
    spawn_workers, \
    check_network_status, \
    Config, \
    load_config_from_pyfile


class LibUtilsCase(unittest.TestCase):
    @mock.patch('os._exit')
    def test_daemonize_from_master(self, m_exit):
        pid = 1
        with mock.patch('os.fork', mock.Mock(return_value=pid)):
            daemonize()
        m_exit.assert_called_once_with(0)

    def test_daemonize_from_master_exception(self):
        with mock.patch('os.fork', mock.Mock(side_effect=OSError("error"))) as m_fork:
            self.assertRaises(Exception, daemonize)
        self.assertEqual(m_fork.call_count, 1)

    @mock.patch('os._exit')
    def test_daemonize_from_child_unsuccess(self, m_exit):
        pid = 0
        with mock.patch('os.fork', mock.Mock(return_value=pid)) as m_fork:
            with mock.patch('os.setsid', mock.Mock()) as m_setsid:
                daemonize()
        m_setsid.assert_called_once_with()
        self.assertEqual(m_fork.call_count, 2)
        self.assertFalse(m_exit.called)

    @mock.patch('os._exit')
    def test_daemonize_from_child_success(self, m_exit):
        master_pid = 0
        child_pid = 1
        with mock.patch('os.fork', mock.Mock(side_effect=[master_pid, child_pid])) as m_fork:
            with mock.patch('os.setsid', mock.Mock()) as m_setsid:
                daemonize()
        m_setsid.assert_called_once_with()
        self.assertEqual(m_fork.call_count, 2)
        m_exit.assert_called_once_with(0)

    def test_daemonize_from_child_exception(self):
        with mock.patch('os.fork', mock.Mock(side_effect=[0, OSError("err")])) as m_fork:
            with mock.patch('os.setsid', mock.Mock()) as m_setsid:
                self.assertRaises(Exception, daemonize)
        m_setsid.assert_called_once_with()
        self.assertEqual(m_fork.call_count, 2)

    @mock.patch('os.getpid', mock.Mock(return_value=1))
    def test_create_pidfile(self):
        pid = 1
        m_open = mock.mock_open()
        with mock.patch('source.lib.utils.open', m_open, create=True):
            create_pidfile('/file/path')
        m_open.assert_called_once_with('/file/path', 'w')
        m_open().write.assert_called_once_with(str(pid))

    def test_load_config_from_pyfile(self):
        config = Config()
        config.TEST = 1
        config.TEST2 = {"TEST3": 2}
        exec_file = {
            "TEST": 1,
            "TEST2": {
                "TEST3": 2
            },
            "fake": 3
        }
        with mock.patch('source.lib.utils.execfile_ret', mock.Mock(return_value=exec_file)):
            result = load_config_from_pyfile('test_file_path/')
        self.assertEqual(result.__dict__, config.__dict__)

    def test_parse_cmd_args(self):
        args = ["-c", "config", "-d"]
        parsed_args = parse_cmd_args(args)
        import argparse
        self.assertEqual(argparse.Namespace(config='config', daemon=True, pidfile=None), parsed_args)

    def test_spawn_workers(self):
        num_of_workers = 5
        with mock.patch('source.lib.utils.Process') as m_process:
            spawn_workers(num_of_workers, None, None, None)
        self.assertEqual(m_process.call_count, num_of_workers)

    @mock.patch('source.lib.utils.urllib2.urlopen', mock.Mock())
    def test_check_network_status_success(self):
        self.assertTrue(check_network_status(None, None))

    @mock.patch('source.lib.utils.urllib2.urlopen', mock.Mock(side_effect=urllib2.URLError("error")))
    def test_check_network_status_url_error(self):
        self.assertFalse(check_network_status(None, None))

    @mock.patch('source.lib.utils.urllib2.urlopen', mock.Mock(side_effect=socket.error("error")))
    def test_check_network_status_socket_error(self):
        self.assertFalse(check_network_status(None, None))

    @mock.patch('source.lib.utils.urllib2.urlopen', mock.Mock(side_effect=ValueError("error")))
    def test_check_network_status_value_error(self):
        self.assertFalse(check_network_status(None, None))




