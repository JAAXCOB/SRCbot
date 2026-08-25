import os

BASE_DIR = "/opt/srcbot"
reg_file = os.path.join(BASE_DIR, "registrations.txt")
names_file = os.path.join(BASE_DIR, "names.txt")

if not os.path.exists(reg_file):
    print("registrations.txt not found — nothing to migrate.")
    exit()

existing = {}
if os.path.exists(names_file):
    for line in open(names_file).readlines():
        parts = line.strip().split("|", 1)
        if len(parts) == 2:
            existing[parts[0]] = parts[1]

added = 0
for line in open(reg_file).readlines():
    parts = line.strip().split("|")
    if len(parts) >= 2:
        uid, name = parts[0], parts[1]
        if uid not in existing:
            existing[uid] = name
            added += 1

with open(names_file, "w") as f:
    for uid, name in existing.items():
        f.write(f"{uid}|{name}\n")

print(f"Done. {added} new names added. Total in names.txt: {len(existing)}.")
