import os
import sys
import subprocess
import google.generativeai as genai
from pathlib import Path

# Configure Gemini API - Ensure GOOGLE_API_KEY is in your environment variables
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

def get_changed_files():
    """Detects files changed in the last commit if no specific file is provided."""
    try:
        result = subprocess.check_output(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"],
            stderr=subprocess.STDOUT
        ).decode("utf-8")
        return [f for f in result.splitlines() if f.startswith("raw/") and f.endswith(".md")]
    except Exception:
        return []

def update_index():
    """Regenerates wiki/INDEX.md based on current wiki files."""
    wiki_dir = Path("wiki")
    files = sorted([f.stem for f in wiki_dir.glob("*.md") if f.name != "INDEX.md"])
    index_content = "# Stoicism Wiki Index\n\n" + "\n".join([f"- [[{name}]]" for name in files])
    (wiki_dir / "INDEX.md").write_text(index_content)
    print("[*] wiki/INDEX.md refreshed.")

def get_wiki_context():
    """Gathers snippets from existing wiki to help AI detect contradictions and link topics."""
    wiki_dir = Path("wiki")
    context = []
    for f in wiki_dir.glob("*.md"):
        if f.name == "INDEX.md": continue
        # Read first 5 lines (usually title + summary) to provide context without hitting token limits
        content = f.read_text().splitlines()[:5]
        context.append(f"File: {f.name}\nContent: {' '.join(content)}")
    return "\n\n".join(context)

def process_file(file_path, model, standards, wiki_context):
    """Sends raw content to Gemini and saves the resulting wiki updates."""
    raw_content = Path(file_path).read_text()
    filename = os.path.basename(file_path)
    
    prompt = f"""
    Context: I am updating my research wiki based on new raw material.
    
    Existing Wiki Knowledge:
    {wiki_context}

    Raw Source File: {filename}
    Raw Content:
    {raw_content}

    Task:
    Following the standards in GEMINI.md, update or create wiki articles.
    1. Match the output language to the input language perfectly.
    2. Flag contradictions between this new source and the Existing Wiki Knowledge.
    3. If a contradiction is found, add a '## CONTRADICTION ALERT' section to the article.
    4. Use [[topic-name]] to link to existing or new articles.

    Return the result in this exact format for each article:
    ---FILE: topic-name.md---
    <article content starting with 2-sentence summary>
    """

    response = model.generate_content(prompt)
    
    # Basic parser for the AI's response to extract filenames and content
    parts = response.text.split("---FILE: ")
    for part in parts:
        if not part.strip(): continue
        try:
            fname, content = part.split("---", 1)
            fname = fname.strip()
            target_path = Path("wiki") / fname
            target_path.write_text(content.strip())
            print(f"[+] Updated wiki/{fname}")
        except ValueError:
            continue

def sync_wiki():
    if not os.environ.get("GOOGLE_API_KEY"):
        print("[!] Error: GOOGLE_API_KEY environment variable not set.")
        return

    print("[*] Reading GEMINI.md standards...")
    standards = Path("GEMINI.md").read_text()
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        system_instruction=f"You are a research assistant. Follow these standards strictly:\n{standards}"
    )

    print("[*] Scanning git commits for changes in raw/...")
    files_to_process = get_changed_files()

    if not files_to_process:
        print("[*] No changes detected in raw/.")
        return

    wiki_context = get_wiki_context()
    for file_path in files_to_process:
        print(f"[*] Processing {file_path}...")
        process_file(file_path, model, standards, wiki_context)
    
    # Example command to run a 'lint' audit after sync
    # subprocess.run(["python3", "scripts/audit_wiki.py"])
    
    print("[*] Update complete. wiki/INDEX.md refreshed.")
    update_index()
    print("[*] Sync complete.")

if __name__ == "__main__":
    try:
        sync_wiki()
    except Exception as e:
        print(f"[!] Sync failed: {e}")