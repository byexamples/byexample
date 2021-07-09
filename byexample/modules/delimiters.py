from __future__ import unicode_literals
import ast, itertools
import byexample.regex as re
from byexample.finder import ZoneDelimiter
from byexample.common import constant
from byexample.log import clog

stability = 'provisional'
'''
>>> from byexample.modules.delimiters import DocStringDelimiter
>>> from byexample.log import init_log_system
>>> init_log_system()
'''


class NoDelimiter(ZoneDelimiter):
    target = 'no-delimiter'

    @constant
    def zone_regex(self):
        return re.compile(r'\A(?P<zone>.*)\Z', re.DOTALL | re.MULTILINE)

    def __repr__(self):
        return "No Zone Delimiter"


class CppBlockCommentDelimiter(ZoneDelimiter):
    target = {'.cpp', '.c', '.h', '.hpp', '.js', '.php', '.go', '.java'}

    @constant
    def zone_regex(self):
        return re.compile(
            r'''
            # Begin with a /* marker
            ^[ ]*
             /\*

             # then, grab everything
             (?P<zone>.*?)

             # and the close marker
             \*/
            ''', re.DOTALL | re.MULTILINE | re.VERBOSE
        )

    @constant
    def leading_asterisk(self):
        return re.compile(r'^[ \*]+(?=[^ \*]|$)', re.MULTILINE)

    def get_zone(self, match, where):
        zone = ZoneDelimiter.get_zone(self, match, where)
        return self.leading_asterisk().sub(' ', zone)

    def __repr__(self):
        return "/* ... */"


class HashCommentDelimiter(ZoneDelimiter):
    target = {'.rb', '.sh', '.ps1'}

    @constant
    def zone_regex(self):
        return re.compile(
            r'''
            # Begin with a # marker
            ^[ ]*
             \#

             # then, grab everything that begins with a #
             # until we cannot do it anymore
             (?P<zone>  .*$\n?                  # first line
                        (?:[ ]* \# .*$\n?)*     # the rest of the lines
                    )
            ''', re.MULTILINE | re.VERBOSE
        )

    @constant
    def leading_sharp(self):
        return re.compile(r'^[ ]*#', re.MULTILINE)

    def get_zone(self, match, where):
        zone = ZoneDelimiter.get_zone(self, match, where)
        return self.leading_sharp().sub(' ', zone)

    def __repr__(self):
        return "# ..."


class DocStringDelimiter(ZoneDelimiter):
    target = {'.py'}

    def zone_regex(self):
        raise NotImplementedError("Use get_matches directly")

    def __repr__(self):
        return "''' ... ''' or \"\"\" ... \"\"\""

    def get_matches(self, string, filepath='<string>'):
        mstring_re, dstring_re = self.module_string_and_docstring_regexs()

        # Use 'search' and not 'match' because the starting point 'offset'
        # is close but not the precise location of the docstring.
        # Also, do not use 'finditer' because we want to match the first
        # string that looks like a docstring (we don't want to scan further)
        #
        # On error, rollback to a more naive search (which may lead to false
        # positives)
        offsets = self.near_offsets_of_docstrings(string, filepath)
        if offsets is None:
            # we got an error, rollback to the naive search
            it1 = dstring_re.finditer(string)
        else:
            it1 = (dstring_re.search(string, offset) for offset in offsets)

        # Strings at the 'module' level
        it2 = mstring_re.finditer(string)

        # Combine the matches
        matches_iter = itertools.chain(it1, it2)

        # Sort the matches by match's start position
        return sorted(matches_iter, key=lambda m: m.start())

    def get_offset_by_lineno(self, source):
        '''
            Return a list that map a line number (starting from 1) to
            the character number (starting from 0).

            Because there is no line '0', the first element of the list
            will be None (for padding)

            >>> source = 'hello\nworld\n\n!!'
            >>> offsets = DocStringDelimiter(0,0).get_offset_by_lineno(source)
            >>> offsets
            [None, 0, 6, 12, 13]

            >>> offsets[2]  # offset of the 2nd line 'world'
            6

            >>> source[offsets[2]:offsets[2]+5] # get part of the line
            'world'
            '''
        offset = 0
        offsets = [None]  # lineno==0 has none offset
        for lineno, line in enumerate(source.splitlines(), 1):
            offsets.append(offset)
            offset += len(line) + 1  # plus the new line char

        return offsets

    @constant
    def module_string_and_docstring_regexs(self):
        # match a triple single or triple quote Python string
        tmp = r'''
         # Begin with a triple single or triple quote
         [bBuU]?[rR]?(?P<marker>(?:\'\'\') | (?:"""))

         # then, grab everything until the first end marker
         (?P<zone>.*?)

         # finally, the end marker
         [^\\](?P=marker) # then we must match the same kind of quotes
        '''

        re_flags = re.DOTALL | re.MULTILINE | re.VERBOSE

        # Match a string at the begin of a line. These are the
        # only strings that can exist at the 'module' level of
        # a Python source code.
        # This regex will capture also the docstring of the 'module'
        # if such exists
        module_string_regex = re.compile(r'^ ' + tmp, re_flags)

        # Match an indented string. These will match any string
        # but if the starting point for a search is at the begin
        # of a class or function definition, this will match
        # the docstring of it (using re.match and not re.search)
        docstring_regex = re.compile(r'^[ ]+ ' + tmp, re_flags)

        return module_string_regex, docstring_regex

    def near_offsets_of_docstrings(self, source, filepath='<string>'):
        '''
            Return the character number of each docstring except
            for the docstring of the 'module' of Python.

            The offsets returned are an approximation: it is a
            number less or equal to the correct offset.

            >>> source = '"""module docstring"""\ndef f():\n  """func docstring"""\n  pass'
            >>> offsets = DocStringDelimiter(0,0).near_offsets_of_docstrings(source)
            >>> offsets
            [32]

            >>> source[offsets[0]:offsets[0]+14]  # "less than"
            '  """func docs'

            If an invalid source is given, the code will fail
            and it will return None and a warning will be written

            >>> source = 'invalid syntax'
            >>> filepath = 'foo.py'
            >>> offsets = DocStringDelimiter(0,0).near_offsets_of_docstrings(source, filepath)  # byexample: +norm-ws
            [w] A syntax error was found parsing "foo.py": we may not found all the examples in the docstrings correctly.
            [w] <...>File "foo.py", line 1
                invalid syntax
            <...>       ^
            SyntaxError: invalid syntax
            >>> offsets is None
            True
        '''
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            clog().warn(
                'A syntax error was found parsing "%s": we may not found all the examples in the docstrings correctly.',
                filepath
            )

            import traceback
            e.filename = filepath  # NOTE: this trick may or may not work
            msg = traceback.format_exc(limit=0)
            clog().warn(msg)
            return None

        offsets = self.get_offset_by_lineno(source)

        near_offsets = []
        for node in ast.walk(tree):
            try:
                docstring = ast.get_docstring(node)
            except:
                continue

            if docstring is None:
                continue

            if isinstance(node, ast.Module):
                continue

            start_lineno = node.lineno  # line number of a func/class
            assert start_lineno is not None

            start_lineno += 1  # the next line, it closer to the docstring
            near_offsets.append(offsets[start_lineno])

        return near_offsets


class MarkdownFencedCodeDelimiter(ZoneDelimiter):
    target = {'.md'}

    @constant
    def zone_regex(self):
        return re.compile(
            r'''
            # Begin with a markdown fenced-code marker or a html comment marker
            ^[ ]*
                (?:
                    (?P<marker>```(?:``)*(?=[^`]))  # fenced-code marker (backticks)
                    | (?:<!--)              # or the html comment marker
                )

            # then, grab everything until the first end marker
            (?P<zone>.*?)

            # finally, the end marker
            (?(marker)    # if we matched a fenced-code maker previously
                  ^[ ]*(?P=marker) # then we must match the same amount of backticks
                  |(?:-->)    # otherwise, we must match the close of the html comment
            )
            ''', re.DOTALL | re.MULTILINE | re.VERBOSE
        )

    def __repr__(self):
        return "``` ... ``` or <!-- ... -->"
