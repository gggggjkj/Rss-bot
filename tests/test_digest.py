import json
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

import digest

NOW = datetime(2026, 11, 26, 6, tzinfo=timezone.utc)
RSS = b'''<rss><channel>
<item><title>New &amp; useful</title><link>https://example.com/1</link><pubDate>Thu, 26 Nov 2026 05:00:00 GMT</pubDate><description>&lt;b&gt;News&lt;/b&gt; today</description></item>
<item><title>Old</title><link>https://example.com/2</link><pubDate>Tue, 24 Nov 2026 05:00:00 GMT</pubDate></item>
<item><title>Missing date</title><link>https://example.com/3</link></item>
</channel></rss>'''
ATOM = b'''<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Atom item</title><link href="https://example.com/atom"/><updated>2026-11-25T12:00:00Z</updated><summary>Hello</summary></entry></feed>'''


class DigestTests(unittest.TestCase):
    def test_parse_rss_and_atom_with_time_filter(self):
        entries = digest.parse_feed(RSS, 'RSS', NOW)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['title'], 'New & useful')
        self.assertEqual(entries[0]['text'], 'News today')
        self.assertEqual(digest.parse_feed(ATOM, 'Atom', NOW)[0]['url'], 'https://example.com/atom')

    def test_collect_deduplicates_and_tolerates_failure(self):
        config = {'feeds': [{'name': 'one', 'url': 'https://one'}, {'name': 'two', 'url': 'https://two'}, {'name': 'bad', 'url': 'https://bad'}]}
        with patch('digest.request', side_effect=[RSS, RSS, OSError('failure')]):
            articles, failures = digest.collect(config, NOW)
        self.assertEqual(len(articles), 1)
        self.assertEqual(failures, ['bad'])

    def test_rsshub_base_config_used_when_environment_empty(self):
        config = {'rsshub_base_url': 'https://rss.example', 'feeds': [{'name': 'route', 'route': '/news'}]}
        with patch.dict('os.environ', {'RSSHUB_BASE_URL': ''}), patch('digest.request', return_value=RSS) as req:
            digest.collect(config, NOW)
        req.assert_called_once_with('https://rss.example/news')

    def test_summary_and_discord_payload(self):
        article = {'title': 'Title', 'source': 'Source', 'text': 'Text', 'url': 'https://example.com'}
        result = {'choices': [{'message': {'content': '摘要 [1]'}}]}
        with patch('digest.request', return_value=json.dumps(result).encode()) as req:
            self.assertEqual(digest.summarize([article], 'key', 'model'), '摘要 [1]')
            self.assertEqual(req.call_args.args[1]['model'], 'model')
        with patch('digest.request') as req:
            digest.send_discord('https://discord.example/webhook', 'x' * 4001)
            self.assertEqual(req.call_count, 3)
            for call in req.call_args_list:
                self.assertLessEqual(len(call.args[1]['content']), 2000)
                self.assertEqual(call.args[1]['allowed_mentions'], {'parse': []})

    def test_split_preserves_text(self):
        text = 'a' * 1999 + '\n' + 'b' * 2000
        self.assertEqual('\n'.join(digest.split_message(text)), text)


if __name__ == '__main__':
    unittest.main()
