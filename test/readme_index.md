In theory a ``README.md`` in the root project in ``github`` should be
enough to set up a ``github-page``, with the content of that file as the
content of the index of the web page.

Unfortunately this is not working and an explicit ``index.md`` needs to
be created in the ``docs`` folder.

Symlinks and other tricks didn't work so the only solution that I
found was to have two copies of the files: the ``README.md`` for ``github``
and the ``docs/index.md`` for ``github-pages``.

Both should be almost the same

```shell
$ diff README.md docs/index.md      # byexample: +norm-ws
1,2d0
< # ``byexample``
<

```

