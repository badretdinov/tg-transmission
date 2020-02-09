#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging, json, argparse
from telegram import KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
from torrentservice import *
from filesservice import *
from addservice import *
from systemservice import *
from transmission_rpc import Client

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def start(update, context):
	keyboard = [[KeyboardButton("Torrents")],
				[KeyboardButton("Files")],
				[KeyboardButton("System commands")]]
	reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard = True)
	update.message.reply_text('Hello!', reply_markup=reply_markup)

def cancel(update, context):
	context.user_data.clear()
	query = update.callback_query
	context.bot.edit_message_text(
		chat_id=query.message.chat_id,
		message_id=query.message.message_id,
		text='Canceled'
	)
	return ConversationHandler.END

def error(update, context):
	logger.warning('Update "%s" caused error "%s"', update, context.error)

def main(token, root_dir, rpc, whitelist, proxy):
	if proxy:
		request_kwargs={
		   'proxy_url': 'socks5://{}:{}'.format(proxy['address'], proxy['port']),
		   'urllib3_proxy_kwargs': {
				'username': proxy['username'],
				'password': proxy['password'],
			}
		}
	else:
		request_kwargs = None

	t_service = TorrentService(rpc['address'], rpc['port'], rpc['username'], rpc['password'])
	f_service = FilesService(root_dir)
	a_service = AddService(f_service, t_service)
	s_service = SystemService()

	updater = Updater(token, use_context=True, request_kwargs=request_kwargs)
	dp = updater.dispatcher

	fallbacks = [CallbackQueryHandler(cancel, pattern='^cancel$'),
				 MessageHandler(Filters.regex(r'^Torrents$') & Filters.chat(username=whitelist), t_service.torrent_list),
				 MessageHandler(Filters.regex(r'^Files$') & Filters.chat(username=whitelist), f_service.file_list),
				 MessageHandler(Filters.document & Filters.chat(username=whitelist), a_service.add_torrent_file),
				 MessageHandler(Filters.regex(r'^magnet:\?') & Filters.chat(username=whitelist), a_service.add_torrent_magnet),
				 MessageHandler(Filters.regex(r'^System commands$') & Filters.chat(username=whitelist), s_service.commands_list)]

	torrents_handler = ConversationHandler(
		entry_points=[MessageHandler(Filters.regex(r'^Torrents$') & Filters.chat(username=whitelist), t_service.torrent_list)],
		states={
			TORRENTLIST: [CallbackQueryHandler(t_service.torrent_info, pattern='^t_info_\d+$')],

			TORRENTINFO: [CallbackQueryHandler(t_service.move_top, pattern='^t_top_\d+$'),
						  CallbackQueryHandler(t_service.move_up, pattern='^t_up_\d+$'),
						  CallbackQueryHandler(t_service.move_down, pattern='^t_down_\d+$'),
						  CallbackQueryHandler(t_service.move_bottom, pattern='^t_bottom_\d+$'),
						  CallbackQueryHandler(t_service.resume_torrent, pattern='^t_resume_\d+$'),
						  CallbackQueryHandler(t_service.resume_torrent_now, pattern='^t_resume_now_\d+$'),
						  CallbackQueryHandler(t_service.stop_torrent, pattern='^t_stop_\d+$'),
						  CallbackQueryHandler(t_service.verify_torrent, pattern='^t_verify_(\d+?)$'),
						  CallbackQueryHandler(t_service.remove_torrent_confirm, pattern='^t_remove_confirm_\d+$')],

			REMOVETORRENT: [CallbackQueryHandler(t_service.remove_torrent, pattern='^t_remove_\d+$'),
							CallbackQueryHandler(t_service.remove_torrent_complete, pattern='^t_remove_complete_\d+$')]
		},
		fallbacks=fallbacks
	)
	files_handler = ConversationHandler(
		entry_points=[MessageHandler(Filters.regex(r'^Files$') & Filters.chat(username=whitelist), f_service.file_list)],
		states={
			FILESLIST: [CallbackQueryHandler(f_service.file_list, pattern='^t_file_info_[0-9]*$'),
						CallbackQueryHandler(f_service.file_list_back, pattern='^t_file_info_back$'),
						CallbackQueryHandler(f_service.remove_file_confirm, pattern='^t_file_delete_confirm$')],

			REMOVEFILECONFIRM: [CallbackQueryHandler(f_service.remove_file, pattern='^t_file_delete$')]
		},
		fallbacks=fallbacks
	)
	add_handler = ConversationHandler(
		entry_points=[MessageHandler(Filters.document & Filters.chat(username=whitelist), a_service.add_torrent_file),
						MessageHandler(Filters.regex(r'^magnet:\?') & Filters.chat(username=whitelist), a_service.add_torrent_magnet)],
		states={
			ADDFOLDERLIST: [CallbackQueryHandler(a_service.choose_dir_for_torrent, pattern='^a_folder_info_[0-9]*$'),
							CallbackQueryHandler(a_service.choose_dir_for_torrent_back, pattern='^a_folder_info_back$'),
							CallbackQueryHandler(a_service.choose_dir_for_torrent_finish, pattern='^a_folder_info_finish$')]
		},
		fallbacks=fallbacks
	)
	commands_handler = ConversationHandler(
		entry_points=[MessageHandler(Filters.regex(r'^System commands$') & Filters.chat(username=whitelist), s_service.commands_list)],
		states={
			SYSTEMCOMMANDS: [CallbackQueryHandler(s_service.restart_minidlna, pattern='^restart_minidlna$'),
							CallbackQueryHandler(s_service.reboot, pattern='^reboot$'),
							CallbackQueryHandler(s_service.poweroff, pattern='^poweroff$')]
		},
		fallbacks=fallbacks
	)

	dp.add_handler(torrents_handler)
	dp.add_handler(files_handler)
	dp.add_handler(add_handler)
	dp.add_handler(commands_handler)
	dp.add_handler(CommandHandler('start', start, Filters.chat(username=whitelist)))
	dp.add_error_handler(error)

	updater.start_polling()
	updater.idle()

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-config', help='path to the config file', type=argparse.FileType('r'))
	args = parser.parse_args()
	config_file = vars(args)['config']
	config_str = config_file.read()
	config = json.loads(config_str)
	token = config['token']
	users = config['user_whitelist']
	root_dir = config['root_dir']
	rpc = config['rpc']
	try:
		proxy = config['proxy']
	except:
		proxy = None
	main(token, root_dir, rpc, users, proxy)