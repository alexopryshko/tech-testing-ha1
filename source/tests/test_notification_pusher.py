import unittest
import mock
from notification_pusher import notification_worker


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

    

