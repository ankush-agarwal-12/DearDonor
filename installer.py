import os
import re

project_dir = '.'  # Change this if needed
imports = set()

for subdir, _, files in os.walk(project_dir):
    for file in files:
        if file.endswith('.py'):
            with open(os.path.join(subdir, file), 'r', encoding='utf-8') as f:
                for line in f:
                    match = re.match(r'^\s*(import|from)\s+([a-zA-Z0-9_\.]+)', line)
                    if match:
                        pkg = match.group(2).split('.')[0]
                        if pkg not in ('__future__',):  # skip built-ins if needed
                            imports.add(pkg)

# Save to requirements.txt
with open('requirements.txt', 'w') as req_file:
    for lib in sorted(imports):
        req_file.write(f"{lib}\n")

print("Extracted libraries written to requirements.txt")
