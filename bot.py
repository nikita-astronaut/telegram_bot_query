# -*- coding: utf-8 -*-
import time
import telebot
import config
import urllib2
import simplejson
from io import StringIO

k_initiated_state = 0
k_query_asked_state = 1
k_number_asked_state = 2

bot = telebot.TeleBot(config.token)

user_states = {}
user_queries = {}
user_numbers = {}

def get_four_google_images(request, index):
	fetcher = urllib2.build_opener()
	searchTerm = request.replace(' ', '%20')
	startIndex = index
	searchUrl = "http://ajax.googleapis.com/ajax/services/search/web?v=1.0&q=" + str(searchTerm) + "&start=" + str(startIndex)

	return simplejson.load(fetcher.open(searchUrl))

def modify_state(chat_id):
	user_states[chat_id] += 1
	if user_states[chat_id] > k_number_asked_state:
		user_states[chat_id] = k_query_asked_state

@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
    bot.send_message(message.chat.id, config.response_text_on_start)
    chat_id = message.chat.id

    if chat_id not in user_states:
        user_states[chat_id] = k_initiated_state
        user_queries[chat_id] = ''
        user_numbers[chat_id] = 0

def form_string(site):
	response_text = ''
	response_text += site['titleNoFormatting']
	response_text += '\n'
	response_text += site['url']
	response_text += '\n'
	response_text += site['content']

	return response_text

def is_ascii(s):
    return all(ord(c) < 128 for c in s)

def response(text, number, chat_id):
	number_of_full_calls = number / 4
	extra_sites = number % 4

	for call in range(number_of_full_calls):
		deserialized_output = get_four_google_images(text, call)
		sites_data = deserialized_output['responseData']['results']
		for site in range(4):
			bot.send_message(chat_id, form_string(sites_data[site]))

	if extra_sites > 0:
		deserialized_output = get_four_google_images(text, number_of_full_calls)
		sites_data = deserialized_output['responseData']['results']
		for site in range(extra_sites):
			bot.send_message(chat_id, form_string(sites_data[site]))

	user_queries[chat_id] = ''
	user_numbers[chat_id] = 0		


@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_msg(message):
	chat_id = message.chat.id

	if chat_id not in user_states:
		user_states[chat_id] = k_initiated_state
	
	modify_state(chat_id)

	if (user_states[chat_id] == k_query_asked_state):
		if (is_ascii(message.text)):
			user_queries[chat_id] = message.text
			bot.send_message(chat_id, config.ask_for_number)
		else:
			user_states[chat_id] -= 1
			bot.send_message(chat_id, config.not_english)
				
	if (user_states[chat_id] == k_number_asked_state):
		try:
			user_numbers[chat_id] = int(message.text)
			response(user_queries[chat_id], user_numbers[chat_id], chat_id)
			bot.send_message(chat_id, config.thank)
		except:
			bot.send_message(chat_id, config.angry)
			user_states[chat_id] = k_query_asked_state

if __name__ == '__main__':
    bot.polling(none_stop=True)
