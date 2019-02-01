# file names from the docs folder (only markdown files, exclude examples folder)
ls -1 docs/*/*.md | sed 's/\.md$//' | sed 's/^docs//g' | grep -v '^/examples/' | sort > .fnames.tmp

# links to the docs files
grep "site.uprefix" docs/_includes/idx.html | sed 's/^.*site.uprefix }}//g' | sed 's/\([^"]*\)".*$/\1/g' | sort > .flinks.tmp

# print any difference: missing links to existent files/dangling links pointing to nowhere
diff .fnames.tmp .flinks.tmp | grep '^[<>]' | sed 's/^</Missing link to: /g' | sed 's/^>/Dangling link: /g' | sort

# return the same exit code than:
diff .fnames.tmp .flinks.tmp > /dev/null
