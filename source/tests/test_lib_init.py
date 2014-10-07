import unittest
import mock

from source.lib import check_for_meta, make_pycurl_request


class LibInitCase(unittest.TestCase):

    def test_check_for_meta(self):
        meta = '<html><head><meta http-equiv="refresh" content="0;URL=''http://thetudors.example.com/''" /></head></html>'
        self.assertEqual(check_for_meta(meta, ''), 'http://thetudors.example.com/')

    def test_check_for_bad_meta(self):
        meta = '<html><head><meta http-equiv="refresh" content="0;URL=''http://thetudors.example.com/''; sdfsdfsdf" /></head></html>'
        self.assertIsNone(check_for_meta(meta, ''))

    def _test_make_pycurl_request(self, useragent, m_curl=mock.MagicMock()):
        m_buffer = mock.MagicMock()
        m_buffer.getvalue = mock.Mock(return_value='test')

        m_curl.getinfo = mock.Mock(return_value='url')

        with mock.patch('source.lib.StringIO', mock.Mock(return_value=m_buffer)):
            with mock.patch('pycurl.Curl', mock.Mock(return_value=m_curl)):
                content, redirect_url = make_pycurl_request('url', 11, useragent)

        self.assertEqual(content, 'test', 'Wrong content')
        self.assertEqual('url', redirect_url, 'Wrong redirect url')

    def test_make_pycurl_request(self):
        self._test_make_pycurl_request(None)

    def test_make_pycurl_request_useragent(self):
        m_curl = mock.MagicMock()
        self._test_make_pycurl_request('mozilla', m_curl)

        m_curl.setopt.assert_any_call(m_curl.USERAGENT, 'mozilla')

    