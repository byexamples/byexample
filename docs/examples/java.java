/* Byexample will look for examples in any language
 * inside of the C/C++ multi line comments.
 *
 * This is an example in Python
 * >>> 1 + 2
 * 3

 Of course, we support Java examples as well!
 j> int i = 0;
 j> i + 2
 => 2

 j> void foo() {
 ..   System.out.println("hello!");
 .. }

 j> foo();
 hello!
 */

class Super {
    public int awesome() {
        /*
         * Here is another example, Shell this time:
         * $ echo "Java rocks!"
         * Java rocks!
         * */
        return 1;
    }
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
