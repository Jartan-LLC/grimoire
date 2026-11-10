from pubsubby import Client


def test_subscribe_delivers():
    got = []
    client = Client("h")
    client.subscribe("t", cb=got.append)
    client.deliver("t", "m")
    assert got == ["m"]
