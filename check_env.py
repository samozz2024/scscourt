#!/usr/bin/env python3
"""
Quick script to verify .env configuration
Run this on your server to debug the API key issue
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("Environment Variables Check")
print("=" * 80)

required_vars = {
    "CAPSOLVER_API_KEY": os.getenv("CAPSOLVER_API_KEY", ""),
    "SUPABASE_URL": os.getenv("SUPABASE_URL", ""),
    "SUPABASE_KEY": os.getenv("SUPABASE_KEY", ""),
    "PROXY_URL": os.getenv("PROXY_URL", ""),
}

for var_name, var_value in required_vars.items():
    if var_value:
        # Show first 10 and last 5 chars for security
        if len(var_value) > 15:
            masked = f"{var_value[:10]}...{var_value[-5:]}"
        else:
            masked = var_value[:5] + "..." if len(var_value) > 5 else "***"
        print(f"✓ {var_name}: {masked}")
    else:
        print(f"✗ {var_name}: NOT SET")

print("=" * 80)

# Test CapSolver API key format
capsolver_key = os.getenv("CAPSOLVER_API_KEY", "")
if capsolver_key:
    print(f"\nCapSolver API Key Length: {len(capsolver_key)} characters")
    if capsolver_key.startswith("CAP-"):
        print("✓ Key format looks correct (starts with CAP-)")
    else:
        print("⚠ Key format might be incorrect (should start with CAP-)")
else:
    print("\n✗ CAPSOLVER_API_KEY is not set!")

print("\n.env file location should be:")
print(f"  {os.path.abspath('.env')}")
print(f"\nFile exists: {os.path.exists('.env')}")
