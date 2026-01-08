import requests
token = ""
data = requests.get(f"https://api.telegram.org/bot{token}/getUpdates").json()

if data["result"]:
    chat_id = data["result"][-1]["message"]["chat"]["id"]
    print(f"Your CHIEF_CHAT_ID is: {chat_id}")
else:
    print("No messages found! Did you click START and send a message to the bot yet?")