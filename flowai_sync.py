import subprocess

print("🔄 Syncing notes from Notion...")
subprocess.run(["python", "sync_from_notion.py"])

print("\n⬆️ Uploading notes to GitHub...")
subprocess.run(["python", "sync_to_github.py"])

print("\n✅ All done!")
