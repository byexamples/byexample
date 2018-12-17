# Byexample will look for examples in any language
# inside of the Ruby comment lines that are *consecutive*.
#
# This is an example in Python
# >>> 1 + 2
# 3
#
# And this is another example in Ruby (even if the # are misaligned)
  #    >> 2 + 2
    #  => 4

def awesome
    #####
    # Here is another example, Shell this time:
    # $ echo "Ruby rocks!"
    # Ruby rocks!
    #####
    return 1 \
        >> 2;          ## this line will not be confused with a Ruby example
end

