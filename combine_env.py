import os

# File paths
files_in_order = [
    "env.example",        # lowest priority
    "env.development",
    "env.production",
    ".env"                # highest priority
]

merged = {}

# Step 1: Read each file in order
for filename in files_in_order:
    if os.path.exists(filename):
        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    merged[key.strip()] = value.strip()

# Step 2: Write combined .env
with open(".env", "w") as f:
    f.write("# Combined .env generated automatically\n\n")
    for key, value in merged.items():
        f.write(f"{key}={value}\n")

print("✅ .env file created successfully with merged values.")
