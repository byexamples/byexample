Ensure that the current git tag (version of `byexample`) is written
correctly in different parts of the project, source code and
documentation.

```shell
$ git describe --abbrev=0
<current-tag>

$ grep -c "<current-tag>" README.md
1

$ grep -c "<current-tag>" byexample/__init__.py
1

$ grep -c "rev: <current-tag>" docs/recipes/pre-commit.md
2
```
