# Byexample will look for examples in any language
# inside of the PowerShell comment lines that are *consecutive*.
#
# This is an example in Python
# >>> 1 + 2
# 3
#
# And this is another example in PowerShell
#    PS> 2 + 2
#    4

# Of course, we support PowerShell examples as well!
# PS> $i = 0;
# PS> $i + 2
# 2
#
# PS> function Get-Foo {
# -->   echo "hello!"
# --> }
#
# PS> Get-Foo
# hello!

function Be-Awesome {
    #####
    # Here is another example, Shell this time:
    # $ echo "PowerShell rocks!"
    # PowerShell rocks!
    #####

    # But this will not be confused with a Shell
    # example even if it begins with a $ because
    # it is not inside of a comment.
    $ok = 1
}

