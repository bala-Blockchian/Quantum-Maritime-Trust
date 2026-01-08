import requests
import time
import uuid

BASE_URL = "http://127.0.0.1:8000"
DELIVERY_ID = f"BUNKER-{uuid.uuid4().hex[:8].upper()}"

def test_bunker_lifecycle():
    print(f"Starting Simulation for Delivery: {DELIVERY_ID}")
    print("-" * 50)

    print("Sending Nomination...")
    nomination_data = {
        "delivery_id": DELIVERY_ID,
        "imo_number": "IMO9876543",
        "supplier_id": 5500,
        "expected_sulphur": 0.49
    }
    
    nom_res = requests.post(f"{BASE_URL}/nominate", json=nomination_data)
    
    if nom_res.status_code == 200:
        print(f"Nomination Success! Tx: {nom_res.json().get('tx_hash')}")
    else:
        print(f"Nomination Failed: {nom_res.text}")
        return

    time.sleep(2)

    print("\n2️Sending Finalization Data...")
    finalize_data = {
        "delivery_id": DELIVERY_ID,
        "actual_qty": 550,
        "density": 991,
        "sample_id": "SEAL-2026-ABC"
    }

    print(" CHECK TELEGRAM: Please reply 'SIGN' to your bot now...")
    
    fin_res = requests.post(f"{BASE_URL}/finalize", json=finalize_data, timeout=70)

    if fin_res.status_code == 200:
        print(f"Finalization Success!")
        print(f"Blockchain Tx: {fin_res.json().get('tx_hash')}")
        print("\nEnd-to-End Bunker Lifecycle Complete!")
    else:
        print(f"Finalization Failed: {fin_res.text}")

if __name__ == "__main__":
    test_bunker_lifecycle()