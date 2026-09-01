from bot.token_usage import TokenUsage


def test_token_usage_report_groups_recent_usage_by_user(tmp_path):
    usage = TokenUsage(tmp_path / "token_usage.json")

    usage.record(12345, 100, 25)
    usage.record(12345, 50, 10)
    usage.record(67890, 20, 5)

    assert usage.report() == {
        "12345": {"input": 150, "output": 35},
        "67890": {"input": 20, "output": 5},
    }
