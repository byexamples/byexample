/* Byexample will look for examples in any language
 * inside of the PHP multi line comments.
 *
 * This is an example in Python
 * >>> 1 + 2
 * 3

 Of course, we support PHP examples as well!
 php> $i = 0;
 php> print_r($i + 2);
 2

 php> function foo() {
 ...>   echo("hello!");
 ...> }

 php> foo();
 hello!
 */

int awesome() {
    /*
     * Here is another example, Shell this time:
     * $ echo "PHP rocks!"
     * PHP rocks!
     * */
    return 1
}

/* */
// Byexample will not search for examples in this kind of
// comments
//
// So this, is not an example
// >>> 3 * 4
// infinite
//
/* */
