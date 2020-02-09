from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
import os, re, itertools, shutil

FILESLIST, REMOVEFILECONFIRM = range(2)

class FilesService:
	def __init__(self, default_url):
		self.url = default_url

	def listdir(self, path, incl_files):
		folders = []
		files = []
		for name in os.listdir(path):
			if not name.startswith('.'):
				current_path = os.path.join(path, name)
				if os.path.isdir(current_path):
					folders.append(name)
				elif incl_files:
					files.append(name)

		return folders + files

	def path_by_index(self, path, prev_index, context):
		content = self.listdir(path, True)
		new_dir = next(itertools.islice(content, int(prev_index), None))
		path = os.path.join(path, new_dir)
		context.user_data['Path'] = path
		return path

	def file_list(self, update, context):
		if not update.callback_query:
			context.user_data.clear()
			prev_index = ''
		else:
			prev_index = re.search('^t_file_info_([0-9]*?)$', update.callback_query.data).group(1)

		try:
			path = context.user_data['Path']
		except:
			path = self.url
		
		if prev_index:
			path = self.path_by_index(path, prev_index, context)
		
		if os.path.isdir(path):
			return self.dir_info(update, context, path)
		else:
			return self.file_info(update, context, path)

	def file_list_back(self, update, context):
		try:
			path = context.user_data['Path']
			if path != self.url:
				path = os.path.dirname(path)
				context.user_data['Path'] = path
		except:
			path = self.url
		return self.dir_info(update, context, path)

	def dir_info(self, update, context, path):
		keyboard = []

		content = self.listdir(path, True)
		for i, name in enumerate(content):
			file_path = os.path.join(path, name)
			title = '📁 {}'.format(name) if os.path.isdir(file_path) else '🧾 {}'.format(name)
			d = 't_file_info_{}'.format(i)
			keyboard.append([InlineKeyboardButton(title, callback_data=d)])

		keyboard.append([InlineKeyboardButton('✕ Cancel', callback_data='cancel')])

		if update.callback_query:
			if path != self.url:
				upper_row = [InlineKeyboardButton('← Back', callback_data='t_file_info_back'), InlineKeyboardButton('☒ Delete', callback_data='t_file_delete_confirm')]
				keyboard.insert(0, upper_row)

			reply_markup = InlineKeyboardMarkup(keyboard)
			context.bot.edit_message_text(
				chat_id=update.callback_query.message.chat_id,
				message_id=update.callback_query.message.message_id,
				reply_markup=reply_markup,
				text=path
			)
		else:
			reply_markup = InlineKeyboardMarkup(keyboard)
			update.message.reply_text(text=path, reply_markup=reply_markup)
		return FILESLIST

	def file_info(self, update, context, path):
		keyboard = [
			[InlineKeyboardButton('← Back', callback_data='t_file_info_back'), InlineKeyboardButton('☒ Delete', callback_data='t_file_delete_confirm')]
		]
		keyboard.append([InlineKeyboardButton('✕ Cancel', callback_data='cancel')])
		reply_markup = InlineKeyboardMarkup(keyboard)
		context.bot.edit_message_text(
			chat_id=update.callback_query.message.chat_id,
			message_id=update.callback_query.message.message_id,
			reply_markup=reply_markup,
			text=path
		)
		return FILESLIST

	def remove_file_confirm(self, update, context):
		path = context.user_data['Path']
		keyboard = [
			[InlineKeyboardButton('☒ Delete', callback_data='t_file_delete')],
			[InlineKeyboardButton('✕ Cancel', callback_data='cancel')]
		]
		object_to_delete = os.path.basename(path)
		reply_markup = InlineKeyboardMarkup(keyboard)
		context.bot.edit_message_text(
			chat_id=update.callback_query.message.chat_id,
			message_id=update.callback_query.message.message_id,
			reply_markup=reply_markup,
			text='Are you sure you want to delete {}?'.format(object_to_delete)
		)
		return REMOVEFILECONFIRM

	def remove_file(self, update, context):
		path = context.user_data['Path']
		if os.path.isdir(path):
			shutil.rmtree(path)
		else:
			os.remove(path)
		removed_object = os.path.basename(path)
		context.bot.edit_message_text(
			chat_id=update.callback_query.message.chat_id,
			message_id=update.callback_query.message.message_id,
			text='{} has been deleted'.format(removed_object)
		)
		context.user_data.clear()
		return ConversationHandler.END