# import os
# import time
# from dotenv import load_dotenv
# from notion_client import Client
# from slugify import slugify

# # Load environment variables
# load_dotenv()
# NOTION_TOKEN = os.getenv("NOTION_TOKEN")
# DATABASE_ID = os.getenv("DATABASE_ID")

# notion = Client(auth=NOTION_TOKEN)

# def fetch_all_notes(database_id):
#     results = []
#     has_more = True
#     next_cursor = None

#     while has_more:
#         response = notion.databases.query(
#             **{
#                 "database_id": database_id,
#                 "start_cursor": next_cursor,
#             }
#         )
#         results.extend(response['results'])
#         has_more = response.get("has_more", False)
#         next_cursor = response.get("next_cursor", None)

#     return results

# def fetch_page_blocks(page_id):
#     blocks = []
#     has_more = True
#     next_cursor = None

#     while has_more:
#         response = notion.blocks.children.list(block_id=page_id, start_cursor=next_cursor)
#         blocks.extend(response['results'])
#         has_more = response.get("has_more", False)
#         next_cursor = response.get("next_cursor", None)

#     return blocks

# def extract_text_from_block(block):
#     block_type = block.get("type")
#     if block_type in block and "text" in block[block_type]:
#         texts = block[block_type]["text"]
#         return "".join([t["plain_text"] for t in texts])
#     return ""

# def save_note_to_txt(note, folder="synced_notes"):
#     os.makedirs(folder, exist_ok=True)
    
#     title = note['properties']['Name']['title'][0]['plain_text']
#     slug = slugify(title)
#     category = note['properties'].get("Category", {}).get("select", {}).get("name", "Uncategorized")
    
#     blocks = fetch_page_blocks(note["id"])
#     content_lines = []
#     print(f"🔎 Blocks for page '{title}':")
#     for b in blocks:
#         print(b)

#     for block in blocks:
#         text = extract_text_from_block(block)
#         if text.strip():
#             content_lines.append(text.strip())

#     filename = os.path.join(folder, f"{slug}.txt")
#     with open(filename, "w", encoding="utf-8") as f:
#         f.write(f"Title: {title}\n")
#         f.write(f"Category: {category}\n\n")
#         f.write("\n".join(content_lines))

#     print(f"✅ Synced: {filename}")

# def sync_to_txt():
#     print("🔄 Syncing notes from Notion...")
#     notes = fetch_all_notes(DATABASE_ID)
#     print("📥 Syncing notes from Notion...")
#     for note in notes:
#         save_note_to_txt(note)

# if __name__ == "__main__":
#     sync_to_txt()


import os
import re
import time
from dotenv import load_dotenv
from notion_client import Client

# Load environment variables from .env
load_dotenv()

notion = Client(auth=os.getenv("NOTION_TOKEN"))
database_id = os.getenv("NOTION_DATABASE_ID")

print("🔐 NOTION_TOKEN loaded:", os.getenv("NOTION_TOKEN") is not None)
print("📁 NOTION_DATABASE_ID loaded:", database_id)

OUTPUT_DIR = "synced_notes"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def slugify(text):
    return re.sub(r'\W+', '_', text).strip('_').lower()

def get_database_pages():
    results = []
    next_cursor = None
    while True:
        response = notion.databases.query(
            **{"database_id": database_id, "start_cursor": next_cursor} if next_cursor else {"database_id": database_id}
        )
        results.extend(response.get("results", []))
        next_cursor = response.get("next_cursor")
        if not next_cursor:
            break
    return results

def retrieve_block_text(block):
    block_type = block.get("type")
    block_data = block.get(block_type, {})
    if block_type == "paragraph":
        return "".join([t["plain_text"] for t in block_data.get("rich_text", [])])
    elif block_type == "heading_1":
        return "# " + "".join([t["plain_text"] for t in block_data.get("rich_text", [])])
    elif block_type == "heading_2":
        return "## " + "".join([t["plain_text"] for t in block_data.get("rich_text", [])])
    elif block_type == "heading_3":
        return "### " + "".join([t["plain_text"] for t in block_data.get("rich_text", [])])
    elif block_type == "bulleted_list_item":
        return "- " + "".join([t["plain_text"] for t in block_data.get("rich_text", [])])
    elif block_type == "numbered_list_item":
        return "1. " + "".join([t["plain_text"] for t in block_data.get("rich_text", [])])
    elif block_type == "to_do":
        checked = block_data.get("checked", False)
        checkbox = "[x]" if checked else "[ ]"
        return f"- {checkbox} " + "".join([t["plain_text"] for t in block_data.get("rich_text", [])])
    elif block_type == "toggle":
        return "<details><summary>" + "".join([t["plain_text"] for t in block_data.get("rich_text", [])]) + "</summary></details>"
    elif block_type == "quote":
        return "> " + "".join([t["plain_text"] for t in block_data.get("rich_text", [])])
    elif block_type == "code":
        lang = block_data.get("language", "")
        content = "".join([t["plain_text"] for t in block_data.get("rich_text", [])])
        return f"```{lang}\n{content}\n```"
    else:
        return ""

def fetch_block_children(block_id):
    content = []
    try:
        response = notion.blocks.children.list(block_id=block_id)
        for block in response.get("results", []):
            content.append(retrieve_block_text(block))
    except Exception as e:
        print(f"Error fetching children for block {block_id}: {e}")
    return "\n".join([line for line in content if line.strip()])

def sync_notes():
    print("🔄 Starting sync from Notion...")
    pages = get_database_pages()
    print(f"📝 Found {len(pages)} pages in database.")
    
    for page in pages:
        props = page.get("properties", {})
        title_property = next((v for v in props.values() if v["type"] == "title"), None)
        if not title_property:
            print("⚠️ Skipping page with no title.")
            continue
        title = "".join([t["plain_text"] for t in title_property["title"]])
        slug = slugify(title)
        content = fetch_block_children(page["id"])
        
        file_path = os.path.join(OUTPUT_DIR, f"{slug}.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            f.write(content)
        
        print(f"✅ Synced: {title} -> {file_path}")
        time.sleep(0.2)  # prevent hitting Notion rate limits
    
    print("🎉 Sync complete.")

if __name__ == "__main__":
    sync_notes()

