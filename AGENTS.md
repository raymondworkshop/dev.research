## Study Operating Manual
Personal knowledge base for learning, improvement, and content research. 
- read → notes → wiki → apply.

### Folders
| Path | Who | Role |
|------|-----|------|
| `notes/` | you | Never modify |
| `books/` | you | Full text for cites |
| `wiki/` | AI | Theme pages |
| `outputs/` | AI | Long reports |

### Rules
- `notes/` + `books/` are the sources of truth. `wiki/` is curated theme pages (not a highlight dump).
- In wiki: strip export labels (`[info]`, `[insights]`, `[how]`); file author meaning cleanly.
- AI-written wiki prose (intros, merges, framing from `make sync` / compile) must be prefixed inline as `[AI Synthesis]:` on the same line as the text.
- Study-partner plans use `AI:`.
- Cite only that note’s `#### reference` (prefer `books/…` paths).
- No chapter summaries / quizzes unless asked.

### Signals in notes (from `books-export`) — for compile/study only; do not copy into wiki
| Mark | Meaning | Use |
|------|---------|-----|
| `###` / green | theme | strong theme hint |
| `**bold**` / purple | insight | *suggestion* for a theme (merge/skip OK) |
| `[insights]` / pink | insight | *suggestion* for a theme (merge/skip OK) |
| `[how]` / blue | action | *suggestion* for `### Actions` / study-partner try |
| `[info]` / yellow | detail | under a theme, not a new theme |

### Pipeline
1. **Export** — Apple Books → `notes/`  
   `make books-export BOOK='title|id'` · `LIST=1` to list ids  
   Colors → table above (paragraph-merge, chapter `##`, green→`###`).

2. **Compile** — `notes/` → `wiki/<theme>.md`  
   Prefer `###` for pages; treat bold / insights as theme *suggestions* (group, rename, or drop).  
   Turn suggested `[how]` into plain `### Actions` bullets (no `[how]` tag).  
   Template: `[AI Synthesis]:` intro → `###` → `### Actions` → `## Sources` → `## Related Topics`  
   `make sync NOTE='notes/….md'` · optional `THEMES='a,b'` · `DRY=1` → draft.

3. **Study partner** — real issue + note/`#### reference` only.  
   Pick 1 suggested `[how]` to try + `AI:` plan · 1–2 questions.

4. **Query** — via `wiki/INDEX.md`: Summary → Findings → Evidence → Recommendations. Complex → `outputs/`.

5. **Audit** — orphans, bad `[[links]]`, contradictions. `make audit`.
