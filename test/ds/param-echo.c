#include <stdio.h>
int main(int argc, char* argv[]) {
    for (; argc > 0; --argc)
        printf("%s\n", argv[argc-1]);
    return 0;
}
