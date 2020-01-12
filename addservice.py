from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
from io import BytesIO
import os, re, base64

ADDFOLDERLIST = range(1)

class AddService:
	def __init__(self, f, t):
		self.f_service = f
		self.t_service = t

	def add_torrent_magnet(self, update, context):
		context.user_data.clear()
		context.user_data['TorrentMagnet'] = update.message.text
		return self.choose_dir_for_torrent(update, context)

	def add_torrent_file(self, update, context):
		context.user_data.clear()
		doc = update.message.document
		context.user_data['TorrentDocument'] = doc
		return self.choose_dir_for_torrent(update, context)

	def choose_dir_for_torrent_back(self, update, context):
		try:
			path = context.user_data['Path']
			if path != self.f_service.url:
				path = os.path.dirname(path)
				context.user_data['Path'] = path
		except:
			path = self.f_service.url
		return self.folder_content(update, context, path)

	def choose_dir_for_torrent(self, update, context):
		if not update.callback_query:
			prev_index = ''
		else:
			prev_index = re.search('^a_folder_info_([0-9]*?)$', update.callback_query.data).group(1)
			
		try:
			path = context.user_data['Path']
		except:
			path = self.f_service.url
		if prev_index:
			path = self.f_service.path_by_index(path, prev_index, context)
		return self.folder_content(update, context, path)

	def folder_content(self, update, context, path):
		keyboard = []
		folders = self.f_service.listdir(path, False)
		for i, name in enumerate(folders):
			file_path = os.path.join(path, name)
			title = '📁 {}'.format(name)
			keyboard.append([InlineKeyboardButton(title, callback_data='a_folder_info_{}'.format(i))])
		keyboard.append([InlineKeyboardButton('✕ Cancel', callback_data='cancel')])
		select = InlineKeyboardButton('◎ Select', callback_data='a_folder_info_finish')

		if update.callback_query:
			if path != self.f_service.url:
				upper_row = [InlineKeyboardButton('← Back', callback_data='a_folder_info_back'), select]
				keyboard.insert(0, upper_row)
			else:
				keyboard.insert(0, [select])

			reply_markup = InlineKeyboardMarkup(keyboard)
			context.bot.edit_message_text(
				chat_id=update.callback_query.message.chat_id,
				message_id=update.callback_query.message.message_id,
				reply_markup=reply_markup,
				text=path
			)
		else:
			keyboard.insert(0, [select])
			reply_markup = InlineKeyboardMarkup(keyboard)
			update.message.reply_text(text=path, reply_markup=reply_markup)
		return ADDFOLDERLIST

	def choose_dir_for_torrent_finish(self, update, context):
		try:
			path = context.user_data['Path']
		except:
			path = self.f_service.url

		try:
			torrent_url = context.user_data['TorrentMagnet']
		except:
			try:
				torrent_url = base64.b64encode(context.user_data['TorrentDocument'].get_file().download_as_bytearray()).decode('ascii')
			except:
				context.bot.edit_message_text(
					chat_id=update.callback_query.message.chat_id,
					message_id=update.callback_query.message.message_id,
					text='Something went wrong'
				)
				return ConversationHandler.END
		
		t_name = self.t_service.add_torrent(torrent_url, path)
		context.bot.edit_message_text(
			chat_id=update.callback_query.message.chat_id,
			message_id=update.callback_query.message.message_id,
			text='{} added'.format(t_name)
		)
		context.user_data.clear()
		return ConversationHandler.END