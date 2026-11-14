"""Time helpers."""


def format_duration(seconds):
    hours, rest = divmod(seconds, 3600)
    return f"{hours}h{rest // 60}m"
