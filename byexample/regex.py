import sys
import re

escape = re.escape
compile = re.compile
match = re.match
fullmatch = re.fullmatch
search = re.search
sub = re.sub
subn = re.subn
split = re.split
findall = re.findall
finditer = re.finditer

# 'purge' is not public, it should not be needed

# Borrow from regex module its uppercase FLAGS
# so they are accessible from importing this module directly
module = sys.modules[__name__]
for sym in (sym for sym in dir(re) if sym.isupper()):
    setattr(module, sym, getattr(re, sym))
