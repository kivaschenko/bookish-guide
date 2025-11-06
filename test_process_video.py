#!/usr/bin/env python3
"""
Test script to verify the new "Process Video" functionality.
"""

import requests
import json

# API base URL
BASE_URL = "http://localhost:47393/api"

# Test credentials
USERNAME = "testuser"
PASSWORD = "testpass123"


def test_process_video():
    """Test the new process video endpoint."""

    print("🧪 Testing Process Video functionality...")

    # Step 1: Login to get auth token
    print("\n1. Logging in...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": USERNAME, "password": PASSWORD},
        headers={"Content-Type": "application/json"},
    )

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")

    # Step 2: Get B-roll list to find a video to process
    print("\n2. Getting B-roll list...")
    broll_response = requests.get(f"{BASE_URL}/broll/", headers=headers)

    if broll_response.status_code != 200:
        print(f"❌ Failed to get B-roll list: {broll_response.status_code}")
        return False

    brolls = broll_response.json()["brolls"]

    # Find a video without AI analysis
    video_to_process = None
    for broll in brolls:
        if broll["mime_type"].startswith("video/") and not broll.get("ai_description"):
            video_to_process = broll
            break

    if not video_to_process:
        print("ℹ️  No unprocessed videos found. All videos already have AI analysis.")
        return True

    print(f"✅ Found unprocessed video: {video_to_process['filename']}")

    # Step 3: Test the process endpoint
    print(f"\n3. Processing video ID {video_to_process['id']}...")
    process_response = requests.post(
        f"{BASE_URL}/broll/{video_to_process['id']}/process", headers=headers
    )

    if process_response.status_code == 200:
        result = process_response.json()
        print("✅ Video processing successful!")
        print(f"   Message: {result.get('message')}")
        print(f"   Thumbnail generated: {result.get('thumbnail_generated')}")
        if result.get("ai_description"):
            print(f"   AI Description: {result['ai_description'][:100]}...")
        if result.get("ai_tags"):
            print(f"   AI Tags: {', '.join(result['ai_tags'][:5])}...")
    else:
        print(f"❌ Video processing failed: {process_response.status_code}")
        print(f"   Response: {process_response.text}")
        return False

    print("\n🎉 Process Video functionality is working!")
    return True


if __name__ == "__main__":
    try:
        test_process_video()
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
