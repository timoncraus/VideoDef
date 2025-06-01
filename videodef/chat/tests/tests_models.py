from chat.tests.utils import ChatTestBase
from chat.models import SmallChat


class ChatModelTest(ChatTestBase):
    def test_str_method(self):
        expected_str = f"{self.user1.username}: Привет!"
        self.assertEqual(str(self.message), expected_str)

    def test_str_method_new_chat(self):
        chat = SmallChat.objects.create(user1=self.user1, user2=self.user2)
        expected_str = f"Чат между пользователями {self.user1} и {self.user2}"
        self.assertEqual(str(chat), expected_str)
