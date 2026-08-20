# KDP correspondence — why there is no complete-edition Kindle

The evidence behind a public claim. Everything else in this repository can be
regenerated from the source and the code; this cannot, so it is kept here rather
than in a support inbox.

## What was submitted

The complete edition as EPUB — **37,226 articles, 888 chunks, 10,744 images,
~579 MB** — inside KDP's stated 650 MB ceiling. (200 MB is only the
Send-to-Kindle personal-documents cap, not a publishing limit.)

## What we had already established locally

* **Kindle Previewer bisection (2026-07):** ≤6,582 articles convert; ≥7,902 fail.
* **Full corpus:** Previewer runs, switches to the "enhancing for Kindle reader"
  stage, then logs **"Book conversion successful" and emits no artifact**.
* **Half corpus** (`--volume 1..14`, 18,476 articles / 5,352 images / 250.7 MB):
  behaves identically — the same hollow success. Half the corpus is 2.3× over the
  July ceiling, so this was predictable from the bisection.
* The vol-1 sampler **does** convert to a real KPF, so the toolchain works; it is
  scale that fails.

Three independent failures: full corpus, half corpus, and KDP's own ingestion.

## The reply (KDP Senior Support, 2026-08-15)

> This is Muneer from the KDP Senior Support Team.
>
> Thank you for your patience while I reached out to our technical team regarding
> the challenges we're facing with your file.
>
> Our Technical Team has responded with the following information:
> "The fact that kindle create cannot ingest the file to create a KPF is
> indicative of the corruption in the publisher's pub file. The publisher's file
> is too complex, and takes too long to process, resulting in the upload failure
> the publisher is experiencing. To be clear, we cannot open the file shared by
> the publisher due to this issue.
>
> The publisher will need to make a new file from their epub file, ensuring the
> complexity of the file is reduced. We recommend the publisher create a KPF
> using Kindle Create, and upload the revised file for processing."
>
> While I understand that this is not the answer you were looking for, as we had
> discussed that your testing confirmed there is no corruption, they have
> confirmed that the file is too complex for our system.
>
> I sincerely hope you are able to reduce this complexity so that we can try to
> publish your file and hopefully continue publishing any future titles you may
> create.
>
> Kindle Create supports .jpg, jpeg, or .png formatted images.
>
> Kindle Create recommends starting with .Doc//Docx files for creating novels,
> essays, poetry, and non-fiction books.
>
> If you're creating comics books, text books, travel guides, cookbooks, or music
> books, we recommend using .PDF files.

## How to use it

**Quote Muneer's summary, not the technical team's paragraph:**

> "…as we had discussed that your testing confirmed there is no corruption, they
> have confirmed that the file is too complex for our system."

That is Amazon's own words, it withdraws the corruption theory in light of our
testing, and it says **their system** — not the format. The technical team's
block opens by asserting "corruption in the publisher's pub file" and then
contradicts itself two sentences later by explaining the failure as complexity
and processing time; reproducing it publishes Amazon's claim that the file is
corrupt and hands a critic the quote to dismiss the edition with.

**What the email supports, precisely:** Amazon cannot process a book of this
scale, confirmed by their own technical team with the file in hand. It does NOT
support "the Kindle format cannot represent this book" — a 7–8 part edition
would convert. That was rejected on editorial grounds, not technical ones: each
part carries roughly half its cross-references degraded to live-site URLs, and
the tolerance was two parts.

The stronger claim for copy is therefore the positive one — *an eight-part
edition was declined because it would break the cross-references that make the
edition usable* — with Amazon's sentence as the supporting fact.

**The remedy offered is a non-answer at this scale.** Kindle Create with
`.doc`/`.docx`, or PDF for cookbooks and travel guides, addressed to a 37,226-
article reference work. No size or complexity limit was ever named, in this
message or anywhere in the exchange, and no escalation path was offered.

See [[project_render_to_python]] for the build-side record and the closed-verdict
reasoning.
