import requests
import time
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from pymongo.server_api import ServerApi
import os

class DatabaseClient:
    def __init__(self, uri):
        self.db = self.connect_mongodb(uri)

    def connect_mongodb(self, uri):
        try:
            self.client = MongoClient(uri, server_api=ServerApi('1'))
            self.client.admin.command('ping')
            print(f"[{datetime.now()}] Successfully connected to MongoDB.")
            return self.client['llm_server_miners']
        except ConnectionFailure as e:
            print(f"[{datetime.now()}] MongoDB connection failed: {e}")
            exit(1) 

    def get_latest_model_payload(self):
        doc = self.db.best_finetune_model.find_one({'id': 'best_finetune_model'})
        if doc:
            return {key: value for key, value in doc.items() if key != '_id'}
        return None

def load_new_model(payload):
    url = "http://0.0.0.0:6919/load_model"
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code, response.text

def main():
    uri = "mongodb+srv://miner_llm:ByjJThQcxGL7QOdT@cluster0.qnwgewf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    db_client = DatabaseClient(uri)
    last_loaded_model_payload = db_client.get_latest_model_payload()

    model_auto_updates_sleep = int(os.environ.get('LLM_MODEL_AUTOUP_SLEEP', '60'))

    while True:
        try:
            current_payload = db_client.get_latest_model_payload()
            print(f"[{datetime.now()}]Current model : ", current_payload)
            if current_payload != last_loaded_model_payload:
                print(f"[{datetime.now()}] New model detected: {current_payload}. Loading...")
                status_code, response_text = load_new_model(current_payload)
                print(f"Response from server: {status_code}, {response_text}")
                last_loaded_model_payload = current_payload
            else:
                print(f"[{datetime.now()}] No new model update.")
        except Exception as e:
            print(f"[{datetime.now()}] Error: {e}")

        time.sleep(model_auto_updates_sleep)

if __name__ == "__main__":
    main()