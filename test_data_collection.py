import requests
import json

def test_data_collection():
    # First register a test user
    register_data = {
        'username': 'testuser',
        'password': 'testpass'
    }
    
    try:
        # Register user
        response = requests.post('http://localhost:5000/register', json=register_data)
        print(f"Register response: {response.status_code} - {response.text}")
        
        # Login user
        login_data = {
            'username': 'testuser',
            'password': 'testpass'
        }
        response = requests.post('http://localhost:5000/login', json=login_data)
        print(f"Login response: {response.status_code} - {response.text}")
        
        # Test data collection with minimal data
        minimal_data = {
            'username': 'testuser',
            'session_start': '2024-01-01T00:00:00',
            'session_end': '2024-01-01T01:00:00'
        }
        
        response = requests.post('http://localhost:5000/collect_data', json=minimal_data)
        print(f"Minimal data collection response: {response.status_code} - {response.text}")
        
        # Test data collection with some missing fields
        partial_data = {
            'username': 'testuser',
            'session_start': '2024-01-01T02:00:00',
            'session_end': '2024-01-01T03:00:00',
            'swipe_gesture_coordinates': '100.0,200.0|150.0,250.0',
            'swipe_gesture_pattern': 'right_0_100',
            'consent': False  # Test with consent false
        }
        
        response = requests.post('http://localhost:5000/collect_data', json=partial_data)
        print(f"Partial data collection response: {response.status_code} - {response.text}")
        
        # Test data collection with all fields
        full_data = {
            'username': 'testuser',
            'session_start': '2024-01-01T04:00:00',
            'session_end': '2024-01-01T05:00:00',
            'swipe_gesture_coordinates': '100.0,200.0|150.0,250.0|200.0,300.0',
            'swipe_gesture_pattern': 'down_1_150',
            'gyroscope_pattern': '0.123,0.456,0.789',
            'wifi_ssid': 'TestWiFi',
            'wifi_bssid': 'AA:BB:CC:DD:EE:FF',
            'location_lat': 12.3456,
            'location_lon': 78.9012,
            'login_time': '2024-01-01T04:00:00',
            'screen_brightness': 0.75,
            'consent': True
        }
        
        response = requests.post('http://localhost:5000/collect_data', json=full_data)
        print(f"Full data collection response: {response.status_code} - {response.text}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend. Make sure it's running on http://localhost:5000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Testing data collection with various scenarios...")
    test_data_collection() 