import sys
import re

escape = re.escape
compile = re.compile

# Borrow from regex module its uppercase FLAGS
# so they are accessible from importing this module directly
module = sys.modules[__name__]
for sym in (sym for sym in dir(re) if sym.isupper()):
    setattr(module, sym, getattr(re, sym))
