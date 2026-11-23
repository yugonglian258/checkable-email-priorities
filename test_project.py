"""Regression checks for inference and the HTTP action boundary."""
import copy
import json
import unittest

import app
import triage


class InferenceTests(unittest.TestCase):
    def test_revised_fixture_labels(self):
        now = triage.datetime.fromisoformat(app.DATA['now'])
        for case in app.DATA['cases'].values():
            for thread in case['threads']:
                with self.subTest(thread=thread['id']):
                    actual = triage.classify(app.THREADS[thread['id']], now, 'v2')
                    self.assertEqual(actual['suggestion'], thread['expected'])

    def test_baseline_reproduces_quoted_date_failure(self):
        result = triage.classify(app.THREADS['B1'], triage.datetime.fromisoformat(app.DATA['now']), 'v1')
        self.assertEqual(result['suggestion'], 'ACTION_TODAY')

    def test_relative_today_uses_message_date(self):
        thread = dict(app.THREADS['A1'], latest_received='2026-10-21T09:00:00+01:00')
        result = triage.classify(thread, triage.datetime.fromisoformat(app.DATA['now']), 'v2')
        self.assertEqual(result['suggestion'], 'NEEDS_REVIEW')

    def test_missing_text_and_future_timestamp(self):
        for change in ({'latest': ''}, {'latest_received': '2026-10-23T09:00:00+01:00'}):
            result = triage.classify(dict(app.THREADS['A1'], **change), triage.datetime.fromisoformat(app.DATA['now']), 'v2')
            self.assertEqual(result['suggestion'], 'NEEDS_REVIEW')

    def test_invalid_and_conflicting_dates(self):
        for message in ('Please reply by 2026-02-30.', 'Please reply by 2026-10-22 or 2026-10-23.'):
            result = triage.classify(dict(app.THREADS['A1'], latest=message), triage.datetime.fromisoformat(app.DATA['now']), 'v2')
            self.assertEqual(result['suggestion'], 'NEEDS_REVIEW')


class ActionTests(unittest.TestCase):
    def setUp(self):
        self.session = triage.LabelSession()

    def choose(self, thread='A1', choice='Confirm', version='v2'):
        return app.act(self.session, dict(action='choose', thread=thread, choice=choice, version=version))

    def test_suggestion_does_not_save(self):
        app.state(self.session)
        app.act(self.session, dict(action='refresh', version='v1'))
        self.assertEqual(self.session.labels, {})

    def test_confirm_correction_and_undo(self):
        self.choose()
        corrected = self.choose('B1', 'Later', 'v1')
        self.assertEqual(corrected['labels'], {'A1': 'ACTION_TODAY', 'B1': 'NOT_TODAY'})
        undone = app.act(self.session, dict(action='undo'))
        self.assertEqual(undone['labels'], {'A1': 'ACTION_TODAY'})

    def test_unresolved_confirm_is_rejected(self):
        with self.assertRaises(ValueError):
            self.choose('B1')
        self.assertEqual(self.session.labels, {})

    def test_unsure_saves_nothing(self):
        result = self.choose('B1', "I don't know")
        self.assertFalse(result['feedback']['changed'])
        self.assertEqual(result['labels'], {})

    def test_sessions_are_separate(self):
        self.choose()
        self.assertEqual(app.state(triage.LabelSession())['labels'], {})

    def test_bad_request_preserves_labels(self):
        self.choose()
        before = copy.deepcopy(self.session.labels)
        for request in ({'action': 'choose', 'thread': 'missing'},
                        {'action': 'choose', 'thread': 'A1', 'choice': 'delete'},
                        {'action': 'undo', 'version': 'unknown'}):
            with self.assertRaises((ValueError, TypeError)):
                app.act(self.session, request)
            self.assertEqual(self.session.labels, before)

    def test_client_suggestion_cannot_override_server_result(self):
        with self.assertRaises(ValueError):
            app.act(self.session, dict(action='choose', thread='B1', choice='Confirm',
                                       suggestion='ACTION_TODAY', version='v2'))
        self.assertFalse(self.session.labels)


if __name__ == '__main__':
    unittest.main(verbosity=2)
