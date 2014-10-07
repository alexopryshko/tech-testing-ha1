import unittest
import mock
from source.lib.utils import Config
from source import redirect_checker


def break_while(*args, **kwargs):
    redirect_checker.keep_running = False


class ActiveChildren:
    _mock = mock.Mock()

    def __init__(self, length):
        self.var = length * [self._mock]

    def __len__(self):
        return len(self.var)

    def __iter__(self):
        return iter(self.var)


class RedirectCheckerTestCase(unittest.TestCase):

    @mock.patch('os.getpid', mock.Mock(return_value=10))
    @mock.patch('source.redirect_checker.keep_running', mock.Mock())
    @mock.patch('source.redirect_checker.daemonize', mock.Mock())
    @mock.patch('source.redirect_checker.create_pidfile', mock.Mock())
    @mock.patch('source.redirect_checker.load_config_from_pyfile', mock.Mock())
    @mock.patch('source.redirect_checker.parse_cmd_args', mock.Mock())
    @mock.patch('source.redirect_checker.configuration', mock.Mock())
    @mock.patch('source.redirect_checker.dictConfig', mock.Mock())
    @mock.patch('source.redirect_checker.main_loop_function')
    def test_main_loop(self, m_main_loop_function):
        with mock.patch('source.redirect_checker.sleep', mock.Mock(side_effect=break_while)):
            redirect_checker.main([1])
        self.assertTrue(m_main_loop_function.called)

    @mock.patch('source.redirect_checker.worker', mock.Mock())
    @mock.patch('source.redirect_checker.check_network_status', mock.Mock(return_value=True))
    @mock.patch('source.redirect_checker.spawn_workers')
    def test_main_loop_function_network_access_on(self, m_spawn_workers):
        config = Config()
        config.CHECK_URL = 'url'
        config.HTTP_TIMEOUT = 1
        config.WORKER_POOL_SIZE = 5
        active_children = 1
        with mock.patch('source.redirect_checker.active_children', lambda: ActiveChildren(active_children)):
            redirect_checker.main_loop_function(config, 10)
        self.assertEqual(m_spawn_workers.called, True)

    @mock.patch('source.redirect_checker.worker', mock.Mock())
    @mock.patch('source.redirect_checker.check_network_status', mock.Mock(return_value=False))
    @mock.patch('source.redirect_checker.spawn_workers')
    def test_main_loop_function_network_access_off(self, m_spawn_workers):
        config = Config()
        config.CHECK_URL = 'url'
        config.HTTP_TIMEOUT = 1
        config.WORKER_POOL_SIZE = 50
        active_children = 10
        m_active_children = ActiveChildren(active_children)
        with mock.patch('source.redirect_checker.active_children', lambda: m_active_children):
            redirect_checker.main_loop_function(config, 10)
        self.assertEqual(len(m_active_children._mock.method_calls), active_children)
        for item in m_active_children._mock.method_calls:
            self.assertTrue(item[0] == 'terminate')

    @mock.patch('source.redirect_checker.worker', mock.Mock())
    @mock.patch('source.redirect_checker.check_network_status', mock.Mock(return_value=True))
    @mock.patch('source.redirect_checker.spawn_workers')
    def test_main_loop_function_worker_pool_size_equals_number_of_active_children(self, m_spawn_workers):
        config = Config()
        config.CHECK_URL = 'url'
        config.HTTP_TIMEOUT = 1
        config.WORKER_POOL_SIZE = 5
        active_children = 5

        with mock.patch('source.redirect_checker.active_children', lambda: ActiveChildren(active_children)):
            redirect_checker.main_loop_function(config, 10)
        self.assertEqual(m_spawn_workers.called, False)




