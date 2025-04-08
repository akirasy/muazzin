import requests
import json
import time

class TelegramBot:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{self.token}/"
        self._last_update_id = None

    def _make_request(self, method, endpoint, data=None, files=None):
        url = self.base_url + endpoint
        headers = {"Content-Type": "application/json"}
        try:
            if method == "get":
                response = requests.get(url, params=data)
            elif method == "post":
                response = requests.post(url, headers=headers, json=data, files=files)
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {endpoint}: {e}")
            return None

    def get_me(self):
        return self._make_request("get", "getMe")

    def send_message(self, chat_id, text, parse_mode=None, reply_markup=None):
        data = {"chat_id": chat_id, "text": text}
        if parse_mode:
            data["parse_mode"] = parse_mode
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._make_request("post", "sendMessage", data=data)

    def send_photo(self, chat_id, photo_path, caption=None, reply_markup=None):
        files = {"photo": open(photo_path, "rb")}
        data = {"chat_id": chat_id}
        if caption:
            data["caption"] = caption
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._make_request("post", "sendPhoto", data=data, files=files)

    def get_updates(self, offset=None, timeout=30):
        params = {"timeout": timeout}
        if offset:
            params["offset"] = offset
        return self._make_request("get", "getUpdates", data=params)

if __name__ == "__main__":
    BOT_TOKEN = "YOUR_BOT_TOKEN"  # Replace with your actual bot token
    bot = TelegramBot(BOT_TOKEN)

    # Get bot information
    bot_info = bot.get_me()
    if bot_info and bot_info["ok"]:
        print("Bot information:", bot_info["result"])
    elif bot_info:
        print("Error getting bot info:", bot_info["description"])
    else:
        print("Failed to get bot info.")

    # Example of sending a message
    # bot.send_message("YOUR_CHAT_ID", "Hello from the TelegramBot class!")

    # Example of sending a photo
    # bot.send_photo("YOUR_CHAT_ID", "/path/to/your/image.jpg", caption="My awesome photo!")

