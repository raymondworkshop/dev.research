#### dev.research

Research: going deep on a topic over weeks or months — reading papers, articles, reports, and incrementally building a comprehensive wiki with an evolving thesis.


Reading a book: filing each chapter as you go, building out pages for characters, themes, plot threads, and how they connect. By the end you have a rich companion wiki. Think of fan wikis like Tolkien Gateway — thousands of interlinked pages covering characters, places, events, languages, built by a community of volunteers over years. You could build something like that personally as you read, with the LLM doing all the cross-referencing and maintenance.


#### dir
myresearch/
├── raw/ (input dump)
├── wiki/ (AI-organized knowledge base)
├── outputs/ (AI-generated reports and answers)
└── CLAUDE.md (operating instructions for the AI)

#### wiki
prompt = "Read everything in raw/. Following the rules in CLAUDE.md, build a complete wiki in wiki/.

Start by creating INDEX.md listing every major topic alphabetically.
Then create one .md file per topic. Link related topics using
[[topic-name]] format. Summarize every source document.

Flag any contradictions you find between sources. 

Never translate the source language. Match the output language to the input language perfectly
"

#### review
Review the entire wiki/ directory. Complete this audit:
1. Flag contradictions between articles
2. Find topics mentioned but never fully explained
3. List claims not backed by a source in raw/
4. Identify stale information (>90 days without update)
5. Suggest 3 new articles to fill knowledge gaps

#### reference
* []