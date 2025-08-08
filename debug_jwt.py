#!/usr/bin/env python3
"""
Debug Supabase JWT to understand its structure
"""

import base64
import json

def decode_jwt_parts(token):
    """Decode JWT without verification to see structure"""
    parts = token.split('.')
    
    # Decode header
    header_data = base64.urlsafe_b64decode(parts[0] + '==')
    header = json.loads(header_data)
    
    # Decode payload
    payload_data = base64.urlsafe_b64decode(parts[1] + '==')
    payload = json.loads(payload_data)
    
    return header, payload

# Your Supabase JWT
token = "eyJhbGciOiJIUzI1NiIsImtpZCI6IkpKWkJHMUtHVFYwTkxXMmYiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3d3cXRrcXZjbW1jY2Vza3N0bnlmLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJiMWI0YzJlNy02NzAxLTQzZTItYWQ4Yy00NTM5MGE1YzMzNTEiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzU0NjMzODk5LCJpYXQiOjE3NTQ2MzAyOTksImVtYWlsIjoiYW5rdXNoMUBuZ28ub3JnIiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJlbWFpbCIsInByb3ZpZGVycyI6WyJlbWFpbCJdfSwidXNlcl9tZXRhZGF0YSI6eyJlbWFpbF92ZXJpZmllZCI6dHJ1ZX0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoicGFzc3dvcmQiLCJ0aW1lc3RhbXAiOjE3NTQ2MzAyOTl9XSwic2Vzc2lvbl9pZCI6ImRiNTczODMxLTI4NzctNDU4ZC04Yjc2LTQ5ZWU4ODcwY2ExMSIsImlzX2Fub255bW91cyI6ZmFsc2V9.b_WyG4D8uu7DSyWe6lCLRhckyIc8dJJga151-e2b_uo"

header, payload = decode_jwt_parts(token)

print("JWT Header:")
print(json.dumps(header, indent=2))
print("\nJWT Payload:")
print(json.dumps(payload, indent=2))
print(f"\nAlgorithm: {header.get('alg')}")
print(f"User ID (sub): {payload.get('sub')}")
print(f"Issuer: {payload.get('iss')}")
print(f"Audience: {payload.get('aud')}") 