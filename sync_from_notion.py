import os
import requests
from notion_client import Client
from dotenv import load_dotenv
from slugify import slugify

# === Load environment variables ===
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")

# === Initialize Notion client ===
notion = Client(auth=NOTION_TOKEN)

# === Configuration ===
OUTPUT_DIR = "synced-notes"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def fetch_notion_pages():
    response = notion.databases.query(database_id=DATABASE_ID)
    return response.get("results", [])

def parse_page(page):
    props = page["properties"]
    title = props["Name"]["title"][0]["plain_text"] if props["Name"]["title"] else "Untitled"
    content = props.get("Content", {}).get("rich_text", [])
    category = props.get("Category", {}).get("select", {}).get("name", "Uncategorized")

    full_content = "\n".join([block["plain_text"] for block in content])
    return title, category, full_content

def sync_to_markdown():
    notion_titles = []

    print("📥 Syncing notes from Notion...")
    pages = fetch_notion_pages()

    for page in pages:
        title, category, content = parse_page(page)
        slug = slugify(title)
        notion_titles.append(slug)

        file_path = os.path.join(OUTPUT_DIR, f"{slug}.md")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n")
            f.write(f"## Category: {category}\n\n")
            f.write(content)

        print(f"✅ Synced: {slug}.md")

    # === OPTIONAL DELETE LOGIC (commented out for safety) ===
    """
    for filename in os.listdir(OUTPUT_DIR):
        if filename.endswith(".md"):
            name_without_ext = os.path.splitext(filename)[0]
            if name_without_ext not in notion_titles:
                file_to_delete = os.path.join(OUTPUT_DIR, filename)
                os.remove(file_to_delete)
                print(f"🗑️ Deleted: {filename} (not found in Notion)")
    """

if __name__ == "__main__":
    sync_to_markdown()
