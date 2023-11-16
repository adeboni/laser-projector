"""Flask client test"""
import requests

r = requests.get("http://127.0.0.1:8100/laser_data/1024/")
raw_bytes = r.content
print(list(raw_bytes))
