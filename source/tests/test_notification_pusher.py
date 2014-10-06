import unittest
import mock
from notification_pusher import notification_worker, done_with_processed_tasks, install_signal_handlers, main


class MockConfig:
    def __init__(self):
        self.field = mock.Mock()

    def __getattr__(self, item):
        return self.field


class NotificationPusherTestCase(unittest.TestCase):
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
        import source.notification_pusher as notification_pusher
        sig = 1
        notification_pusher.stop_handler(sig)
        self.assertEqual(notification_pusher.run_application, False)
        self.assertEqual(notification_pusher.exit_code, notification_pusher.SIGNAL_EXIT_CODE_OFFSET + sig)

