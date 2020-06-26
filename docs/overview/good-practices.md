# Good practices

Writing with `byexample` serves two purposes: have a good quality
documentation and a nice set of automated tests.

Here are some good practices and tips that will help you along the way:

 - **Tell a story:** imagine that you are explaining your awesome tool or
   feature to a friend, now write it. It is much easier to read a *story*
   than a boring manual reference. If you get stuck, just start
   writing disconnected phrases; once you start writing, you will feel
   how the words flow.
 - Keep an eye on the **orthography**: it has not be perfect, but a good
   orthography helps a lot to the reader. Use tools for corrections and
   a translator if you are not a native speaker.
 - **Make it beautiful:** no fancy stuff is needed, just a little of
   [markdown](https://en.wikipedia.org/wiki/Hyperlink) is all what you need:
   use bold and italics to **highlight** the words that you want to stress and
   use links to connect your tests.
 - **Be defensive:** don't assume that your tests will run in a clean
   environment; clean it at the begin and
   [fail fast](https://byexamples.github.io/byexample/basic/setup-and-tear-down)
   if you can't.
 - **Be a good citizen:** play nice and clean the environment once you
   [finish](https://byexamples.github.io/byexample/basic/setup-and-tear-down).
 - **Be agile:** `byexample` is flexible, you can
   [combine](https://byexamples.github.io/byexample/recipes/advanced-checks)
   several interpreters in same document and do strict or relaxed checks as you
   need. Keep it simple, *because it is*.
