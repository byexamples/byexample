from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL

NOTE = INFO + 1
CHAT = INFO - 1
TRACE = DEBUG - 1


def str_to_level(s):
    s = s.upper()
    return globals()[s]
