/* Byexample will look for examples in any language
 * inside of the Javascript multi line comments.
 *
 * This is an example in Python
 * >>> 1 + 2
 * 3

 Of course, we support Javascript examples as well!
 > var i = 0;
 > i + 2
 2

 > function foo() {
 .   console.log("hello!");
 . }

 > foo();
 hello!
 */

function awesome() {
    /*
     * Here is another example, Shell this time:
     * $ echo "Javascript rocks!"
     * Javascript rocks!
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
