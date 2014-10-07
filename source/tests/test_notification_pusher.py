import unittest
import mock
from notification_pusher import notification_worker, done_with_processed_tasks, install_signal_handlers, main
import source.notification_pusher as notification_pusher


class MockConfig:
    def __init__(self):
        self.field = mock.Mock()

    def __getattr__(self, item):
        return self.field


def stop_loop(*args, **kwargs):
    notification_pusher.run_application = False


class NotificationPusherTestCase(unittest.TestCase):
    def setUp(self):
        from source.lib.utils import Config
        self.config = Config()
        self.config.LOGGING = {}
        self.config.SLEEP_ON_FAIL = 1

    @mock.patch('source.notification_pusher.current_thread', mock.Mock())
    @mock.patch('source.notification_pusher.requests.post', mock.Mock(return_value=mock.Mock()))
    @mock.patch('source.notification_pusher.json.dumps', mock.Mock())
    def test_notification_worker_ok(self):
        m_task_queue = mock.MagicMock()
        m_task = mock.MagicMock()
        data = {
            'id': 1,
            'callback_url': 'callback_url'
        }
        m_task.data.copy.return_value = data
        m_task_queue.task_id = 1
        notification_worker(m_task, m_task_queue)
        m_task_queue.put.assert_called_once_with((m_task, 'ack'))

    @mock.patch('source.notification_pusher.current_thread', mock.Mock())
    @mock.patch('source.notification_pusher.json.dumps', mock.Mock())
    def test_notification_worker_request_exception(self):
        m_task_queue = mock.MagicMock()
        m_task = mock.MagicMock()
        data = {
            'id': 1,
            'callback_url': 'callback_url'
        }
        m_task.data.copy.return_value = data
        m_task_queue.task_id = 1
        import requests
        with mock.patch('source.notification_pusher.requests.post', mock.Mock(side_effect=requests.RequestException)):
            notification_worker(m_task, m_task_queue)
        m_task_queue.put.assert_called_once_with((m_task, 'bury'))

    def test_done_with_processed_tasks(self):
        m_task_queue = mock.MagicMock()
        m_task_queue.qsize.return_value = 1
        m_task = mock.MagicMock()
        m_task.task_id = 1
        m_task_queue.get_nowait.return_value = (m_task, 'action_name.capitalize')
        done_with_processed_tasks(m_task_queue)
        m_task_queue.get_nowait.assert_called_once_with()

    @mock.patch('source.notification_pusher.logger.debug')
    def test_done_with_processed_tasks_empty_exception(self, m_logger):
        m_task_queue = mock.MagicMock()
        m_task_queue.qsize.return_value = 1
        from gevent import queue as gevent_queue
        m_task_queue.get_nowait.side_effect = gevent_queue.Empty
        done_with_processed_tasks(m_task_queue)
        self.assertTrue(m_logger.called)

    @mock.patch('source.notification_pusher.logger.exception')
    def test_done_with_processed_tasks_tarantool_database_error(self, m_logger):
        m_task_queue = mock.MagicMock()
        m_task_queue.qsize.return_value = 1
        m_task = mock.MagicMock()
        m_task.task_id = 1
        m_task_queue.get_nowait.return_value = (m_task, 'action_name')
        import tarantool
        m_task.action_name.side_effect = tarantool.DatabaseError
        done_with_processed_tasks(m_task_queue)
        self.assertTrue(m_logger.called)

    @mock.patch('source.notification_pusher.stop_handler', mock.Mock())
    @mock.patch('source.notification_pusher.gevent.signal')
    def test_install_signal_handlers(self, m_gevent_signal):
        import signal
        signals = [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT]
        install_signal_handlers()
        self.assertEqual(m_gevent_signal.call_count, len(signals))

    @mock.patch('source.notification_pusher.current_thread', mock.Mock())
    @mock.patch('source.notification_pusher.run_application', True)
    @mock.patch('source.notification_pusher.exit_code', 0)
    def test_stop_handler(self):
        sig = 1
        notification_pusher.stop_handler(sig)
        self.assertEqual(notification_pusher.run_application, False)
        self.assertEqual(notification_pusher.exit_code, notification_pusher.SIGNAL_EXIT_CODE_OFFSET + sig)

    @mock.patch('source.notification_pusher.parse_cmd_args', mock.Mock())
    @mock.patch('source.notification_pusher.dictConfig', mock.Mock())
    @mock.patch('source.notification_pusher.current_thread', mock.Mock())
    @mock.patch('source.notification_pusher.run_application', True)
    @mock.patch('source.notification_pusher.install_signal_handlers', mock.Mock())
    @mock.patch('source.notification_pusher.patch_all', mock.Mock())
    def test_main_all_success(self):
        config = MockConfig()
        with mock.patch('source.notification_pusher.exit_code', 0):
            with mock.patch('source.notification_pusher.configuration', mock.Mock(return_value=config)):
                with mock.patch('source.notification_pusher.main_loop',
                                mock.Mock(side_effect=stop_loop)) as main_loop_m:
                    ret = notification_pusher.main([1])
        main_loop_m.assert_called_once_with(config)
        self.assertEqual(ret, 0)

    @mock.patch('source.notification_pusher.parse_cmd_args', mock.Mock())
    @mock.patch('source.notification_pusher.dictConfig', mock.Mock())
    @mock.patch('source.notification_pusher.current_thread', mock.Mock())
    @mock.patch('source.notification_pusher.run_application', True)
    @mock.patch('source.notification_pusher.install_signal_handlers', mock.Mock())
    @mock.patch('source.notification_pusher.patch_all', mock.Mock())
    def test_main_all_unsuccess(self):
        config = MockConfig()
        with mock.patch('source.notification_pusher.exit_code', 0):
            with mock.patch('source.notification_pusher.configuration', mock.Mock(return_value=config)):
                with mock.patch('source.notification_pusher.main_loop',
                                mock.Mock(side_effect=Exception)) as main_loop_m:
                    with mock.patch('source.notification_pusher.sleep', mock.Mock(side_effect=stop_loop)) as m_sleep:
                        ret = notification_pusher.main([1])
        main_loop_m.assert_called_once_with(config)
        self.assertTrue(m_sleep.called)
        self.assertEqual(ret, 0)