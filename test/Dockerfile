FROM debian:buster-slim

RUN apt-get update     \
 && DEBIAN_FRONTEND=noninteractive apt-get --no-install-recommends install -y \
# Dependencies for Cling, the interpreter of C++
# Due licensing cling does not offer a binary for Debian so we need
# all of this to compile cling ourselves
        git         \
        gcc         \
        g++         \
        debhelper   \
        devscripts  \
        gnupg       \
        wget        \
        cmake       \
        python      \
        ca-certificates \
        sudo \
# Install Python, necessary to run byexample and to run the examples written
# in Python. Pick only Python 3
        python3     \
        python3-pip \
        python3-setuptools \
# Different shells to test the examples written in Shell
        dash        \
        ksh         \
        bash        \
# Interpreters for Ruby, Javascript and GDB
        ruby        \
        nodejs      \
        gdb         \
# Vim, of course, to write the tests.
        vim         \
        less        \
# Interpreters for PHP and Elixir
# (Elixir require a modern repository and Erlang/OTP platform)
        php-cli

RUN DEBIAN_FRONTEND=noninteractive apt-get --no-install-recommends install -y \
        elixir


# Erlang
#RUN wget https://packages.erlang-solutions.com/erlang-solutions_2.0_all.deb && dpkg -i erlang-solutions_2.0_all.deb \
# && DEBIAN_FRONTEND=noninteractive apt-get --no-install-recommends install -y \
#        esl-erlang  \
# &&  apt-get clean  \
# &&  rm -rf /var/lib/apt/lists/

# Cling compilation and installation
#RUN wget https://raw.githubusercontent.com/root-project/cling/master/tools/packaging/cpt.py \
# && chmod +x cpt.py         \
# && ./cpt.py --last-stable=tar -y --use-wget --no-test  \
# && ln -s /root/ci/build/builddir/bin/cling /usr/bin/cling


# Install byexample, you can run later "pip3 install -U byexample" to
# get the latest version or "pip3 install -e ." to install a dev version
CMD /bin/bash
