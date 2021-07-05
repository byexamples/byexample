/* Byexample will look for examples in any language
 * inside of the C/C++ multi line comments.
 *
 * This is an example in Python
 * >>> 1 + 2
 * 3

 Of course, we support C/C++ examples as well!
 ?: int i = 0;
 ?: i + 2
 (int) 2

 ?: #include <iostream>
 ?: void foo() {
 ::   std::cout << "hello!\n";
 :: }

 ?: foo();
 hello!
 */

int awesome() {
    /*
     * Here is another example, Shell this time:
     * $ echo "C/C++ rocks!"
     * C/C++ rocks!
     * */
    return 1;
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
