import bcrypt

# Step 1: Choose a new secure password for Gerald
new_password = "Gerald!2025"  # <-- replace with Gerald's chosen strong password

# Step 2: Generate bcrypt hash
hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt(rounds=12))

# Step 3: Print the hash (copy this for your YAML)
print("New bcrypt hash for YAML:", hashed.decode())
print("Use this password to log in as Gerald:", new_password)

