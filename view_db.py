import sqlite3
import os
import datetime

db_path = os.path.join("database", "memory.db")
md_path = "database_contents.md"

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

output = []
output.append("# 📊 AgentForge Database Viewer")
output.append(f"*Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")

# Helper to escape markdown pipe characters inside cell text
def escape_md(text):
    if text is None:
        return ""
    # Replace pipes and escape brackets
    return str(text).replace("|", "\\|").replace("\n", "<br>")

# 1. Agents
output.append("## 🤖 Agents (`agents` table)")
cursor.execute("SELECT * FROM agents")
agents = cursor.fetchall()
if not agents:
    output.append("*No agents found in database.*\n")
else:
    output.append("| Agent ID | Name | Type | Created At | Last Active | Active |")
    output.append("| --- | --- | --- | --- | --- | --- |")
    for row in agents:
        is_active = "✅ Yes" if row["is_active"] else "❌ No"
        output.append(f"| `{row['agent_id']}` | **{row['agent_name']}** | `{row['agent_type']}` | {row['created_at']} | {row['last_active']} | {is_active} |")
    output.append("")

# 2. Conversations
output.append("## 💬 Conversations (`conversations` table)")
cursor.execute("SELECT * FROM conversations ORDER BY id DESC")
convs = cursor.fetchall()
if not convs:
    output.append("*No conversations found in database.*\n")
else:
    output.append("| ID | Agent ID | Role | Content | Timestamp |")
    output.append("| --- | --- | --- | --- | --- |")
    for row in convs:
        content = escape_md(row['content'])
        if len(content) > 300:
            content = content[:300] + "..."
        output.append(f"| {row['id']} | `{row['agent_id']}` | **{row['role']}** | {content} | {row['timestamp']} |")
    output.append("")

# 3. Action Logs
output.append("## ⚙️ Action Logs (`action_logs` table)")
cursor.execute("SELECT * FROM action_logs ORDER BY id DESC")
logs = cursor.fetchall()
if not logs:
    output.append("*No action logs found in database.*\n")
else:
    output.append("| ID | Agent ID | Action Type | Result | Timestamp |")
    output.append("| --- | --- | --- | --- | --- |")
    for row in logs:
        result = escape_md(row['result'])
        if len(result) > 150:
            result = result[:150] + "..."
        output.append(f"| {row['id']} | `{row['agent_id']}` | `{row['action_type']}` | {result} | {row['timestamp']} |")
    output.append("")

# 4. Knowledge Sources
output.append("## 📚 Knowledge Sources (`knowledge_sources` table)")
cursor.execute("SELECT * FROM knowledge_sources")
sources = cursor.fetchall()
if not sources:
    output.append("*No knowledge sources found in database.*\n")
else:
    output.append("| ID | Agent ID | Source Name | Source Type | Chunks |")
    output.append("| --- | --- | --- | --- | --- |")
    for row in sources:
        output.append(f"| {row['id']} | `{row['agent_id']}` | **{row['source_name']}** | `{row['source_type']}` | {row['chunk_count']} |")
    output.append("")

conn.close()

with open(md_path, "w", encoding="utf-8") as f:
    f.write("\n".join(output))

print(f"Database exported successfully to {md_path}!")
