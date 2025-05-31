from django.test import TestCase
from django.utils import timezone

from account.models import User, Profile
from videocall.models import VideoCall
from videocall.tests.utils import VideoCallTestBase
import datetime


class VideoCallModelTest(VideoCallTestBase):
    def test_string_representation(self):
        self.assertIn("→", str(self.call))

    def test_duration_none_if_not_ended(self):
        self.assertIsNone(self.call.duration())

    def test_duration_calculated(self):
        self.call.ended_at = self.call.started_at + datetime.timedelta(seconds=90)
        self.call.save()
        self.assertEqual(self.call.duration(), "1м 30с")
