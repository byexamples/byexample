This is a quick introduction to the database schema.
    >>> import sqlite3
    >>> c = sqlite3.connect(':memory:')       # in memory, useful for testing
    >>> _ = c.executescript(open('test/ds/stock.sql').read())  # byexample: +fail-fast

Get the stocks' prices
    >>> _ = c.execute('select price from stocks')

Do not forget to close the connection
    >>> c.close()                             # byexample: -skip

