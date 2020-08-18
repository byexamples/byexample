int mylibC_foo(int j) {
    // this line is valid in C but not in C++
    // because in C++ 'new' is a reserved word
    int new = j + 1;
    return new;
}
