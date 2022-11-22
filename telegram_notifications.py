import requests
import json

def send_telegram_message(message: str, chat_id: str, api_key: str):
	responses = {}
	headers = {'Content-Type': 'application/json', 'Proxy-Authorization': 'Basic base64'}
	data_dict = {'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML', 'disable_notification': False}
	data = json.dumps(data_dict)
	url = f'https://api.telegram.org/bot{api_key}/sendMessage'
	response = requests.post(url, data=data, headers=headers, proxies=proxies, verify=False)
	return response
