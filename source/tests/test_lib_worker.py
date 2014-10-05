__author__ = 'alexander'

import unittest
import mock
from source.lib.worker import worker, worker_loop_function, DatabaseError, get_redirect_history_from_task


class MockConfig:
    def __init__(self):
        self.field = mock.Mock()

    def __getattr__(self, item):
        return self.field


class LibWorkerCase(unittest.TestCase):
    @mock.patch('source.lib.worker.get_tube', mock.Mock(side_effect=[
        mock.MagicMock(name="input_tube"),
        mock.MagicMock(name='output_tube')
    ]))
    @mock.patch('source.lib.worker.worker_loop_function')
    def test_worker_parent_exists(self, m_worker_loop_function):
        with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False])):
            worker(MockConfig(), 1)
        self.assertEqual(m_worker_loop_function.call_count, 1)

    @mock.patch('source.lib.worker.get_tube', mock.Mock(side_effect=[
        mock.MagicMock(name="input_tube"),
        mock.MagicMock(name='output_tube')
    ]))
    @mock.patch('source.lib.worker.worker_loop_function')
    def test_worker_parent_not_exists(self, m_worker_loop_function):
        with mock.patch('os.path.exists', mock.Mock(return_value=False)):
            worker(MockConfig(), 1)
        self.assertEqual(m_worker_loop_function.call_count, 0)

    def test_worker_loop_function_input_tube_timeout(self):
        input_tube = mock.MagicMock(name="input_tube")
        input_tube.take.return_value = None
        output_tube = mock.MagicMock(name='output_tube')
        with mock.patch('source.lib.worker.get_redirect_history_from_task') as m_get_redirect_history_from_task:
            worker_loop_function(MockConfig(), input_tube, output_tube)
        self.assertEqual(m_get_redirect_history_from_task.call_count, 0)

    def test_worker_loop_function_is_input_result_get_redirect_history_from_task_false(self):
        input_tube = mock.MagicMock(name="input_tube")
        output_tube = mock.MagicMock(name='output_tube')
        is_input = False
        data = 'data'
        with mock.patch('source.lib.worker.get_redirect_history_from_task', mock.Mock(return_value=(is_input, data))):
            worker_loop_function(MockConfig(), input_tube, output_tube)
        output_tube.put.assert_called_once_with(data)

    def test_worker_loop_function_is_input_result_get_redirect_history_from_task_true(self):
        input_tube = mock.MagicMock(name="input_tube")
        task = mock.MagicMock(name="task")
        input_tube.take.return_value = task
        task_meta_return_data = {'pri': 'unpacked_task_metadata'}
        task.meta.return_value = task_meta_return_data
        output_tube = mock.MagicMock(name='output_tube')
        is_input = True
        data = 'data'
        from source.lib.utils import Config
        config = Config()
        config.QUEUE_TAKE_TIMEOUT = 1
        config.HTTP_TIMEOUT = 1
        config.MAX_REDIRECTS = 1
        config.USER_AGENT = "Chrome/31.0.1650.63 Safari/537.36"
        config.RECHECK_DELAY = 1
        with mock.patch('source.lib.worker.get_redirect_history_from_task', mock.Mock(return_value=(is_input, data))):
            worker_loop_function(config, input_tube, output_tube)
        input_tube.put.assert_called_once_with(data, delay=config.RECHECK_DELAY, pri=task_meta_return_data['pri'])

    @mock.patch('source.lib.worker.get_redirect_history_from_task', mock.Mock(return_value=None))
    def test_worker_loop_function_task_ack(self):
        input_tube = mock.MagicMock(name="input_tube")
        task = mock.MagicMock(name="task")
        input_tube.take.return_value = task
        output_tube = mock.MagicMock(name='output_tube')
        worker_loop_function(MockConfig(), input_tube, output_tube)
        task.ack.assert_called_once_with()

    @mock.patch('source.lib.worker.get_redirect_history_from_task', mock.Mock(return_value=None))
    @mock.patch('source.lib.worker.logger')
    def test_worker_loop_function_task_ack_exception(self, m_logger):
        input_tube = mock.MagicMock(name="input_tube")
        task = mock.MagicMock(name="task")
        task.ack.side_effect = DatabaseError
        input_tube.take.return_value = task
        output_tube = mock.MagicMock(name='output_tube')
        worker_loop_function(MockConfig(), input_tube, output_tube)
        task.ack.assert_called_once_with()
        self.assertTrue(m_logger.exception.called)

    def test_get_redirect_history_from_task_error_in_history(self):
        task = mock.MagicMock(name='task')
        task.data.get.return_value = None
        history_types = 'ERROR'
        history_urls = ['urls']
        counters = 1
        with mock.patch('source.lib.worker.get_redirect_history',
                        mock.Mock(return_value=(history_types, history_urls, counters))):
            result = get_redirect_history_from_task(task, 0)
        self.assertTrue(result[0])
        self.assertEqual(result[1], task.data)

    def test_get_redirect_history_from_task_history(self):
        task = mock.MagicMock(name='task')
        history_types = 'OK'
        history_urls = ['urls']
        counters = 1
        with mock.patch('source.lib.worker.get_redirect_history',
                        mock.Mock(return_value=(history_types, history_urls, counters))):
            result = get_redirect_history_from_task(task, 0)
        self.assertFalse(result[0])
        self.assertNotEqual(result[1], task.data)

    @mock.patch('source.lib.worker.get_redirect_history', mock.Mock(return_value=('OK', None, 0)))
    def test_get_redirect_history_from_task_history_with_suspicious_in_data(self):
        task = mock.MagicMock(name='task')
        task.data = {
            'url': 'url',
            'recheck': False,
            'url_id': 1,
            'suspicious': 'doubt'
        }
        result = get_redirect_history_from_task(task, 0)
        self.assertEqual(result[1]['suspicious'], task.data['suspicious'])

    @mock.patch('source.lib.worker.get_redirect_history', mock.Mock(return_value=('OK', None, 0)))
    def test_get_redirect_history_from_task_history_with_out_suspicious_in_data(self):
        task = mock.MagicMock(name='task')
        task.data = {
            'url': 'url',
            'recheck': False,
            'url_id': 1,
        }
        result = get_redirect_history_from_task(task, 0)
        self.assertFalse('suspicious' in result[1])






