from crm.admin import deactivate
from crm.users import get_user


def test_deactivate():
    assert deactivate(2)
    assert get_user(2).active is False
    assert not deactivate(99)
