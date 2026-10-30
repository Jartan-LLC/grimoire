"""Print every user as CSV."""

from crm.users import USERS, get_user

for user_id in sorted(USERS):
    user = get_user(user_id)
    print(f"{user.id},{user.name},{user.email}")
