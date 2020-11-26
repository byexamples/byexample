echo -e 'source "https://rubygems.org"\ngem "github-pages"' > Gemfile
bundle install && cd docs && bundle exec jekyll build

