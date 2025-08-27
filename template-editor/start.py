#!/usr/bin/env python3
"""
Startup script for the template editor server.
"""

import uvicorn
from server import app

if __name__ == "__main__":
    print("Starting Template Editor Server...")
    print("Navigate to: http://localhost:8001/issues/issue_detail.html/normal_issue.html")
    uvicorn.run("server:app", host="0.0.0.0", port=8001, reload=True)