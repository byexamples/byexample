# PHP

To support PHP, ``byexample`` relays in the interactive mode of the ``php``
interpreter.

From PHP 5.1.0 this is available as long as the interpreter is compiled with
``readline`` suppport. See [interactive.php](https://www.php.net/manual/en/features.commandline.interactive.php).

> **Stability**: ``experimental`` - non backward compatibility changes are
> possible or even removal between versions (even patch versions).

### Variable and function definitions

Variables are local the scope and cannot be used inside of a function:
there are not global and there is not support for closures in PHP.

```php
php> $a = 2;
php> function foo($b) {
...>     echo $b;
...> }

php> foo($a);
2
```

Note how all the expressions must end with a ``;``.

### Syntax errors

``byexample`` will show you the syntax errors detected by ``php``.
You can even check for them as part of the normal output:

```php
php> for ($i = 0; $i < unknown; $i+=1) {
...>    echo $i;
...> }
PHP Notice:  Use of undefined constant unknown - assumed 'unknown' in php shell code on line <...>
```

## Known limitations

### Explicit pretty print

To pretty print a variable or expression, you need to call ``var_dump``
or ``print_r`` (or other that you want) *explicitly*.

```php
php> $arr = [1, [1.5, 1.6], 2];

php> $arr;  // nothing is printed

php> var_dump($arr);
array(3) {
  [0]=>
  int(1)
  [1]=>
  array(2) {
    [0]=>
    float(1.5)
    [1]=>
    float(1.6)
  }
  [2]=>
  int(2)
}

php> print_r($arr);         // byexample: +norm-ws
Array
(
    [0] => 1
    [1] => Array
        (
            [0] => 1.5
            [1] => 1.6
        )
    [2] => 2
)
```

``var_dump`` and ``print_r`` may add some extra spaces and
new lines (espcially ``print_r``) that will interfer with the output.
For complex structures using ``+norm-ws`` fixes the problem.

### Terminal support

To work with the current PHP interpreter, the ANSI
[terminal emulator](/{{ site.uprefix }}/advanced/terminal-emulation) is
enabled by default (``+term=ansi``) and cannot be disabled.

Also, the [terminal geometry](/{{ site.uprefix }}/advanced/geometry)
cannot by changed after launching the interpreter
so the option ``+geometry`` cannot be used in an example (but it can be
used from the command line)

The amount of rows of the terminal has a minimum value of 128 and this limit
is really important: if your outputs have more than 128 lines you will need
to increase the geometry or the results may be undefined.

The same for the width of the terminal: minimum of 128 columns.

### Echoed input lines

If the PHPsnippet has a very long line, greater than the terminal's width,
the last part of the line that does not fit in the terminal will be *echoed*
in the output of the example.

This is an annoying artifact due how ``php -a`` works.

A simple workaround is to make the lines of the code in the snippet
shorter or increase the
[terminal width](/{{ site.uprefix }}/advanced/geometry).

### Abort on a timeout

If a PHP example takes too long and
[timeout](/{{ site.uprefix }}/basic/timeout), the whole execution
timeout.

