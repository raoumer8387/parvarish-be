"""
Quick test script for the Lacking Analysis System.

Run this after the server is running to test all endpoints.
Make sure you have valid authentication tokens.
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Replace with actual tokens after login
PARENT_TOKEN = "your_parent_jwt_token_here"
CHILD_ID = 1  # Replace with actual child ID

headers = {
    "Authorization": f"Bearer {PARENT_TOKEN}",
    "Content-Type": "application/json"
}


def test_analyze_lacking():
    """Test 1: Get lacking analysis"""
    print("\n" + "="*60)
    print("TEST 1: Analyze Child Lacking")
    print("="*60)
    
    url = f"{BASE_URL}/parent/lacking/analyze/{CHILD_ID}?days=7"
    response = requests.get(url, headers=headers)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Child: {data['child_name']}")
        print(f"Total Games: {data['total_games_played']}")
        print(f"Lacking Areas Found: {len(data['lacking_areas'])}")
        
        for area in data['lacking_areas']:
            print(f"\n  - {area['label']}: {area['score']}/100 ({area['priority']} priority)")
        
        return data
    else:
        print(f"Error: {response.text}")
        return None


def test_get_notifications():
    """Test 2: Get notifications"""
    print("\n" + "="*60)
    print("TEST 2: Get Notifications")
    print("="*60)
    
    url = f"{BASE_URL}/parent/lacking/notifications"
    response = requests.get(url, headers=headers)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Total Notifications: {data['total_count']}")
        print(f"Unread: {data['unread_count']}")
        
        for notif in data['notifications'][:3]:  # Show first 3
            print(f"\n  📢 {notif['message']}")
            print(f"     Child: {notif['child_name']}")
            print(f"     Priority: {notif['priority']}")
        
        return data
    else:
        print(f"Error: {response.text}")
        return None


def test_get_guidance(lacking_area="presence_of_mind"):
    """Test 3: Get Islamic guidance"""
    print("\n" + "="*60)
    print(f"TEST 3: Get Islamic Guidance for '{lacking_area}'")
    print("="*60)
    
    url = f"{BASE_URL}/parent/lacking/guidance"
    payload = {
        "child_id": CHILD_ID,
        "lacking_area": lacking_area
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Child: {data['child_name']}")
        print(f"Area: {data['lacking_label']}")
        print(f"Score: {data['score']}/100")
        print(f"\nGuidance Preview:\n{data['guidance'][:300]}...")
        print(f"\nIslamic References Used: {data['islamic_references_used']}")
        
        return data
    else:
        print(f"Error: {response.text}")
        return None


def test_generate_tasks(lacking_area="presence_of_mind"):
    """Test 4: Generate Islamic tasks"""
    print("\n" + "="*60)
    print(f"TEST 4: Generate Tasks for '{lacking_area}'")
    print("="*60)
    
    url = f"{BASE_URL}/parent/lacking/generate-tasks"
    payload = {
        "child_id": CHILD_ID,
        "lacking_area": lacking_area,
        "num_tasks": 3
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Tasks Generated: {len(data['tasks'])}")
        print(f"Tasks Saved to DB: {data['tasks_saved']}")
        
        for i, task in enumerate(data['tasks'], 1):
            print(f"\n  Task {i}: {task['title']}")
            print(f"  Description: {task['description'][:100]}...")
            print(f"  Category: {task['category']} | Difficulty: {task['difficulty']} | XP: {task['xp_reward']}")
            if task.get('islamic_reference'):
                print(f"  Islamic Ref: {task['islamic_reference']}")
        
        return data
    else:
        print(f"Error: {response.text}")
        return None


def test_mark_notification_read(notification_id):
    """Test 5: Mark notification as read"""
    print("\n" + "="*60)
    print("TEST 5: Mark Notification as Read")
    print("="*60)
    
    url = f"{BASE_URL}/parent/lacking/notifications/mark-read"
    payload = {
        "notification_id": notification_id
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data['message']}")
        return data
    else:
        print(f"Error: {response.text}")
        return None


def run_full_test_suite():
    """Run all tests in sequence"""
    print("\n" + "="*70)
    print(" 🧪 LACKING ANALYSIS SYSTEM - FULL TEST SUITE")
    print("="*70)
    
    # Test 1: Analyze lacking
    analysis = test_analyze_lacking()
    
    # Test 2: Get notifications
    notifications = test_get_notifications()
    
    # If lacking areas found, test guidance and task generation
    if analysis and analysis['lacking_areas']:
        lacking_area = analysis['lacking_areas'][0]['area']
        
        # Test 3: Get guidance
        guidance = test_get_guidance(lacking_area)
        
        # Test 4: Generate tasks
        tasks = test_generate_tasks(lacking_area)
    
    # Test 5: Mark notification as read (if notifications exist)
    if notifications and notifications['notifications']:
        notif_id = notifications['notifications'][0]['id']
        test_mark_notification_read(notif_id)
    
    print("\n" + "="*70)
    print(" ✅ ALL TESTS COMPLETED")
    print("="*70)


if __name__ == "__main__":
    print("\n⚠️  IMPORTANT: Update PARENT_TOKEN and CHILD_ID variables before running!")
    print("You can get the token by logging in via POST /api/v1/auth/login\n")
    
    # Uncomment to run:
    # run_full_test_suite()
    
    # Or run individual tests:
    # test_analyze_lacking()
    # test_get_notifications()
    # test_get_guidance("presence_of_mind")
    # test_generate_tasks("mood_identification")
