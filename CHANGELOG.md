## 9.2.0 (828b26e) - Wed Jun 24 14:48:01 2020 +0000

### Changes from previous version:

### Enhancements
 - new option: +force-echo-filtering+input, allow the user to force
   the echo filtering needing in some cases. It is an experimental
   feature (see 451b218a)

### Fixes
 - fix the zone finder for python modules (docstring): now find the
   examples only in docstrings and in the strings at the module level
   (see 6bc53be7)

### Others
 - minor fixes in the tests of Elixir, Python and GDB
   (see 0e7eb38a, 696f1dbf, 274f177e)

## 9.1.1 (93eb446) - Mon Jun 15 13:50:47 2020 +0000

### Changes from previous version:

### Enhancements
 - Support Python 3.8 and 3.9 (issue #116)

### Others
 - Enforce disable cache for Python 3.8 and up. This is an undocumented
   feature that never left the 'experimental'.

## 9.1.0 (1b16ea4) - Mon Jan 27 15:27:53 2020 +0000

### Changes from previous version:

### Enhancements
 - new option: +input, allow the user to type input in a running example
(1070aa40, 72e6cb9) (closes #78)
 - InputPrefixNotFound subclass of Timeout exception (ce3f7a94)
 - new option: +input-prefix-range, control min/max prefix required for
inputs (bd281952)
 - minor enhancements in the log's comments (20a07ab3)

### Incompatible changes (lib)
 - _expect_prompt can wait for other things than prompts (3174d48)
 - track remaining time with Countdown (5f995f, 895537f, cc1f4759,
911719e)
 - capture_tag_regexs now returns a namedtuple (5985e6d)
### Others
 - refactor and code relocation of Example/Where/Zone (6935cf9)
 - _exec_and_wait now receive the example as a context (6b862ee)
 - other renames (8278a74)

## 9.0.1 (17f9303) - Tue Dec 31 01:44:58 2019 +0000

### Changes from previous version:

### Enhancements
 - Configure the prompts (and pretty printer) of Python after
initialized the interpreter (#106)
 - Allow `byexample` to use Django's manage.py shell (#105)

### Others:
 - Reformat the source code to follow the PEP 8 using yapf. Now this is
part of the automated tests to keep the code in good shape. (f4d2af69,
d92e6012)

## 9.0.0 (cb4a1e9) - Sun Dec 8 20:12:22 2019 +0000

This is an inflexion point in byexample as it officially drops support for
Python 2.7.

### Changes from previous version:

### Fixes
 - Fix recover mechanism (not always worked), still not perfect. (b48c4aed2)

### Enhancements
 - Allow to wait for a custom prompt during the spawn (84b6d5ed)
 - PHP interpreter (experimental) (eedb025b52)
 - Elixir interpreter (experimental) (8462de107, 1fce7ecce)
 - Refactor get output without echoed input (C++ and PHP) (2e4cfd19)
 - Several enhancements in the log systems.

### Incompatible changes (examples)
 - Byexample does not longer support Python 2.7 (2.x). Python 2.7 will reach
to its end of life on January 1st 2020. Due this, having magical code in
the PythonRunner to *mask and hide* the difference between Python 2.x's
str and unicodes and 3.x's bytes and str has little value: the
str/unicode/bytes marker are not hidden anymore and the "b'" bytes
marker will be visible again.

### Incompatible changes (lib)
 - Remove common.log (API break) (f7bdda65) (#96)
 - Send the formatted logs to Progress; don't format in Progress
(lib-level incompatible change) (8d34657d9) (#96)
 - Use clog instead of log (lib-level incompatible change) (b0367987)
(#96)

### Others:
 - Specialized Dockerfile to set up an environment with all the
interpreters supported by byexample, ready to run the tests.
 - Several fixes in the documentation (thanks @matt17r)
 - Several hacks were removed now that we support only one version of
Python.

## 8.2.0-a1 (bb864ce) - Sun Sep 22 22:55:49 2019 +0000


## 8.1.3 (258c11d) - Sat Aug 3 12:58:22 2019 +0000

### Changes from previous version:
### Fixes
 - The License is packaged with the code (#89)
 - Alternative impl for fcntl in Window envs (#90)
 - Warn if the experimental and hidden RegexCache is used

## 8.1.2 (ba48bf7) - Thu Jul 11 15:00:43 2019 +0000

### Changes from previous version:
### Enhancements
 - Enhance some messages to the user
 - Update the project url to point to github page and not the repo

## 8.1.1 (c7e2e08) - Mon Jun 24 02:05:11 2019 +0000

### Changes from previous version:
### Fixes
 - Disable edit/readline feature (autocompletion and others) for Bash
(shell module). (fixes #87)

## 8.1.0 (60ab38a) - Tue Mar 5 15:23:08 2019 +0000

### Changes from previous version:
### Fixes
 - Fixed typo of class name ``PexepctMixin``, replaced by ``PexpectMixin``
(57452bdc39). Backward compatibility layer implemented in 7eafbb3b.
 - Fixed undefined ``sh`` shell and set to ``bash`` (3c3f59ba8).
 - Default implementation for the ``__init__`` of ``Concern`` (de26777a7).

### Enhancements
 - Allow to change the shell with some predefined options: ``bash``, ``dash``,
``ksh`` (3c3f59ba8) with the new ``+shell`` option.
 - Add better logs for the initial phases of ``byexample``: modules load
and parsing options (b6b371c55, part of issue #66 ).
 - Experimental *Conditional Execution* (a module) to allow to skip
or not an example based on a condition (797052faeb). Introduces
the ``+if``, ``+on`` and ``+unless`` options.
 - Restricted the set of possible characters for a tag name to letters,
numbers, minus and dot symbols; the names must starts with a letter or a
dot (a5707d48). The ``:`` symbol is allowed too but reserved for future
uses. Related to issue #32 .
 - Auto hide the non-printable replacement in the enhanced diff
(ec24b30673), closes #58.
 - Warn about non-printable char replaced that could be confused
(add2a0bc2), closes #30.
 - Improved how the diff are shown (ec24b30673, add2a0bc2).
 - Allow call external diff program (c210b5b59). Enable this with
``--diff tool`` and set the diff command line with ``--difftool <cmd>``.
Closes #20.

### Documentation:
 - More notes about checks (5bd91a047).
 - FAQs (8028bb4b, a5707d48)

### Potential incompatible changes (examples)
 - In Debian/Ubuntu based distros, ``sh`` is a symlink to ``dash``. In
``byexample 8.1.0``, ``sh`` is replaced by ``bash`` which it could break
some examples. See the comments in 3c3f59ba8 for a full explanation.
In any case the incompatible changes should be easy to fix and if not,
the user can force to rollback to ``dash`` with the option ``+shell=dash``.
For Red Hat/Fedora based distros, ``sh`` is a symlink to ``bash`` so
it should be ok.

## 8.0.1 (33845bb) - Tue Feb 19 13:24:28 2019 +0000

### Changes from previous version:
### Fixes
 - Printing a utf-8 example when byexample's output is redirected to a
file fails in Python 2.7 (fixes #80)

## 8.0.0-a1 (0e8eb7d) - Mon Dec 17 14:47:18 2018 +0000


## 8.0.0 (16a89a4) - Sun Feb 17 00:03:27 2019 +0000

### Changes from previous version:
### Fixes
 - ``cling`` errors including ASCII escape sequences are interpreted
correctly (210ee637)
 - Enhance the diff mapping ctrl unicodes to ``'?'`` and only mapping
ctrl unicodes (e396b241)
 - Update Python's pretty print (``pp``) on a geometry change ``SIGWINCH``
(90e18b70)
 - Pass options to ``Concern.start`` hook (91fb6b39)
 - Avoid race condition in read/write cache from/to disk (73c1b01ef)
 - Ignore non-ascii chars in Python 2.7 with ``+term=ansi ``(fa506e594)
 - Fixed pathological regexs and incompatible ones with the Linear
Expected optimization (0f7282ff, ebba12a71)
 - Warn if no files were passed/found instead of crashing (637162df1)
 - Fix option parsing and defaults (e4c07ff7, 38b9946e8)
 - Do not cache some internal objects (25ec8af02)
 - Do not allow for abbreviations of long options (fae5ca8780)
 - Perform a read even if timeout is 0 (``_expect_prompt``), fix
the message of the timeout (eb2107e08e)
 - Best effort for shutdown the runners (3bc281d2a)
 - Count example once, even if ``finish_parse`` is called twice (a9322b562)

### Enhancements
 - Capture greedy/non-greedy (heuristic): named tags are non-greedy as they
are used to capture interesting, typically short strings; unnamed tags are
non-greedy too except at the end of a line where typically capture
longer uninteresting outputs. (c94def08, fb889619f, 6d5178c84)
 - Better support for cling (the C/C++ interpreter) using ``pyte`` (a
terminal emulator). (210ee637)
 - Full support for unicode inputs (running byexample with Python 2.x
and 3.x) (6cb12dd5, 4b32b572, cd9b96ea, 10421dc8, 79064664).
 - Document the ``--encoding`` option (10421dc8).
 - Send a ``SIGWINCH`` on ``+geometry`` change (90e18b70)
 - Support for terminal emulations: ``+term=as-is`` (no emulation), ``+term=dumb``
(removes any trailing whitespace, converts to spaces the tabs and uniforms
the new lines) and ``+term=ansi`` (full terminal emulation, useful for ``ncurses`` based
outputs). (9ca21baa, 2605f5d2)
 - Improve to the cache system (still experimental) (99ff4d1bf,
f36b085d6, 19978f752)
 - Reimplemented part of the expected parsing: the ``expected_tokenizer``
(052cb456e)
 - Reimplemented the parser for the expected as a state machine
(73ba50fe3, e07b7878, 912290a4, 02dc851f7, 6aebd27b8, 78096ea65,
6b6ee55c87, bc9bbf908, 1998b6930, 233afd37, 641c88d39)
 - The target/language of Finders/Parsers can be a collection
(851b14f62)
 - Simplify the check overlap (76cc8a897, e7e457b608)
 - The original (7.x) ``+stop-on-silence`` stops the process only on
timeout; it was renamed to ``+stop-on-timeout`` and the
``+stop-on-silence`` was fixed to do what it's supposed to do: stop
after some period of inactivity or silence. (8b46779374, ba7a0c2dc94)
 - Default timeout for internal ops ``-x-dfl-timeout``. (65c6c946ca,
a058d0f5f)
 - Renamed ``+delaybeforesend`` to ``-x-delaybeforesend`` (b3b3009511)
 - ``-x-min-rcount`` to control the sensitivity of the incremental match
(fe57cafd3)
 - ``--shebang`` renamed to ``-x-shebang`` (86664f6e5)
 - Concern ``event`` generic event type; Process uses event for logging.
(d20c14097, 89a46248f)
 - Deterministic output (``pp``) for Ruby Hashes. (9139d3ee0a)
 - Ruby support: 2.0, 2.1, 2.2, 2.3, 2.4, 2.5 and 2.6; RVM environments
too (4d9fc174f).
 - Recover the runner after a timeout and do not abort. (47557f7060)
 - Support for cancel an ongoing example. (802d88a49)

### Potential incompatible changes (examples)
 - The unnamed tag's regex is greedy; named tags are not (c94def08)
 - The C/C++ now require the use of a full terminal emulator
(``+terminal=ansi``) always and its geometry cannot change. (210ee637,
e6b2fa76)
 - Changed the default terminal emulation from ``+term=as-is`` to ``+term=dumb``
which it is more useful and reduce the need of ``+norm-ws`` (2605f5d2).
 - The hacky ``# >>`` Ruby prompt is not supported, superseded by Zone
Delimiter for Ruby files (.rb) (a5b5dcd0f)

### Incompatible changes (examples)
 - Limit the number of output rows for C/C++ examples (bedef7ef)
 - Do not allow an underscore in a tag name (38766d83d)
 - Capture greedy/non-greedy (heuristic): named tags are non-greedy as they
are used to capture interesting, typically short strings; unnamed tags are
non-greedy too except at the end of a line (c94def08, fb889619f, 6d5178c84)
 - Zone Delimiter: defined find zones where to find examples -- ``byexample``
will not find examples anywhere anymore (b2adc9362, fadc894da). Examples
can be found only in code blocks and comments of a Markdown file; in the
docstrings of a Python file; in the comments of a Ruby file ... (see
each language) (46ef5d955, c0d6e05cf, f064ac7f8). Only prompt based examples
are supported. (bb86873fa, 08051927)
 - Use ``?:`` and ``::`` as primary and secondary prompts for C/C++ examples
(582f33c226)
 - Rename ``stop-on-silence`` by ``stop-on-timeout`` (8b46779374)
 - Implement ``stop-on-silence`` for shell (incompatible with 7.x)
(ba7a0c2dc94)
 - To set options in the C/C++ examples, use ``// byexample: ...`` only
(``/* .. */`` is not supported anymore) (21060dac0)

### Incompatible changes (lib)
 - Refactor ``_spawn_interpreter`` (3670321c3)
 - Refactor ``PexepctMixin``/``ExampleRunner`` passing options explicitly
(``_exec_and_wait``, ``_expect_prompt``, ``_change_terminal_geometry_ctx``,
``_change_terminal_geometry``, ``run`` and ``_get_output``) (2cfe8b60)
 - Refactor and removed unused code in ``Expected`` (193a5a99f, 426e4801d)
 - Explicit timeout value for ``_expect_prompt`` (28be774c5)

### Incompatible changes (modules)
 - Each runner needs to implement its ``ExampleRunner.run`` in terms of
``PexepctMixin._run``; ``PexepctMixin._run`` will delegate the runner-specific
code calling ``PexepctMixin._run_impl`` (to be overridden by the runner)
(bea45a20f)
 - Pass options to ``Concern.start`` hook (91fb6b39)
 - Removed the concept of spurious endings and specific/generic finders
(2ddfd1d876)
 - Extend ``user_aborted`` to a more generic aborted hook; ``user_aborted`` is
not supported anymore. (4356a9a4a)

### Others
 - New dependency: ``pyte`` version 0.8.0.
 - Makefile: Allow run the tests using multiple processors (e379c427)
 - Documentation refactor (87fcdca3, eca2d804, 4b700163, 374dc0926,
bc5921392, 6f75b4fae, f67e1dcb, d6676dd80, e0a17c8d32, 653b5b30)
 - Removed ``--interact``/``--debug`` option (e346c155a)
 - Make provisional the Ruby and the Clipboard modules. (5345ec3e0e)

## 7.4.5 (8940e10) - Wed Dec 5 03:40:34 2018 +0000

### Changes from previous version:
### Fixes:
 - Disable readline for irb (ruby interpreter). Fixes #70.

## 7.4.4 (0bf93de) - Sun Nov 11 23:53:11 2018 +0000

### Changes from previous version:
### Enhancements:
 - Use 'provisional' as alias for 'unstable'.

## 7.4.3 (eb38a9e) - Fri Oct 26 12:01:50 2018 +0000

### Changes from previous version:
### Fixes:
 - Changed how the Ruby runner toggles the echo mode of IRB
(+ruby-expr-print) due a change in Ruby 2.5 (see 539d3a19). Closes #62
 - Added a missing module (sys) and fixed a typo in one attr name (see
d44d9b07)

## 7.4.2 (0a424e4) - Tue Oct 23 02:14:20 2018 +0000

### Changes from previous version:
### Enhancements:
 - Print a warning if a Parser/Finder/Runner/Concern is loaded but it
has its key attibute (target, language, concerns) missing.
 - Print the Python version used to run byexample.

## 7.4.1 (070b3ec) - Fri Oct 19 12:35:30 2018 +0000

### Changes from previous version:
### Enhancements:
 - Extended the KeyboardInterrupt capture scope (see 0e8e09ef6a)
 - Prevent sigints in critical paths (see 6dfbba75). Closes #54
 - Minor improvements to the progress report (see a43a0f37)

### Fixes:
 - A KeyboardInterrupt (aka ^C) abort the whole execution in
the most possible ordered way without printing a traceback (see
c56f79d4, 6dfbba7 and 0a33405c)

Note:
 - Despite of be implemented #54, byexample is *not* race-condition free
when an asynchronous SIGINT signal is received (aka KeyboardInterrupt or
^C). It was done in #54 a best effort to minimize the damage and the
resources leaked or blocked.

## 7.4.0 (ca856e8) - Mon Oct 15 00:26:22 2018 +0000

### Changes from previous version:
### Enhancements:
 - Support report progress in parallel (see 48ef2c16).
 - Support run concurrently (see d6d2e42b). Closes #45.
 - Experimental support for Javascript-nodejs (see 9febf82). Closes #55.

### Fixes:
 - Fix "leak" of options' up (see a04fe83c)

Possible incompatible changes (usability minor level)
 - Do not fake tqdm; disable ProgressBarReporter if tqdm is not
installed.

## 7.3.0 (cece44f) - Fri Oct 12 19:05:57 2018 +0000

### Changes from previous version:
### Enhancements:
 - Regex cache (experimental) (see a73eb2fa, 501da7c, 260dee67, 59ca1008)
disabled by default.
 - First line with a lowe indentation level cuts the example (fa4a10f6).
 - Remove spurious endings (see 55e4df79, 833d69c5). Closes #47
 - Improved timeout message (see fd4d6f). Closes #27
 - Change terminal's geometry from cmdline (see 90ac4fc, 8dc9460). Closes #34

### Fixes:
 - A timeout is now considered an ABORT (see ab9c860d). Closes #44.

Possible incompatible changes (modules)
  - Concern.finish will receive another parameter: timedout.
  - Python 3.3 support is gone.

### Others:
 - New dependency: appdirs
 - Internal helper script r.py updated.
 - Updated the docs.

## 7.2.3 (08107f8) - Thu Oct 4 15:17:07 2018 +0000

### Changes from previous version:
### Enhancements:
 - Small optimizations (see bd8a740a, 92d8982)
 - Improved error message when two examples overlap (see 5e08f80)
 - Other minor optimization.
### Fixes:
 - Made Markdown examples compatible with others (see 38793dc)
 - Count new lines correctly avoiding hacks (see 2a67300f)
 - Timeout (--timeout) accepts float now (see bfdd8e1)
 - Made optional the capture at the end (see 528a7c85, fixes #51 )

### Others:
 - Removed huff (see dbe0497)

## 7.2.2 (116e197) - Mon Sep 3 14:24:21 2018 +0000

### Changes from previous version:
### Enhancements:
 - Cached the extension of the options parser (see bf8abfd9)
 - Cached the already parsed options (see 4ee34e96)
 - Other minor optimization.

Note: the runtime should be reduced by a ~33% with these optimizations.

## 7.2.1 (78778f8) - Sat Sep 1 22:58:31 2018 +0000

### Changes from previous version:
### Enhancements:
 - Removed obsolete code.
 - Improved the documentation.

## 7.2.0 (ced5262) - Sat Sep 1 22:13:03 2018 +0000

### Changes from previous version:
### Enhancements:
 - Find prompt-based examples of Ruby even if they are prefixed by #
   This *may* detect new examples but it should be unlikely and with
   low impact. (The Ruby module is still experimental)
 - Enable +fail-fast inside in an example #42 As side effect, the
   examples will be skipped (marked as SKIP). See c17f433
 - Enable -skip inside in an example to executing even if the execution
   is failing fast #43 See c17f433
 - Improved the documentation.
### Fixes:
 - Don't let gdb to ask for confirmation.

## 7.1.2 (64dfa5e) - Thu Aug 23 16:30:53 2018 +0000

### Changes from previous version:
### Fix:
 - Fixed the README in PyPI and improve it a little.

## 7.1.1 (bad260a) - Tue Aug 21 02:14:05 2018 +0000

### Changes from previous version:
### Fix:
 - Fixed the setup.py that was requiring Python >= 2.6 for running
byexample. The support for Python 2.6 was dropped in 6.0.0. However,
almost everything in byexample can run under 2.6 (except shebang
feature).

## 7.1.0 (8319e72) - Sat Aug 18 23:28:25 2018 +0000

### Changes from previous version:
### Enhancements
 - Implemented the stop-on-silence option for Shell: instead of raising a
timeout, if an example takes too long the runner will stop the long-running
process. It is undefined if there isn't a process running and the
example times out. See docs/languages/shell for a complete overview and
possible usage of this.

## 7.0.3 (0cbf5f3) - Fri Aug 10 00:56:15 2018 +0000

### Changes from previous version:
### Enhancements
 - Disable output with colors if the terminal doesn't support them.

## 7.0.2 (0ec11ff) - Thu Aug 2 14:01:33 2018 +0000

### Changes from previous version:
### Enhancements
 - Allow to load command line options from a file using '@file' syntax.

## 7.0.1 (d7ae00e) - Wed Aug 1 15:34:11 2018 +0000

### Changes from previous version:
### Fixes
 - The tag names that contains a minus - like <foo-bar> will work in
paste mode (+paste).

## 7.0.0 (0a861f3) - Sun Jul 29 22:33:13 2018 +0000

### Changes from previous version:
### Fixes
 - Save in Example its own local options and not its options merged with
the global one. It will be during the execution of the example that its
options will be merged.
 - Expected's get_captures can be called without calling
check_got_output before.
 - Fixed the interact functionality for Python 3.x
 - Print the error (if any) after the interact session.
 - Make sure that expected_str is a string even if the example has no
expected output (in which case expected_str will be the empty string).
 - Fixed the heuristics to avoid collisions: pick the specific finder
over the generic one even if they are of different languages.
 - Fix print traceback for Python 2.x

### Enhancements
 - Allow a Ruby => following by the end of the string: this trigger the
auto print expressions without needing a value after the =>.
 - The Concerns can add their own options and flags like the Parsers.
 - Made Example modifiable a full class instead of a namedtuple.
 - Improve the errors printing the source code of the example where the
error happen (if available).
 - Extended the Concern interface adding hooks to the parsing phase of
an example: start_build, before_build_regex and finish_build.
 - Delayed the parsing phase just before executing the example: this
allow the modification of an example before parsing (like its expected).
 - Better error printing if the parsing of an example fails.
 - Clipboard module to support 'paste' of previously captured texts. See
720916aa. Use +paste option to enable it.
 - Better prints (logs). See 45e3188e.

### Incompatible changes (examples)
 - Removed +shell option from Shell runner

### Incompatible changes (lib)
 - No more ExampleMatch, Example will do its job. See f949d64b.
Initially the Example is created by the Finder in an "incomplete, not
parsed yet" state. Later, the Example is parsed calling
Example.parse_yourself which calls Parser.parse.
 - Parser.build_example renamed to Parse.parse (and simplified its
interface).

### Incompatible changes (modules)
 - The option parser optparser is not passed explicitly, you can still
get it from options['optparser'].
 - Runner.initialize will not be called with the examples.
 - Concern.start_run will be called with a *not parsed* examples: some
of theirs attributes will be missing.
 - Renamed some Concern's hooks: start_run to start, end_run to finish,
end_example to finish_example
 - Removed Example's meta; Example is writable so there is no need to
have an extra attribute.

## 6.0.1 (c7927f1) - Fri Jul 20 02:27:48 2018 +0000

### Changes from previous version:
### Fixes
    - Added support for the heredoc syntax used by the Ruby interpreter
``irb``.

## 6.0.0 (b13e349) - Wed Jul 11 15:16:22 2018 +0000

### Changes from previous version:
### Fixes
 - Made deterministic the output of the captured texts shown when the
example fails.
 - Parse the examples *after* removing duplicated/overlapping ones. This
prevents that a malformed example that would be removed later gets
parsed *before* making the whole process to fail.
 - Remove the word ``TIMEOUT`` from the help, this was the name of the
option a long time ago.
 - Fix the traceback printed when the example crashes.
 - Fix ExampleHarvest's name.

### Enhancements
 - Added a ``rm`` option to define a set of chars that should be removed
from the expected and the got strings. See 6050a884 for a small example.
 - Detect when a ``Ruby`` example expects the representation of
the value of the executed expression (``=>``). If detected, capture the
representation and check it as usual; if not, ignore it. This free the
user from adding ; at the end of each line or using "+pass" hacks. This
change in theory *should* be backward compatible and can be changed via
``+ruby-expr-print`` by setting it to ``true`` (always check), ``false``
never check or ``auto`` (auto detect, the default).
 - Two hooks (end_example, finally_example); allow got modification from
concern.
 - Created a 'meta' attribute in the example, a mutable dictionary.
Under the key 'got' it should be the got string that can be changed from
the ``end_example`` and ``finally_example`` hooks.
 - Enable the redefinition of the command line to spawn a given
runner/interpreter using the option ``shebang``. This was enabled by all
the runner/interpreted supported by ``byexample``. See 6e3abae0 or
``docs/usage.md``.
 - The ``timeout`` option now accepts a fraction of seconds.
 - Tagged each module with a stability tag: fine tuned the versioning.
See 5f3d0494 and ``README.md``.

### Incompatible changes (examples)
 - Enable by default pp (pretty print) for ruby exprs' outputs. This can
be disabled from the command line with the option ``ruby-pretty-print``
 - Use ``..`` as the second prompt for the ``Ruby`` examples. This make
the life easier when the examples are multilines. See 9784f38 for more
details.

### Incompatible changes (lib)
 - The ``shebang`` option required a non backward compatibility change
of the internal class ``PexepctMixin``.
 - The ``shebang`` option also is "not" compatible with ``Python 2.6``.
 - We are dropping the support for ``Python 2.6`` (for the execution of
``byexample`` itself, not the runner/interpreter of examples in
``Python``)

## 5.0.0 (ffb8dc9) - Sat Jun 23 23:00:55 2018 +0000

### Changes from previous version:

### Fixes
 - Prevented long running checks (#28) using a linear matching
algorithm.
 - When an example fails, byexample will try to fill the tags in the
expected with the got's pieces. Put a limit (timeout) when computing
this to prevent long running. See #29. Set this to 2 secs.
 - Fixed a pathological regex of the form \s+ <tag> \s+. Because the tag
can match nothing (the empty string), the resulting regex was \s+\s+
which leaded to a lot of backtracking.
 - Fixed Differ's print of the captured strings (removed trailing
whitespace)
 - Fixed an integer division on Python 3, in the Differ code.

### Enhancements
 - New doc about how byexample show the differences in a failing example:
docs/differences.rst
 - Implemented a linear matching algorithm (#28) to see if a expected string
matches or not the got one in an example. This should not be faster
but also it should be safer (see #23) without doing more hacks (see #25)
 - Improve exception handling: print the exception class and print a
hint for the user: run the example in verbose mode to get the full
traceback.
 - When an example fails, byexample will try to fill the tags in the
expected with the got's pieces. The algorithm now performs a more
aggressive strategy to make more clear expected strings and therefore
more clear diffs.

### Incompatible changes (examples)
 - Repeating a named capture tag (<foo>) in the same example is not
allowed anymore. Previously this meant that the captured string under
the same tag must be the same string. But this prevented further
improvements and it was a feature implemented without a real reason of
the benefits.
 - Replaced 'capture' option by 'tags'

### Incompatible changes (command line)
 - Replaced 'capture' option by 'tags'

### Incompatible changes (lib)
 - Refactor the Checker and replaced by Differ (who do the diffs) and
the Expected's subclasses (who do the comparison): LinearExpected and
RegexExpected.
 - The namedtuple Expected was replaced by a full class Expected.
 - The interface of Expected and Differ changed.
 - Renamed module checker.py by differ.py and created a new one:
expected.py

### Incompatible changes (modules)
 - Because the Checker interface changed (now is Differ) and the
Expected changed too, this may affect the third party modules (3rd party
interpreters and concerns)

## 4.2.1 (c162021) - Mon Apr 30 02:47:54 2018 +0000

### Changes from previous version:

### Fixes:
 - Fixed an incorrect comparision in the diff algorithm.

### Enhancements:
 - Implemented huff: a more human readable diff program.

## 4.2.0 (ff15714) - Wed Feb 28 01:36:13 2018 +0000

### Changes from previous version:

### Enhancements
 - Do not print the traceback by default to avoid printing internal
   stuff for common mistakes. But print it if verbose is greather than
   0.
 - Suppress any error's message in quiet mode.
 - Improved all the errors' messages trying to use more descriptive
   messages. Extend them adding in which file and number line (if
   possible) the error is located and who was the responsible of it.

### Incompatible changes (lib)
 - Remove the 'where' attribute/parameter from almost everywhere
   This affects some very public methods:
    * ExampleParser: process_snippet_and_expected, extract_options

   And others not so public:
    * ExampleFinder: check_keep_matching
    * ExampleParser: expected_as_regexs

## 4.1.0 (f072c8d) - Mon Feb 26 15:25:16 2018 +0000

### Changes from previous version:
### Fixes
 - Reimplemented (and fixed) the universal newlines: now the sequence
   \r\n and \r are replaced by \n correctly.
 - Removed a hardcoded delay when sending something to the underlying
   interpreter. Before was a delay of 0.01 secs, now it is disabled.
   See eb37d358.

### Enhancements
 - Cached the compilation of the regexs avoiding calling re.compile
   more than once for a regex.
   The improvement is small as re.compile already has a cache for this
   but it is better to cache ourselves in case we want to change the
   regex engine (Python's re module for now)
 - Refactor of internal ExampleParser's methods allowing to change the
   meaning of things like 'whitespace' or 'ellipsis'.
 - Do not delay the sending of input to the interpreter; make it as
   faster as possible. Before was a delay of 0.01 secs, now it is
   disabled. See eb37d358.
   If needed, the flag 'delaybeforesend' can control this delay (none by
   default) from the command line (-o option) or from the example's
   options string.

## 4.0.1 (54c279c) - Sat Feb 17 23:41:08 2018 +0000

Changes:
 - Instead of patching an internal function of pprint for the custom
   display hook of the Python interpreter, patch the repr function.
   This should be a backward compatibility fix.
 - Improve the docs.

## 4.0.0 (97df502) - Thu Feb 15 01:04:16 2018 +0000

### Changes from previous version:

### Fixes
 - The empty lines at the end of the expected and got strings are
   really ignored, not only the last one. This was the original
   intention as most of the time an empty line at the end is an artifact
   of the parser/finder (for the expected string) and is an artifact of
   the interpreter (for the got string).
   If you really need to match an empty line at the end, use a capture
   tag.
 - The WS flag (whitespace) was triggering the replacement of all the
   whitespaces by a single space *and* the replacement by a \s+ regex.
   This double work ended up in a buggy behavior under some condition.
   Now the \s+ implementation is used and nothing else to support WS.
 - Fixed the the u/b Python's markers: by mistake, the strings b' were
   replaced by ' in every case. Now, we replace this only if b' is a
   real string marker. The same for u'

### Enhancements
 - Before calculating the diff, the captured tags in the expected string
   are replaced by the captured string from the got string.
   This improves the posterior diff.
   However, it is not possible to replace all the capture tags: only the
   tags before the first difference and the tags after the last difference
   can be 'safely' replaced.
   This enhancement can be disabled with --no-enhance-diff
 - Thanks to the expected_as_regexs modification, the regexs are line
   oriented which should improve the diff.
   This enhancement can be disabled with --no-enhance-diff
 - Improved the error message when an examples is misaligned showing a
   few lines above and below to give more context.
 - Print the named captured tags and their captured strings after
   showing the diff in a failed example. This should give the user a
   hint of what and how much is begin captured and by what tag.
   This enhancement can be disabled with --no-enhance-diff
 - Made the check of overlapping examples more relaxed:
    * If one example is fully contained by the other, then it's dropped.
    * If one example span the same lines that the other and both are of
      the same language, then it's dropped.
    * In other case of overlapping, raise an exception.
 - Use ^n instead of <blankline> to mark where the empty lines are. This
   is more consistent with the rest of the diff hints.
   This enhancement can be disabled with --no-enhance-diff
 - Implemented the '+py-doctest' option for Python to be (almost) full
   compatible with Python's doctest.
 - Implemented the '+py-pretty-print' option for Python to tweak the
   string representations (u/b markers) and the use of pprint as display
   hook. Enabled by default (like always), it is disabled when the user
   sets '+py-doctest' (compatibility with doctest) but it can be
   reenabled with '+py-pretty-print'.
 - New flag: --show-options. List the available options that byexample
   and the given selected languages support and can be set on an
   example.
 - Improved how the examples are printed in debug/verbose mode.
 - Allow empty lines in an example to be non-indented. See e937a0c9
 - Show the version, license, author and github url in the output of
   --version/-V

### Incompatible changes (lib)
 - expected_as_regexs now returns a list of regular expressions
   instead of a single regex. In addition, the position from where
   each regex was created in the expected string is recorded.
 - The Example class changed accordingly.
 - Refactor all the stuff related to the expected string of an Example
   into a separated structure Expected (an attribute of Example).
 - Moved the Checker class to its own module checker.py
 - Splinted byexample.py into cmdline.py (parse the command line
   arguments) and init.py (to initialize all the main objects)
 - Refactorized the Finder class
 - Moved several functionalities from Parser to Finder. See 2c84deec.
 - Several renames. See 62669bef and a2ba4b8:
    * First, rename the director classes and objects:
       - ExampleFinder -> ExampleHarvest
       - ExampleRunner -> FileExecutor
       - ExampleFinder instance (finder) -> harvester instance.
       - ExampleRunner instance (runner) -> executor instance.
       - executor's run method -> execute method.
    * Second, rename finders and interpreters (disruptive changes)
       - MatchFinder -> ExampleFinder
       - Interpreter -> ExampleRunner
       - Interpreter instances (interpreters) -> runners
       - initialize_interpreters method -> initialize_runners method.
       - shutdown_interpreters method -> shutdown_runners method.
       - example's interpreter attribute -> runner attribute.
    * Renamed the following files:
       - byexample.runner -> byexample.executor
       - byexample.interpreter -> byexample.runner

### Incompatible changed (modules)
 - the classes that extend Parser needs to use a OptionParser (based on
   Python's argparse) to parse the options of an example.
   This is a disruptive change but it simplify the code (see b81f2106)
   but it allows us to change some byexample's options from the example
   directly reusing the same parser and the same way to set the options.
   For example, an given example can say '+diff context' to set a
   particular diff algorithm for that example.
 - The keywords UDIFF, NDIFF and CDIFF are gone. Instead we use '+diff' with an
   argument with the same possible values like in the command line.
 - Reimplemented how we parse the '-o' strings (extra options from the
   command line). Now we use the same parser that we use for an
   example's options. See 59ed7a2e.
 - All the options of byexample are now lowercase. This was the original
   intent: all the options of byexample should be like "+capture" instead of
   "+CAPTURE". (the uppercase version was to be compatible with Python's
   doctests)
 - Renamed 'WS' to 'norm-ws'.
 - Refactorized the interfaces adding better hooks to extend by
   subclasses and renaming with better names and concerns. See
   doc/how_to_extend.rst for a more complete overview of these new
   interfaces.
 - Replaced the +bash/+sh flags by +shell=xxx in the Shell module.
 - For Python, remove empty lines that may trick the interpreter into
   believe that a indented-block was closed when it is not. See f5a86f59.
   This fix can be disabled with -py-remove-empty-lines

### Documentation:
 - improved the docs in general.

## 3.0.0 (e57a0ef) - Tue Jan 9 12:18:59 2018 +0000

### Changes from previous version:

### Fixes
 - Fixed a bug in shell.py: remove the space after the prompt.

### Enhancements
 - New language: GDB (GNU Debugger)
 - New language: C++
 - Find the examples written inside a fenced-code-block (Markdown style)
 - Reimplemented the blacklist/whitelist of languages: -l flag and support
two syntaxes -l A -l B and -l A,B.
 - Experimental interactive mode: take the control of an interpreter for
debugging.
 - Concern interface: extend byexample adding hooks to different stages.
See doc/how_to_extend.rst and byexample/modules/progress.py.
 - Use env to spawn the interpreters
 - Changed --no-enhance-diff and --ff (fail fast) command line flags.
 - Added a per example timeout (TIMEOUT option and --timeout flag)
 - Highlight the examples when they are printted (requires pygments)
 - Better progress bar (requires tqdm).
 - Three possible status: PASS, FAIL and ABORT.
 - In the summary, take into account the Skipped when calculating the total
count.
 - In the summary, do not print the aborted count; instead print the
skipped examples count.
 - Changed the exec_and_wait: send one source line and expect one prompt
at time. See commit #8e86d7f48 for the details, pros and contras.
 - Added a --version flag

### Incompatible changes (command line)
 - Replaced --no-color by --pretty.
 - Removed -f (you can still use --ff and --fail-fast)
 - Renamed --search by --modules (you can also use -m)

### Incompatible changes (interpreters)
 - Removed support for prompt # in Shell examples: the # symbol is too
common and it is easy for byexample to get confuse

### Incompatible changes (lib)
 - Refactor -> we have three components:
    * Finder: who will find the examples in a given string
    * Parser: who will parse the findings and transform them into Examples
    * Interpreter: who will execute the given Examples.
See docs/how_to_extend.rst

## 2.1.1 (6d6ffb9) - Tue Nov 28 17:12:37 2017 +0000

### Changes from previous version:

### Fixes
 - Python 2.6 incompatibilities
 - Python 3.x incompatibilities
 - Fixed a +/-1 line number

### Enhancements
 - Example timeout doesn't produce an exception anymore. Instead, log
the error and fail the execution (like fail-fast)
 - Improved the documentation.
 - Command line flag to disable the colors in the output.
 - Added the possibility to set a value to an option, not only
True/False like +FOO=VAL
 - Added a TIMEOUT option to change the timeout of a given example.

### Incompatible changes
 - Ruby example will use >> as the primary and secondary prompt. The rb>
and ... were removed. This is closer to the irb interpreter behaviour as
well as how others show or write Ruby examples (in tutorials).

