from package_name.modules.hello import hello


def test_hello(capsys):
    hello()
    captured = capsys.readouterr()
    assert captured.out == "Hello\n"
