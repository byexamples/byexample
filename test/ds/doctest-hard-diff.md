
```python
>>> import pprint

>>> def set_breakpoint(func, lineno, file):
...     addr = 0x18172  # random
...     path = 'workdir-random-path-here/' + file
...     bkt = {'addr': hex(addr),
...            'file': file,
...            'fullname': path,
...            'func': func,
...            'line': str(lineno),
...            'original-location': addr,
...            'thread': ['1', '1'],
...            'thread-groups': ['i1'],
...            'times': '0',
...            'type': 'breakpoint'}
...
...     return {'debugger-id': 0x1221, # more random stuff
...             'results': {'bkpts': [bkt]},
...             'type': 'Sync'}

>>> b1 = set_breakpoint('main', 5, 'example.c')
>>> pprint.pprint(b1)           # doctest: +ELLIPSIS
{'debugger-id': ...
 'results': {'bkpts': [{'addr': ...,
                        'file': 'example.c',
                        'fullname': ...,
                        'func': 'main',
                        'line': '5',
                        'original-location': ...,
                        'thread': ['1', '1'],
                        'thread-group': ['i1'],
                        'times': '0',
                        'type': 'breakpoint'}]},
 'type': 'Sync'}

>>> True    # this should not be executed if the above example failed and FAIL_FAST is enabled
False

```
