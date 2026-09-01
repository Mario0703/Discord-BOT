from bot.user_conversations import UserConversations


def test_user_conversation_mapping_is_saved_and_loaded(tmp_path):
    file_path = tmp_path / "conversations.json"

    conversations = UserConversations(file_path)
    conversations.update_conversation(12345, "conv_test")

    loaded = UserConversations(file_path)
    assert loaded.get_conversation(12345) == "conv_test"


def test_remove_conversation_deletes_mapping(tmp_path):
    file_path = tmp_path / "conversations.json"
    conversations = UserConversations(file_path)
    conversations.update_conversation(12345, "conv_test")

    assert conversations.remove_conversation(12345) == "conv_test"
    assert UserConversations(file_path).get_conversation(12345) is None
