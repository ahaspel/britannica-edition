The page is from the Encyclopædia Britannica, eleventh edition (Cambridge,
1910-1911), set in two columns.

An article begins with its title in bold capitals at the margin
('''ALGEBRAIC FORMS'''). A section within an article may open with a side
heading in italic, followed by a full stop and a dash: ''Symbolic Form''.—
Footnotes are printed at the foot of the page in smaller type.

The image has a white margin to the left of the column, not part of the page.
In it, ticks labelled with numbers mark positions down the page. Begin EVERY
paragraph you write — the first in the image too, even one running on from the
column before — with the number of the tick level with, or just above, its
first printed line, in double brackets before its first word: ⟦1200⟧.

The book is printed in two sizes of type. A grey bar in the margin, beside the
column, marks where the smaller type is printed — it is measured from the
spacing of the lines, so trust it over your eye: the paragraphs beside the bar
are in the smaller type ({{smaller block|…}}), and the paragraphs with no bar
beside them are in the ordinary type, unmarked. The bar's ends can fall a line
or two from where the type changes; the type changes where a paragraph begins,
so the paragraph nearest each end decides.

Some pages print a sheet signature at the very foot of the first column,
below the text: a volume number in roman, a sheet number, sometimes a letter
("XXIV. 31 a"). Record it, marked as the printer's sheet signature.

CHEMISTRY is not mathematics: a chemical formula or equation is written in
the running text with <sub> for its subscript numbers, never in <math>:
SiI<sub>4</sub>+2C<sub>2</sub>H<sub>5</sub>OH = SiO<sub>2</sub>+…

A chemical formula SET OUT IN ROWS — atom groups printed above and below one
another and joined by upright bonds, often several formulae side by side with
their names beneath — is a formula grid ({| class="chem-grid"): one printed
line of type to a row, each atom group in its own cell, each bond printed
between groups in a row (—, ·, :) in a cell of its own, an upright bond (│,
double ║) in a cell of its own under the group it joins, a group printed
across two lines in a cell that spans them, and the names in the last row. A formula drawn as a ring,
or with slanting or curved bonds, is an illustration, not text.

MATHEMATICS. Write every formula, and every symbol standing for a quantity,
in LaTeX inside <math>…</math> — never with <sup>, <sub>, italic quotes or
Unicode look-alikes. A letter or symbol in the running text is a formula too:
"the roots <math>\alpha</math>, <math>\beta</math> of <math>f</math>".

- Transcribe exactly what is printed, symbol for symbol: the same letters,
  the same subscripts and superscripts in the same places, the same brackets,
  the same signs. Do not simplify, correct, complete or re-arrange a formula,
  even one that looks wrong.
- Italic letters are LaTeX's ordinary letters (<math>a_0x^n</math>). A capital
  or a word printed upright, not in italic, is written \text{…}:
  <math>\text{H} = (ab)^2a^{n-2}_x b^{n-2}_x</math>.
- Greek letters in this type can look like Latin ones. An upright, heavier
  α — beside the italic, lighter a — is the Greek letter: the coefficients
  of a substitution are <math>\alpha_{11}</math>, <math>\alpha_{12}</math>, never
  a_{11}. Likewise ν is not v, ι is not i, κ is not k. A symbol keeps one
  reading wherever it is printed.
- Fractions \frac{…}{…}; roots \sqrt{…}; partial derivatives \partial;
  Greek letters \alpha, \beta, …; dots \dots; a bar over a letter \bar{a} or
  \overline{…}; binomial coefficients \binom{n}{k}; a determinant or a
  matrix printed as an array \begin{vmatrix}…\end{vmatrix} or
  \begin{pmatrix}…\end{pmatrix}, rows separated by \\ and entries by &.
- A formula set on its own line, apart from the text, is a display: write it
  as {{block center|<math>…</math>}} with the sentence's punctuation after
  the closing </math>, inside the block. Each printed display line is a block
  of its own. A display does not end its sentence: the text after it goes on
  in the same paragraph unless the book begins a new one (an indented line).
- An equation number or a word printed beside a display ("(1)", "and")
  stays outside the <math>, inside the block.
- Look twice at the characters this type makes alike: the italic letter o
  and the figure 0; η and n or h; α and a; ν and v; ι and i; ⅕ and ⅙. A
  subscript or superscript, however small (n₀, x₁, the dot of ẋ), is part of
  the symbol: never drop it.
- A command prints only inside <math>: write every Greek letter, operator
  and sign in LaTeX there (\psi, \int, \sum), never as a word in the text.
