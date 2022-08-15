import sys, re, collections, pprint
from tabulate import tabulate

lang_re = re.compile(
    r'''^Lang[ ]
         (?P<language> \w+)[ ]
         test[ ]?
         (?:
            \( (?P<lang_version>  [^)]+) \)  | [^(]
         )
         ''', re.VERBOSE)

runner_re = re.compile(
    r''' (?P<language> \w+)[ ]
         Runner's[ ]version:[ ]
         \( (?P<runner_version>  [^)]+) \)$
         ''', re.VERBOSE)

failed_re = re.compile(
    r''' Failed[ ]to[ ]obtain[ ](?P<language> \w+)[ ]
         Runner's[ ]version.*$
         ''', re.VERBOSE)

def parse_line(line):
    '''
        >>> parse_line(r"Lang Ruby test (3.1)  ... Ruby Runner's version: (1.4.1)")
        ('Ruby', '3.1', '1.4.1')

        >>> parse_line(r"Lang Ruby test ... Ruby Runner's version: (1.4.1)")
        ('Ruby', 'latest', '1.4.1')

        >>> parse_line(r"Lang Ruby test ... Failed to obtain Ruby Runner's version ...")
        ('Ruby', 'latest', 'unknown (to review)')

        >>> parse_line(r"Lang Ruby test ... Failed to obtain Python Runner's version ...")
        None
    '''

    # "Lang Ruby test (3.1)  ... Ruby Runner's version: (1.4.1)"
    # |--------------------|
    m = lang_re.match(line)
    assert m

    language, lang_version = m.group('language', 'lang_version')
    if not lang_version:
        lang_version = 'latest'

    # "Lang Ruby test (3.1, v123)  ... Ruby Runner's version: (1.4.1)"
    runner_version = None
    if ',' in lang_version:
        lang_version, runner_version = [s.strip() for s in lang_version.split(',')]

    # "Lang Ruby test (3.1)  ... Failed to obtain Ruby Runner's version ..."
    #       ^^^^                |-----------------^^^^-----------------|
    m = failed_re.search(line)
    if m:
        language2 = m.group('language')
        if language == language2:
            # this case means that something went wrong when byexample
            # tried to retrieve the version of the runner
            if runner_version is None:
                runner_version = '-'
            return language, lang_version, runner_version

        # "Lang Ruby test (3.1)  ... Failed to obtain Python Runner's version ..."
        #       ^^^^                |-----------------^^^^^^-----------------|
        # In this case the failure is not a failure for our language of
        # interest so we skip the line
        return language, lang_version, None

    # "Lang Ruby test (3.1)  ... Ruby Runner's version: (0.9.6)"
    #       ^^^^                |^^^^--------------------------|
    m = runner_re.search(line)
    if not m:
        return language, lang_version, None

    language2, runner_version = m.group('language', 'runner_version')
    if language != language2:
        # Not our language of interest, skip the line
        return language, lang_version, None

    return language, lang_version, runner_version

matrix = collections.defaultdict(dict)
with open(sys.argv[1], 'rt') as f:
    for line in f:

        # If it is not a specific job for testing a language, skip it
        if not line.startswith('Lang '):
            continue

        # If it is not the specific step that run the tests, skip it
        if 'Run ' not in line or 'make lang-' not in line:
            continue

        language, lang_version, runner_version = parse_line(line)
        if runner_version:
            matrix[language][lang_version] = runner_version
        else:
            if lang_version not in matrix[language]:
                matrix[language][lang_version] = 'unknown'

begin_marker = '<!-- matrix CI begin -->'
end_marker = '<!-- matrix CI end -->'

fname_template = 'docs/languages/{}.md'

for language, data in matrix.items():
    data = [[lang_ver, runner_ver] for lang_ver, runner_ver in data.items()]

    doc_file = fname_template.format(language.lower())
    with open(doc_file, 'rt') as f:
        doc = f.read()

    if begin_marker not in doc or end_marker not in doc:
        raise Exception(f"Markers are missing in {doc_file}")

    head, remain = doc.split(begin_marker, 1)
    _, tail = remain.split(end_marker, 1)
    del remain

    table = tabulate(
        data,
        ["Language", "Runner/Interpreter"],
        tablefmt='github',
        disable_numparse=True
        )

    doc = head + begin_marker + '\n\n' + table + '\n\n' + end_marker + tail
    with open(doc_file, 'wt') as f:
        f.write(doc)
