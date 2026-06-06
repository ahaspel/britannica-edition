"""`{{EB1911 Shoulder Heading|text}}` / `{{EB9 Margin Note|text}}` → an «SH» margin label.

Lifted byte-for-byte out of body_text (deleted) so the FIGURE producer (`_figure_faithful`,
its only caller) keeps working unchanged.  A balanced-brace reader — handles nested
`{{Fs|…}}` inside the heading and consumes surrounding newlines so the margin label doesn't
force a paragraph break.  The `_SH`/`_LNK` sentinels are kept local and the behaviour is
identical; folding this into the walker's SHOULDER_HEADING element is step 3, not now.
"""

from __future__ import annotations

import re

_SH = "\x07"   # shoulder-heading sentinel (finalised to «SH» downstream)
_LNK = "\x06"  # legacy link sentinel — inert here (content carries «LN»)


def _convert_shoulder_headings(text: str) -> str:
    prefixes = ("{{eb1911 shoulder heading", "{{eb9 margin note")
    while True:
        low = text.lower()
        cands = [(low.find(p), p) for p in prefixes]
        cands = [(pos, p) for pos, p in cands if pos >= 0]
        if not cands:
            break
        idx, prefix = min(cands)
        # Find balanced closing }}
        depth = 0
        i = idx
        while i < len(text) - 1:
            if text[i:i+2] == "{{":
                depth += 1
                i += 2
            elif text[i:i+2] == "}}":
                depth -= 1
                if depth == 0:
                    # Extract content: everything after the last top-level | .
                    inner = text[idx+len(prefix):i]

                    def _top_level_pipes(s):
                        d = 0
                        in_link = False
                        in_bracket = 0
                        pipes = []
                        k = 0
                        while k < len(s):
                            ch = s[k]
                            if ch == _LNK:
                                in_link = not in_link
                            elif not in_link:
                                if s[k:k+2] == "[[":
                                    in_bracket += 1
                                    k += 2
                                    continue
                                if s[k:k+2] == "]]":
                                    in_bracket -= 1
                                    k += 2
                                    continue
                                if ch == "{":
                                    d += 1
                                elif ch == "}":
                                    d -= 1
                                elif ch == "|" and d == 0 and in_bracket == 0:
                                    pipes.append(k)
                            k += 1
                        return pipes
                    pipes = _top_level_pipes(inner)
                    last_pipe = pipes[-1] if pipes else -1
                    heading_text = inner[last_pipe+1:] if last_pipe >= 0 else inner
                    # If we got an attribute instead of heading text, walk back
                    # through pipes until we find actual text
                    _ATTR_RE = re.compile(r"\s*(?:align|width|style)\s*=", re.IGNORECASE)
                    pipe_idx = len(pipes) - 1
                    while _ATTR_RE.match(heading_text) and pipe_idx > 0:
                        pipe_idx -= 1
                        prev_pipe = pipes[pipe_idx]
                        heading_text = inner[prev_pipe+1:last_pipe]
                        last_pipe = prev_pipe
                    # Strip inner templates, bold/italic, and line breaks
                    heading_text = re.sub(r"<br\s*/?>", " ", heading_text, flags=re.IGNORECASE)
                    heading_text = re.sub(r"\{\{[^{}]*\|([^{}]*)\}\}", r"\1", heading_text)
                    heading_text = (heading_text
                                    .replace("«B»", "").replace("«/B»", "")
                                    .replace("«I»", "").replace("«/I»", ""))
                    # Rejoin hyphenated words split across lines
                    heading_text = re.sub(r"(\w)- (\w)", r"\1\2", heading_text)
                    # Collapse em-spaces and extra whitespace
                    heading_text = heading_text.replace(" ", " ")
                    heading_text = re.sub(r"\s{2,}", " ", heading_text).strip()
                    marker = f"{_SH}SH{heading_text}{_SH}/SH"
                    # Consume surrounding newlines to keep text flowing
                    start = idx
                    end = i + 2
                    if start > 0 and text[start-1] == "\n":
                        start -= 1
                    if end < len(text) and text[end] == "\n":
                        end += 1
                    text = text[:start] + " " + marker + " " + text[end:]
                    break
                i += 2
            else:
                i += 1
        else:
            break  # unbalanced
    return text
