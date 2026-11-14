from mealplan.plan import weekly_plan


def test_seven_dinners():
    dinners = list("abcdefg")
    assert list(weekly_plan(dinners).values()) == dinners
