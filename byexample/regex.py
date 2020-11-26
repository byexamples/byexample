import sys
import regex


def compile(pattern, flags=0):
    return regex.compile(pattern, flags)


escape = regex.escape

# Borrow from regex module its uppercase FLAGS
# so they are accessible from importing this module directly
module = sys.modules[__name__]
for sym in (sym for sym in dir(regex) if sym.isupper()):
    setattr(module, sym, getattr(regex, sym))
