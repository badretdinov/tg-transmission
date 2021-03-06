from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
import os, shutil

SYSTEMCOMMANDS = range(1)

class SystemService:
	def __init__(self, default_url):
		self.url = default_url

	def commands_list(self, update, context):
		keyboard = [[InlineKeyboardButton('⎚ Restart MiniDLNA', callback_data='restart_minidlna')],
					[InlineKeyboardButton('■ Reboot', callback_data='reboot')],
					[InlineKeyboardButton('◻︎ Poweroff', callback_data='poweroff')],
					[InlineKeyboardButton('❖ Check free space', callback_data='free_space')],
					[InlineKeyboardButton('✕ Cancel', callback_data='cancel')]]
		reply_markup = InlineKeyboardMarkup(keyboard)
		update.message.reply_text(text='Commands', reply_markup=reply_markup)
		return SYSTEMCOMMANDS

	def restart_minidlna(self, update, context):
		os.system('sudo minidlnad -R && sudo service minidlna restart')
		query = update.callback_query
		context.bot.edit_message_text(
			chat_id=query.message.chat_id,
			message_id=query.message.message_id,
			text='MiniDLNA has been restarted'
		)
		return ConversationHandler.END

	def reboot(self, update, context):
		query = update.callback_query
		context.bot.edit_message_text(
			chat_id=query.message.chat_id,
			message_id=query.message.message_id,
			text='Reboot has been executed'
		)
		os.system('sudo reboot')
		return ConversationHandler.END

	def poweroff(self, update, context):
		query = update.callback_query
		context.bot.edit_message_text(
			chat_id=query.message.chat_id,
			message_id=query.message.message_id,
			text='Poweroff has been executed'
		)
		os.system('sudo poweroff')
		return ConversationHandler.END

	def get_free_space(self, update, context):
		free = shutil.disk_usage(self.url).free / (2**30)
		query = update.callback_query
		context.bot.edit_message_text(
			chat_id=query.message.chat_id,
			message_id=query.message.message_id,
			text='{0:.2f} GB Free'.format(free)
		)
		return ConversationHandler.END