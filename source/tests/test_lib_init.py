import unittest
import mock
import rstr

from source.lib import check_for_meta, \
    make_pycurl_request, \
    fix_market_url, \
    get_url, REDIRECT_HTTP, COUNTER_TYPES, get_counters, get_redirect_history, prepare_url, REDIRECT_META, prepare_url


class LibInitCase(unittest.TestCase):

    def test_check_for_meta(self):
        meta = self._get_html_with_redirect('http://thetudors.example.com/')
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

    def test_fix_market_url(self):
        result = fix_market_url('market://test/app')
        self.assertEqual('http://play.google.com/store/apps/test/app', result)

    def test_get_url_http(self):
        m_redirect_url = 'index.html'
        m_redirect_type = REDIRECT_HTTP

        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=('<html></html>', m_redirect_url))):
            redirect_url, redirect_type, content = get_url('http://tech-mail.ru', 11)

            self.assertEquals(m_redirect_url, redirect_url)
            self.assertEquals(m_redirect_type, redirect_type)

    def test_get_counters(self):
        page = str()

        for counter_name, regexp in COUNTER_TYPES:
            page += rstr.xeger(regexp)

        counters = get_counters(page)

        self.assertEqual(len(counters), len(COUNTER_TYPES))

    def test_get_redirect_history(self):
        m_types = [REDIRECT_META, REDIRECT_META]
        m_urls = ['url1', 'url2', 'url3']

        with mock.patch('source.lib.get_url', mock.Mock(side_effect=[
            (m_urls[1], m_types[0], self._get_html_with_redirect(m_urls[1])),
            (m_urls[2], m_types[1], self._get_html_with_redirect(m_urls[2])),
            (None, None, '<html></html>')
        ])):
            types, urls, counters = get_redirect_history(m_urls[0], timeout=11)
            self.assertEquals(urls, m_urls)
            self.assertEquals(types, m_types)

    def test_get_url_error(self):
        with mock.patch('source.lib.make_pycurl_request', mock.Mock(side_effect=ValueError)):
            url, redirect_type, content = get_url('url', 11)

            self.assertEquals(redirect_type, 'ERROR')

    def test_prepare_none_url(self):
        self.assertEqual(None, prepare_url(None))

    def _get_html_with_redirect(self, url):
        return '<html><head><meta http-equiv="refresh" content="0;URL=''{0}''" /></head></html>'.format(url)

    def test_get_redirect_history_ok(self):
        m_types = [REDIRECT_META, REDIRECT_META]
        m_urls = ['http://odnoklassniki.ru/', 'url1', 'url3']

        with mock.patch('source.lib.get_url', mock.Mock(side_effect=[
            (m_urls[1], m_types[0], self._get_html_with_redirect(m_urls[1])),
            (m_urls[2], m_types[1], self._get_html_with_redirect(m_urls[2])),
            (None, None, '<html></html>')
        ])):
            types, urls, counters = get_redirect_history(m_urls[0], timeout=11)

            self.assertEquals(len(urls), 1)

    def test_get_url_redirect(self):
        with mock.patch('source.lib.make_pycurl_request',  mock.Mock(return_value=(self._get_html_with_redirect(
        'http://odnoklassniki.ru/st.redirect'), None))):
            url, type, content = get_url('http://odnoklassniki.ru/st.redirect', 11)
            self.assertEqual(type, REDIRECT_META)

    def test_prepare_url_exception(self):
        m_netlock = mock.MagicMock()
        m_netlock.encode = mock.Mock(side_effect=UnicodeError)
        m_urlparse = mock.Mock(return_value=('', m_netlock, '', '', '', ''))

        with mock.patch('source.lib.urlparse', m_urlparse):
            try:
                prepare_url('url')
            except UnicodeError:
                self.fail()

    def test_check_for_meta_wrong(self):
        self.assertEqual(check_for_meta('', ''), None)

    def test_check_for_meta_wrong_url(self):
        self.assertEqual(
            check_for_meta('<html><head><meta http-equiv="refresh" content="0;URwqeL=''http://thetudors.example.com/''" /></head></html>', ''),
            None
        )

    def test_get_url_ok_login(self):
        with mock.patch('source.lib.make_pycurl_request',  mock.Mock(return_value=(self._get_html_with_redirect(
        'http://odnoklassniki.ru/st.redirect'), 'http://odnoklassniki.ru/st.redirect'))):
            url, type, content = get_url('http://odnoklassniki.ru/st.redirect', 11)
            self.assertEqual(type, None)

    def test_get_url_market(self):
        with mock.patch('source.lib.make_pycurl_request',
                        mock.Mock(return_value=
                        (self._get_html_with_redirect('market://url/index.html'), None)
                        )),\
            mock.patch('source.lib.fix_market_url') as m_fix_market:
            get_url('market://url', 11)

            self.assertTrue(m_fix_market.called)

    def test_fix_market_absolute(self):
        self.assertEqual(fix_market_url('path'), 'http://play.google.com/store/apps/path')

    def test_get_redirect_history_error(self):
        m_types = ['ERROR', REDIRECT_META]
        m_urls = ['http://url', 'http://url2', 'http://url3']

        with mock.patch('source.lib.get_url', mock.Mock(side_effect=[
            (m_urls[1], m_types[0], self._get_html_with_redirect('http://url2')),
            (m_urls[2], m_types[1], self._get_html_with_redirect('http://url3')),
            (None, None, '<html></html>')
        ])):
            history_types, history_urls, counters = get_redirect_history(m_urls[0], 11)
            self.assertEquals(len(history_urls), 2)


