from transmission_rpc import Client
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
import re

TORRENTLIST, TORRENTINFO, REMOVETORRENT = range(3)

class TorrentService:
	def __init__(self, address, port, username, password): 
		self.client = Client(address=address, port=port, username=username, password=password)

	def torrent_icon(self, status):
		if status == 'stopped':
			return '⏹'
		else:
			return '▶️'

	def torrent_description(self, torrent):
		return '{} {} {:01.0f}%, {}'.format(self.torrent_icon(torrent.status), torrent.status, torrent.progress, torrent.name)

	def add_torrent(self, url, path):
		tor = self.client.add_torrent(url, download_dir=path)
		return tor.name

	def torrent_list(self, update, context):
		torrents = self.client.get_torrents()
		torrents = sorted(torrents, key = lambda i: i.queue_position) 
		keyboard = []
		for torrent in torrents:
			tname = self.torrent_description(torrent)
			keyboard.append([InlineKeyboardButton(tname, callback_data='t_info_{}'.format(torrent.id))])
		keyboard.append([InlineKeyboardButton('✕ Cancel', callback_data='cancel')])
		reply_markup = InlineKeyboardMarkup(keyboard)
		update.message.reply_text(text='Torrents', reply_markup=reply_markup)
		return TORRENTLIST

	def torrent_info(self, update, context):
		query = update.callback_query
		tid = re.search('^t_info_(\d+?)$', query.data).group(1)
		tor = self.client.get_torrent(tid)
		stop_resume = []
		if tor.status == 'stopped':
			stop_resume = [InlineKeyboardButton('▷ Resume', callback_data='t_resume_{}'.format(tid)), InlineKeyboardButton('▶︎ Resume now', callback_data='t_resume_now_{}'.format(tid))]
		elif tor.status == 'download pending':
			stop_resume = [InlineKeyboardButton('▶︎ Resume now', callback_data='t_resume_now_{}'.format(tid))]
		else:
			stop_resume = [InlineKeyboardButton('◼︎ Stop', callback_data='t_stop_{}'.format(tid))]
		keyboard = [
			[InlineKeyboardButton('▲ Top', callback_data='t_top_{}'.format(tid)), InlineKeyboardButton('△ Up', callback_data='t_up_{}'.format(tid)), InlineKeyboardButton('▽ Down', callback_data='t_down_{}'.format(tid)), InlineKeyboardButton('▼ Bottom', callback_data='t_bottom_{}'.format(tid))],
			stop_resume,
			[InlineKeyboardButton('◉ Verify', callback_data='t_verify_{}'.format(tid))],
			[InlineKeyboardButton('☒ Remove', callback_data='t_remove_{}'.format(tid))],
			[InlineKeyboardButton('✕ Cancel', callback_data='cancel')]
		]
		reply_markup = InlineKeyboardMarkup(keyboard)
		bot = context.bot
		bot.edit_message_text(
			chat_id=query.message.chat_id,
			message_id=query.message.message_id,
			reply_markup=reply_markup,
			text=self.torrent_description(tor)
		)

		return TORRENTINFO

	def move_up(self, update, context):
		query = update.callback_query
		tid = re.search('^t_up_(\d+?)$', query.data).group(1)
		self.client.queue_up(tid)
		tor = self.client.get_torrent(tid)
		context.bot.edit_message_text(
			chat_id=query.message.chat_id,
			message_id=query.message.message_id,
			text='{} moved up'.format(tor.name)
		)
		return ConversationHandler.END

	def move_down(self, update, context):
		query = update.callback_query
		tid = re.search('^t_down_(\d+?)$', query.data).group(1)
		self.client.queue_down(tid)
		tor = self.client.get_torrent(tid)
		context.bot.edit_message_text(
			chat_id=query.message.chat_id,
			message_id=query.message.message_id,
			text='{} moved down'.format(tor.name)
		)
		return ConversationHandler.END

	def move_top(self, update, context):
		query = update.callback_query
		tid = re.search('^t_top_(\d+?)$', query.data).group(1)
		self.client.queue_top(tid)
		tor = self.client.get_torrent(tid)
		context.bot.edit_message_text(
			chat_id=query.message.chat_id,
			message_id=query.message.message_id,
			text='{} moved to top'.format(tor.name)
		)
		return ConversationHandler.END

	def move_bottom(self, update, context):
		query = update.callback_query
		tid = re.search('^t_bottom_(\d+?)$', query.data).group(1)
		self.client.queue_bottom(tid)
		tor = self.client.get_torrent(tid)
		context.bot.edit_message_text(
			chat_id=query.message.chat_id,
			message_id=query.message.message_id,
			text='{} moved to bottom'.format(tor.name)
		)
		return ConversationHandler.END

	def stop_torrent(self, update, context):
		tid = re.search('^t_stop_(\d+?)$', update.callback_query.data).group(1)
		tor = self.client.get_torrent(tid)
		self.client.stop_torrent(tid)
		context.bot.edit_message_text(
			chat_id=update.callback_query.message.chat_id,
			message_id=update.callback_query.message.message_id,
			text='{} stopped'.format(tor.name)
		)
		return ConversationHandler.END

	def resume_torrent(self, update, context):
		tid = re.search('^t_resume_(\d+?)$', update.callback_query.data).group(1)
		tor = self.client.get_torrent(tid)
		self.client.start_torrent(tid)
		context.bot.edit_message_text(
			chat_id=update.callback_query.message.chat_id,
			message_id=update.callback_query.message.message_id,
			text='{} resumed'.format(tor.name)
		)
		return ConversationHandler.END

	def resume_torrent_now(self, update, context):
		tid = re.search('^t_resume_now_(\d+?)$', update.callback_query.data).group(1)
		tor = self.client.get_torrent(tid)
		self.client.start_torrent(tid, bypass_queue=True)
		context.bot.edit_message_text(
			chat_id=update.callback_query.message.chat_id,
			message_id=update.callback_query.message.message_id,
			text='{} resumed'.format(tor.name)
		)
		return ConversationHandler.END

	def verify_torrent(self, update, context):
		tid = re.search('^t_verify_(\d+?)$', update.callback_query.data).group(1)
		tor = self.client.get_torrent(tid)
		self.client.verify_torrent(tid)
		context.bot.edit_message_text(
			chat_id=update.callback_query.message.chat_id,
			message_id=update.callback_query.message.message_id,
			text='{} verification started'.format(tor.name)
		)
		return ConversationHandler.END

	def remove_torrent_confirm(self, update, context):
		tid = re.search('^t_remove_confirm_(\d+?)$', update.callback_query.data).group(1)
		tor = self.client.get_torrent(tid)
		keyboard = [
			[InlineKeyboardButton('☒ Remove torrent', callback_data='t_remove_only_{}'.format(tid))],
			[InlineKeyboardButton('⌧ Remove torrent and delete files', callback_data='t_remove_delete_files_{}'.format(tid))],
			[InlineKeyboardButton('✕ Cancel', callback_data='cancel')]
		]
		reply_markup = InlineKeyboardMarkup(keyboard)
		context.bot.edit_message_text(
			chat_id=update.callback_query.message.chat_id,
			message_id=update.callback_query.message.message_id,
			reply_markup=reply_markup,
			text='Remove {}?'.format(tor.name)
		)
		return REMOVETORRENT

	def remove_torrent(self, update, context):
		tid = re.search('^t_remove_(\d+?)$', update.callback_query.data).group(1)
		tor = self.client.get_torrent(tid)
		self.client.remove_torrent(tid)
		context.bot.edit_message_text(
			chat_id=update.callback_query.message.chat_id,
			message_id=update.callback_query.message.message_id,
			text='{} removed'.format(tor.name)
		)
		return ConversationHandler.END

	def remove_torrent_complete(self, update, context):
		tid = re.search('^t_remove_complete_(\d+?)$', update.callback_query.data).group(1)
		tor = self.client.get_torrent(tid)
		self.client.remove_torrent(tid, delete_data=True)
		context.bot.edit_message_text(
			chat_id=update.callback_query.message.chat_id,
			message_id=update.callback_query.message.message_id,
			text='{} removed'.format(tor.name)
		)
		return ConversationHandler.END