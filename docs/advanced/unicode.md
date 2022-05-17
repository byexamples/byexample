<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none

--
-->

# Unicode Support

``byexample`` has full support for unicode examples.

```shell
$ echo 'por ejemplo'
por ejemplo

$ echo 'по примеру'
по примеру

$ echo '例によって'
例によって
```

If an example fails, ``byexample`` will show you the differences.
This also works if the output is unicode.

Consider the following examples in ``test/ds/bad-unicode``:

```shell
$ cat test/ds/bad-unicode            # byexample: +rm= 
 Those would fail:
 
 $ echo 'por-éjemplo'
 por ejemplo
 
 $ echo 'по-примеру!'
 по примеру
 
 $ echo '例によっ!て'
 例によって

```

Here are those examples failing:

```shell
$ byexample -l shell,python --diff ndiff test/ds/bad-unicode    # byexample: +rm= 
<...>
Differences:
- por ejemplo
?    ^^
 
+ por-éjemplo
?    ^^
<...>
Differences:
- по примеру
?   ^
 
+ по-примеру!
?   ^       +
<...>
Differences:
- 例によって
+ 例によっ!て
?     +
<...>
```

**Note:** the [``ndiff`` algorithm](/{{ site.uprefix }}/overview/differences)
will not put the ``+`` marker in the correct position
if the characters are *wide characters*.

## Encoding

By default, ``byexample`` will use the same encoding that ``Python`` uses
for its standard output, typically ``utf-8``.


You can change the encoding from the command line with ``--encoding``:

```shell
$ byexample -l shell --encoding utf-8 test/ds/bad-unicode
<...>
Expected:
por ejemplo
Got:
por-éjemplo
<...>
Expected:
по примеру
Got:
по-примеру!
<...>
Expected:
例によって
Got:
例によっ!て
<...>
```

The ``--encoding`` option only affects how to decode the files read.

The output that ``byexample`` prints is still interpreted using
the ``Python`` default encoding for the standard output.

If you want to change this behaviour set the environment
variable ``PYTHONIOENCODING``.

```shell
$ PYTHONIOENCODING='utf-8' byexample -l shell test/ds/bad-unicode | cat
<...>
Expected:
por ejemplo
Got:
por-éjemplo
<...>
```

> If you are using ``Python 2.7`` and you are redirecting the output of
> ``byexample`` to a file or pipe you will get an error saying that
> the encoding of the standard output is unset.
>
> This is a known issue of ``Python 2.x`` series which ignores the encoding of
> your terminal.
>
> The solution is to use ``PYTHONIOENCODING`` like before.

## Handling encoding errors

Sometimes, even if you had set the correct encoding it is possible to
find an example that just output weird stuff or binary non-sense.

By default `byexample` will fail with an error even if the example
ignores the output with a `<...>` or `+pass`

```shell
$ cat test/ds/binary-blob           # byexample: +skip
[Bin Start]<...>[Bin End]

$ byexample -l shell test/ds/output-bin
<...>
UnicodeDecodeError:<...>
<...>
[ABORT] Pass: 0 Fail: 0 Skip: 0
```

But it is possible to instruct `byexample` to handle the error
differently with the `--encoding` parameter,
like *replacing* the offending bytes by some character or just *ignoring*
them:

```shell
$ byexample -l shell --encoding utf8:replace test/ds/output-bin
<...>
[PASS] Pass: 1 Fail: 0 Skip: 0
```

> The `PYTHONIOENCODING` environment variable also accepts a similar
> syntax. See the documentation of the `python` interpreter.

## Limitations

If you are running ``byexample`` using ``Python 2.7`` *and* you
enable [ANSI terminal emulation](/{{ site.uprefix }}/advanced/terminal-emulation)
with ``+term=ansi``, any non-ascii characters will be removed.

This is a limitation of one of ``byexample``'s dependencies and
only applies under that specific scenario.

``Python 2.x`` reached to its *end of life* in January 2020. Consider
upgrade it.

## Terminal/font support (TL;DR)

It is possible that you cannot see the symbols in a diff if your
terminal does not have support for them (or you don't have the glyph in
your font).

This is the output of the Markus Kuhn's demo that you can use
for testing your terminal. Just download the file and do a `cat`

```shell
# wget https://github.com/byexamples/byexample/blob/master/test/ds/UTF-8-demo.txt -O- > test/ds/UTF-8-demo.txt # byexample: +skip
$ cat test/ds/UTF-8-demo.txt    # byexample: +rm= 
 
 UTF-8 encoded sample plain-text file
 ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
 
 Markus Kuhn [ˈmaʳkʊs kuːn] <...> — 2002-07-25 CC BY
 
 
 The ASCII compatible UTF-8 encoding used in this plain-text file
 is defined in Unicode, ISO 10646-1, and RFC 2279.
 
 
 Using Unicode/UTF-8, you can write in emails and source code things such as
 
 Mathematics and sciences:
 
   ∮ E⋅da = Q,  n → ∞, ∑ f(i) = ∏ g(i),      ⎧⎡⎛┌─────┐⎞⎤⎫
                                             ⎪⎢⎜│a²+b³ ⎟⎥⎪
   ∀x∈ℝ: ⌈x⌉ = −⌊−x⌋, α ∧ ¬β = ¬(¬α ∨ β),    ⎪⎢⎜│───── ⎟⎥⎪
                                             ⎪⎢⎜⎷ c₈   ⎟⎥⎪
   ℕ ⊆ ℕ₀ ⊂ ℤ ⊂ ℚ ⊂ ℝ ⊂ ℂ,                   ⎨⎢⎜       ⎟⎥⎬
                                             ⎪⎢⎜ ∞     ⎟⎥⎪
   ⊥ < a ≠ b ≡ c ≤ d ≪ ⊤ ⇒ (⟦A⟧ ⇔ ⟪B⟫),      ⎪⎢⎜ ⎲     ⎟⎥⎪
                                             ⎪⎢⎜ ⎳aⁱ-bⁱ⎟⎥⎪
   2H₂ + O₂ ⇌ 2H₂O, R = 4.7 kΩ, ⌀ 200 mm     ⎩⎣⎝i=1    ⎠⎦⎭
 
 Linguistics and dictionaries:
 
   ði ıntəˈnæʃənəl fəˈnɛtık əsoʊsiˈeıʃn
   Y [ˈʏpsilɔn], Yen [jɛn], Yoga [ˈjoːgɑ]
 
 APL:
 
   ((V⍳V)=⍳⍴V)/V←,V    ⌷←⍳→⍴∆∇⊃‾⍎⍕⌈
 
 Nicer typography in plain text files:
 
   ╔══════════════════════════════════════════╗
   ║                                          ║
   ║   • ‘single’ and “double” quotes         ║
   ║                                          ║
   ║   • Curly apostrophes: “We’ve been here” ║
   ║                                          ║
   ║   • Latin-1 apostrophe and accents: '´`  ║
   ║                                          ║
   ║   • ‚deutsche‘ „Anführungszeichen“       ║
   ║                                          ║
   ║   • †, ‡, ‰, •, 3–4, —, −5/+5, ™, …      ║
   ║                                          ║
   ║   • ASCII safety test: 1lI|, 0OD, 8B     ║
   ║                      ╭─────────╮         ║
   ║   • the euro symbol: │ 14.95 € │         ║
   ║                      ╰─────────╯         ║
   ╚══════════════════════════════════════════╝
 
 Combining characters:
 
   STARGΛ̊TE SG-1, a = v̇ = r̈, a⃑ ⊥ b⃑
 
 Greek (in Polytonic):
 
   The Greek anthem:
 
   Σὲ γνωρίζω ἀπὸ τὴν κόψη
   τοῦ σπαθιοῦ τὴν τρομερή,
   σὲ γνωρίζω ἀπὸ τὴν ὄψη
   ποὺ μὲ βία μετράει τὴ γῆ.
 
   ᾿Απ᾿ τὰ κόκκαλα βγαλμένη
   τῶν ῾Ελλήνων τὰ ἱερά
   καὶ σὰν πρῶτα ἀνδρειωμένη
   χαῖρε, ὦ χαῖρε, ᾿Ελευθεριά!
 
   From a speech of Demosthenes in the 4th century BC:
 
   Οὐχὶ ταὐτὰ παρίσταταί μοι γιγνώσκειν, ὦ ἄνδρες ᾿Αθηναῖοι,
   ὅταν τ᾿ εἰς τὰ πράγματα ἀποβλέψω καὶ ὅταν πρὸς τοὺς
   λόγους οὓς ἀκούω· τοὺς μὲν γὰρ λόγους περὶ τοῦ
   τιμωρήσασθαι Φίλιππον ὁρῶ γιγνομένους, τὰ δὲ πράγματ᾿
   εἰς τοῦτο προήκοντα,  ὥσθ᾿ ὅπως μὴ πεισόμεθ᾿ αὐτοὶ
   πρότερον κακῶς σκέψασθαι δέον. οὐδέν οὖν ἄλλο μοι δοκοῦσιν
   οἱ τὰ τοιαῦτα λέγοντες ἢ τὴν ὑπόθεσιν, περὶ ἧς βουλεύεσθαι,
   οὐχὶ τὴν οὖσαν παριστάντες ὑμῖν ἁμαρτάνειν. ἐγὼ δέ, ὅτι μέν
   ποτ᾿ ἐξῆν τῇ πόλει καὶ τὰ αὑτῆς ἔχειν ἀσφαλῶς καὶ Φίλιππον
   τιμωρήσασθαι, καὶ μάλ᾿ ἀκριβῶς οἶδα· ἐπ᾿ ἐμοῦ γάρ, οὐ πάλαι
   γέγονεν ταῦτ᾿ ἀμφότερα· νῦν μέντοι πέπεισμαι τοῦθ᾿ ἱκανὸν
   προλαβεῖν ἡμῖν εἶναι τὴν πρώτην, ὅπως τοὺς συμμάχους
   σώσομεν. ἐὰν γὰρ τοῦτο βεβαίως ὑπάρξῃ, τότε καὶ περὶ τοῦ
   τίνα τιμωρήσεταί τις καὶ ὃν τρόπον ἐξέσται σκοπεῖν· πρὶν δὲ
   τὴν ἀρχὴν ὀρθῶς ὑποθέσθαι, μάταιον ἡγοῦμαι περὶ τῆς
   τελευτῆς ὁντινοῦν ποιεῖσθαι λόγον.
 
   Δημοσθένους, Γ´ ᾿Ολυνθιακὸς
 
 Georgian:
 
   From a Unicode conference invitation:
 
   გთხოვთ ახლავე გაიაროთ რეგისტრაცია Unicode-ის მეათე საერთაშორისო
   კონფერენციაზე დასასწრებად, რომელიც გაიმართება 10-12 მარტს,
   ქ. მაინცში, გერმანიაში. კონფერენცია შეჰკრებს ერთად მსოფლიოს
   ექსპერტებს ისეთ დარგებში როგორიცაა ინტერნეტი და Unicode-ი,
   ინტერნაციონალიზაცია და ლოკალიზაცია, Unicode-ის გამოყენება
   ოპერაციულ სისტემებსა, და გამოყენებით პროგრამებში, შრიფტებში,
   ტექსტების დამუშავებასა და მრავალენოვან კომპიუტერულ სისტემებში.
 
 Russian:
 
   From a Unicode conference invitation:
 
   Зарегистрируйтесь сейчас на Десятую Международную Конференцию по
   Unicode, которая состоится 10-12 марта 1997 года в Майнце в Германии.
   Конференция соберет широкий круг экспертов по  вопросам глобального
   Интернета и Unicode, локализации и интернационализации, воплощению и
   применению Unicode в различных операционных системах и программных
   приложениях, шрифтах, верстке и многоязычных компьютерных системах.
 
 Thai (UCS Level 2):
 
   Excerpt from a poetry on The Romance of The Three Kingdoms (a Chinese
   classic 'San Gua'):
 
   [----------------------------|------------------------]
     ๏ แผ่นดินฮั่นเสื่อมโทรมแสนสังเวช  พระปกเกศกองบู๊กู้ขึ้นใหม่
   สิบสองกษัตริย์ก่อนหน้าแลถัดไป       สององค์ไซร้โง่เขลาเบาปัญญา
     ทรงนับถือขันทีเป็นที่พึ่ง           บ้านเมืองจึงวิปริตเป็นนักหนา
   โฮจิ๋นเรียกทัพทั่วหัวเมืองมา         หมายจะฆ่ามดชั่วตัวสำคัญ
     เหมือนขับไสไล่เสือจากเคหา      รับหมาป่าเข้ามาเลยอาสัญ
   ฝ่ายอ้องอุ้นยุแยกให้แตกกัน          ใช้สาวนั้นเป็นชนวนชื่นชวนใจ
     พลันลิฉุยกุยกีกลับก่อเหตุ          ช่างอาเพศจริงหนาฟ้าร้องไห้
   ต้องรบราฆ่าฟันจนบรรลัย           ฤๅหาใครค้ำชูกู้บรรลังก์ ฯ
 
   (The above is a two-column text. If combining characters are handled
   correctly, the lines of the second column should be aligned with the
   | character above.)
 
 Ethiopian:
 
   Proverbs in the Amharic language:
 
   ሰማይ አይታረስ ንጉሥ አይከሰስ።
   ብላ ካለኝ እንደአባቴ በቆመጠኝ።
   ጌጥ ያለቤቱ ቁምጥና ነው።
   ደሀ በሕልሙ ቅቤ ባይጠጣ ንጣት በገደለው።
   የአፍ ወለምታ በቅቤ አይታሽም።
   አይጥ በበላ ዳዋ ተመታ።
   ሲተረጉሙ ይደረግሙ።
   ቀስ በቀስ፥ ዕንቁላል በእግሩ ይሄዳል።
   ድር ቢያብር አንበሳ ያስር።
   ሰው እንደቤቱ እንጅ እንደ ጉረቤቱ አይተዳደርም።
   እግዜር የከፈተውን ጉሮሮ ሳይዘጋው አይድርም።
   የጎረቤት ሌባ፥ ቢያዩት ይስቅ ባያዩት ያጠልቅ።
   ሥራ ከመፍታት ልጄን ላፋታት።
   ዓባይ ማደሪያ የለው፥ ግንድ ይዞ ይዞራል።
   የእስላም አገሩ መካ የአሞራ አገሩ ዋርካ።
   ተንጋሎ ቢተፉ ተመልሶ ባፉ።
   ወዳጅህ ማር ቢሆን ጨርስህ አትላሰው።
   እግርህን በፍራሽህ ልክ ዘርጋ።
 
 Runes:
 
   ᚻᛖ ᚳᚹᚫᚦ ᚦᚫᛏ ᚻᛖ ᛒᚢᛞᛖ ᚩᚾ ᚦᚫᛗ ᛚᚪᚾᛞᛖ ᚾᚩᚱᚦᚹᛖᚪᚱᛞᚢᛗ ᚹᛁᚦ ᚦᚪ ᚹᛖᛥᚫ
 
   (Old English, which transcribed into Latin reads 'He cwaeth that he
   bude thaem lande northweardum with tha Westsae.' and means 'He said
   that he lived in the northern land near the Western Sea.')
 
 Braille:
 
   ⡌⠁⠧⠑ ⠼⠁⠒  ⡍⠜⠇⠑⠹⠰⠎ ⡣⠕⠌
 
   ⡍⠜⠇⠑⠹ ⠺⠁⠎ ⠙⠑⠁⠙⠒ ⠞⠕ ⠃⠑⠛⠔ ⠺⠊⠹⠲ ⡹⠻⠑ ⠊⠎ ⠝⠕ ⠙⠳⠃⠞
   ⠱⠁⠞⠑⠧⠻ ⠁⠃⠳⠞ ⠹⠁⠞⠲ ⡹⠑ ⠗⠑⠛⠊⠌⠻ ⠕⠋ ⠙⠊⠎ ⠃⠥⠗⠊⠁⠇ ⠺⠁⠎
   ⠎⠊⠛⠝⠫ ⠃⠹ ⠹⠑ ⠊⠇⠻⠛⠹⠍⠁⠝⠂ ⠹⠑ ⠊⠇⠻⠅⠂ ⠹⠑ ⠥⠝⠙⠻⠞⠁⠅⠻⠂
   ⠁⠝⠙ ⠹⠑ ⠡⠊⠑⠋ ⠍⠳⠗⠝⠻⠲ ⡎⠊⠗⠕⠕⠛⠑ ⠎⠊⠛⠝⠫ ⠊⠞⠲ ⡁⠝⠙
   ⡎⠊⠗⠕⠕⠛⠑⠰⠎ ⠝⠁⠍⠑ ⠺⠁⠎ ⠛⠕⠕⠙ ⠥⠏⠕⠝ ⠰⡡⠁⠝⠛⠑⠂ ⠋⠕⠗ ⠁⠝⠹⠹⠔⠛ ⠙⠑
   ⠡⠕⠎⠑ ⠞⠕ ⠏⠥⠞ ⠙⠊⠎ ⠙⠁⠝⠙ ⠞⠕⠲
 
   ⡕⠇⠙ ⡍⠜⠇⠑⠹ ⠺⠁⠎ ⠁⠎ ⠙⠑⠁⠙ ⠁⠎ ⠁ ⠙⠕⠕⠗⠤⠝⠁⠊⠇⠲
 
   ⡍⠔⠙⠖ ⡊ ⠙⠕⠝⠰⠞ ⠍⠑⠁⠝ ⠞⠕ ⠎⠁⠹ ⠹⠁⠞ ⡊ ⠅⠝⠪⠂ ⠕⠋ ⠍⠹
   ⠪⠝ ⠅⠝⠪⠇⠫⠛⠑⠂ ⠱⠁⠞ ⠹⠻⠑ ⠊⠎ ⠏⠜⠞⠊⠊⠥⠇⠜⠇⠹ ⠙⠑⠁⠙ ⠁⠃⠳⠞
   ⠁ ⠙⠕⠕⠗⠤⠝⠁⠊⠇⠲ ⡊ ⠍⠊⠣⠞ ⠙⠁⠧⠑ ⠃⠑⠲ ⠔⠊⠇⠔⠫⠂ ⠍⠹⠎⠑⠇⠋⠂ ⠞⠕
   ⠗⠑⠛⠜⠙ ⠁ ⠊⠕⠋⠋⠔⠤⠝⠁⠊⠇ ⠁⠎ ⠹⠑ ⠙⠑⠁⠙⠑⠌ ⠏⠊⠑⠊⠑ ⠕⠋ ⠊⠗⠕⠝⠍⠕⠝⠛⠻⠹
   ⠔ ⠹⠑ ⠞⠗⠁⠙⠑⠲ ⡃⠥⠞ ⠹⠑ ⠺⠊⠎⠙⠕⠍ ⠕⠋ ⠳⠗ ⠁⠝⠊⠑⠌⠕⠗⠎
   ⠊⠎ ⠔ ⠹⠑ ⠎⠊⠍⠊⠇⠑⠆ ⠁⠝⠙ ⠍⠹ ⠥⠝⠙⠁⠇⠇⠪⠫ ⠙⠁⠝⠙⠎
   ⠩⠁⠇⠇ ⠝⠕⠞ ⠙⠊⠌⠥⠗⠃ ⠊⠞⠂ ⠕⠗ ⠹⠑ ⡊⠳⠝⠞⠗⠹⠰⠎ ⠙⠕⠝⠑ ⠋⠕⠗⠲ ⡹⠳
   ⠺⠊⠇⠇ ⠹⠻⠑⠋⠕⠗⠑ ⠏⠻⠍⠊⠞ ⠍⠑ ⠞⠕ ⠗⠑⠏⠑⠁⠞⠂ ⠑⠍⠏⠙⠁⠞⠊⠊⠁⠇⠇⠹⠂ ⠹⠁⠞
   ⡍⠜⠇⠑⠹ ⠺⠁⠎ ⠁⠎ ⠙⠑⠁⠙ ⠁⠎ ⠁ ⠙⠕⠕⠗⠤⠝⠁⠊⠇⠲
 
   (The first couple of paragraphs of "A Christmas Carol" by Dickens)
 
 Compact font selection example text:
 
   ABCDEFGHIJKLMNOPQRSTUVWXYZ /0123456789
   abcdefghijklmnopqrstuvwxyz £©µÀÆÖÞßéöÿ
   –—‘“”„†•…‰™œŠŸž€ ΑΒΓΔΩαβγδω АБВГДабвгд
   ∀∂∈ℝ∧∪≡∞ ↑↗↨↻⇣ ┐┼╔╘░►☺♀ ﬁ�⑀₂ἠḂӥẄɐː⍎אԱა
 
 Greetings in various languages:
 
   Hello world, Καλημέρα κόσμε, コンニチハ
 
 Box drawing alignment tests:                                          █
                                                                       ▉
   ╔══╦══╗  ┌──┬──┐  ╭──┬──╮  ╭──┬──╮  ┏━━┳━━┓  ┎┒┏┑   ╷  ╻ ┏┯┓ ┌┰┐    ▊ ╱╲╱╲╳╳╳
   ║┌─╨─┐║  │╔═╧═╗│  │╒═╪═╕│  │╓─╁─╖│  ┃┌─╂─┐┃  ┗╃╄┙  ╶┼╴╺╋╸┠┼┨ ┝╋┥    ▋ ╲╱╲╱╳╳╳
   ║│╲ ╱│║  │║   ║│  ││ │ ││  │║ ┃ ║│  ┃│ ╿ │┃  ┍╅╆┓   ╵  ╹ ┗┷┛ └┸┘    ▌ ╱╲╱╲╳╳╳
   ╠╡ ╳ ╞╣  ├╢   ╟┤  ├┼─┼─┼┤  ├╫─╂─╫┤  ┣┿╾┼╼┿┫  ┕┛┖┚     ┌┄┄┐ ╎ ┏┅┅┓ ┋ ▍ ╲╱╲╱╳╳╳
   ║│╱ ╲│║  │║   ║│  ││ │ ││  │║ ┃ ║│  ┃│ ╽ │┃  ░░▒▒▓▓██ ┊  ┆ ╎ ╏  ┇ ┋ ▎
   ║└─╥─┘║  │╚═╤═╝│  │╘═╪═╛│  │╙─╀─╜│  ┃└─╂─┘┃  ░░▒▒▓▓██ ┊  ┆ ╎ ╏  ┇ ┋ ▏
   ╚══╩══╝  └──┴──┘  ╰──┴──╯  ╰──┴──╯  ┗━━┻━━┛  ▗▄▖▛▀▜   └╌╌┘ ╎ ┗╍╍┛ ┋  ▁▂▃▄▅▆▇█
                                                ▝▀▘▙▄▟
```
