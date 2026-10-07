The page is from the Encyclopædia Britannica, eleventh edition (Cambridge,
1910-1911), set in two columns.

An article begins with its title in bold capitals at the margin
('''ALGEBRAIC FORMS'''). A section within an article may open with a side
heading in italic, followed by a full stop and a dash: ''Symbolic Form''.—
Footnotes are printed at the foot of the page in smaller type.

CHEMISTRY is not mathematics: a chemical formula or equation is written in
the running text with <sub> for its subscript numbers, never in <math>:
SiI<sub>4</sub>+2C<sub>2</sub>H<sub>5</sub>OH = SiO<sub>2</sub>+…

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
