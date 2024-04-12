from pymongo import MongoClient
import requests
import time
from threading import Thread

client = MongoClient('xxx')
db = client['corcelio']
collection = db['vision-workers']

def check_for_changes(last_model=None):
    while True:
        document = collection.find_one({"_id": "doc_id"})  # Replace 'doc_id' with actual document ID
        if document:
            current_model = document.get('best_finetune_model')
            if current_model != last_model:
                print(f"New best_finetune_model detected: {current_model}")
                response = requests.post('http://0.0.0.0:6919/load_model', json={"model": current_model})
                print(f"Local API response: {response.status_code}, {response.text}")
                last_model = current_model
        else:
            print("No such document found!")
        time.sleep(10)  # Wait for 10 seconds before the next check

if __name__ == "__main__":
    check_for_changes_thread = Thread(target=check_for_changes)
    check_for_changes_thread.start()
