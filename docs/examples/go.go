/*
 Byexample will look for examples in any language
 inside of the Go block-comments:

 This is an example in Python
 >>> 1 + 2
 3

 And this is another example in Go
 > 2 + 2
 : 4

 Here is another example in Go
 > func foo() {
 .   fmt.Println("hello!")
 . }

 > foo()
 hello!
*/

func awesome() {
    /*******
    * Here is another example, Shell this time, inside a block
    * comment:
    *
    * $ echo "Go rocks!"
    * Go rocks!
    *
    *******/
    return 1 \
        > 2;        // this line will not be confused with a Go example
}


