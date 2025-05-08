# Don't Remove Credit @CodeFlix_Bots, @rohit_1888
# Ask Doubt on telegram @CodeflixSupport
#
# Copyright (C) 2025 by Codeflix-Bots@Github, < https://github.com/Codeflix-Bots >.
#
# This file is part of < https://github.com/Codeflix-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/Codeflix-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#

import asyncio
import os
import random
import sys
import time
from datetime import datetime, timedelta
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode, ChatAction
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, ChatInviteLink, ChatPrivileges
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserNotParticipant
from bot import Bot
from config import *
from helper_func import *
from database.database import *

# Debug logging setup
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

#=====================================================================================##

@Bot.on_message(filters.command('stats') & filters.private & admin)
async def stats(bot: Bot, message: Message):
    logger.debug(f"Received /stats command from user {message.from_user.id}")
    now = datetime.now()
    delta = now - bot.uptime
    time = get_readable_time(delta.seconds)
    await message.reply(BOT_STATS_TEXT.format(uptime=time))

#=====================================================================================##

WAIT_MSG = "<b>Working....</b>"

#=====================================================================================##

@Bot.on_message(filters.command('users') & filters.private & admin)
async def get_users(client: Bot, message: Message):
    logger.debug(f"Received /users command from user {message.from_user.id}")
    msg = await client.send_message(chat_id=message.chat.id, text=WAIT_MSG)
    users = await db.full_userbase()
    await msg.edit(f"{len(users)} users are using this bot")

#=====================================================================================##

# AUTO-DELETE

@Bot.on_message(filters.private & filters.command('dlt_time') & admin)
async def set_delete_time(client: Bot, message: Message):
    logger.debug(f"Received /dlt_time command from user {message.from_user.id}")
    try:
        duration = int(message.command[1])
        await db.set_del_timer(duration)
        await message.reply(f"<b>Dᴇʟᴇᴛᴇ Tɪᴍᴇʀ ʜᴀs ʙᴇᴇɴ sᴇᴛ ᴛᴏ <blockquote>{duration} sᴇᴄᴏɴᴅs.</blockquote></b>")
    except (IndexError, ValueError):
        await message.reply("<b>Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ᴅᴜʀᴀᴛɪᴏɴ ɪɴ sᴇᴄᴏɴᴅs.</b> Usage: /dlt_time {duration}")

@Bot.on_message(filters.private & filters.command('check_dlt_time') & admin)
async def check_delete_time(client: Bot, message: Message):
    logger.debug(f"Received /check_dlt_time command from user {message.from_user.id}")
    duration = await db.get_del_timer()
    await message.reply(f"<b><blockquote>Cᴜʀʀᴇɴᴛ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇʀ ɪs sᴇᴛ ᴛᴏ {duration}sᴇᴄᴏɴᴅs.</blockquote></b>")

#=====================================================================================##

# NEW COMMANDS FROM PREVIOUS UPDATE

# Ping command to check bot's response time
@Bot.on_message(filters.command('ping') & filters.private)
async def ping_bot(client: Bot, message: Message):
    logger.debug(f"Received /ping command from user {message.from_user.id}")
    start_time = time.time()
    msg = await message.reply("<b>Pinging...</b>")
    end_time = time.time()
    latency = (end_time - start_time) * 1000  # Convert to milliseconds
    await msg.edit(f"<b>Pong!</b> Latency: <code>{latency:.2f} ms</code>")

# Uptime command to check how long the bot has been running
@Bot.on_message(filters.command('uptime') & filters.private)
async def uptime_bot(bot: Bot, message: Message):
    logger.debug(f"Received /uptime command from user {message.from_user.id}")
    now = datetime.now()
    delta = now - bot.uptime
    uptime_str = get_readable_time(delta.seconds)
    await message.reply(f"<b>Bot Uptime:</b> <code>{uptime_str}</code>")

# Logs command to fetch recent logs (admin-only)
@Bot.on_message(filters.command('logs') & filters.private & admin)
async def get_logs(client: Bot, message: Message):
    logger.debug(f"Received /logs command from user {message.from_user.id}")
    try:
        num_lines = 50  # Number of lines to fetch
        if len(message.command) > 1:
            try:
                num_lines = int(message.command[1])
                if num_lines <= 0:
                    raise ValueError
            except ValueError:
                await message.reply("<b>Please provide a valid number of lines.</b> Usage: /logs [number]")
                return

        # Read the last `num_lines` from the log file
        with open(LOG_FILE_NAME, 'r') as f:
            lines = f.readlines()
            last_lines = lines[-num_lines:] if len(lines) >= num_lines else lines
            log_content = "".join(last_lines)

        if not log_content.strip():
            await message.reply("<b>No logs found.</b>")
            return

        # Send logs as a message (if too long, split into multiple messages)
        if len(log_content) > 4096:  # Telegram message length limit
            for i in range(0, len(log_content), 4096):
                await message.reply(f"<code>{log_content[i:i+4096]}</code>")
        else:
            await message.reply(f"<b>Recent Logs:</b>\n<code>{log_content}</code>")
    except Exception as e:
        await message.reply(f"<b>Failed to fetch logs:</b> <code>{str(e)}</code>")

# Restart command (admin-only)
@Bot.on_message(filters.command('restart') & filters.private & admin)
async def restart_bot(client: Bot, message: Message):
    logger.debug(f"Received /restart command from user {message.from_user.id}")
    msg = await message.reply("<b>Restarting bot...</b>")
    try:
        # Notify the owner
        await client.send_message(OWNER_ID, "<b>Bot is restarting...</b>")
        # Log the restart
        LOGGER(__name__).info("Bot is restarting...")
        # Stop the bot gracefully
        await client.stop()
        # Restart the process (this works if the bot is run with a process manager like PM2 or Heroku)
        os.execl(sys.executable, sys.executable, *sys.argv)
    except Exception as e:
        await msg.edit(f"<b>Failed to restart:</b> <code>{str(e)}</code>")

#=====================================================================================##

# NEW COMMANDS FOR IMAGE AND SHORTENER MANAGEMENT

# Add Force Sub Picture
@Bot.on_message(filters.command('addforcesub') & filters.private)  # Removed admin filter for testing
async def add_force_sub_pic(client: Bot, message: Message):
    logger.debug(f"Received /addforcesub command from user {message.from_user.id}")
    if len(message.command) != 2:
        await message.reply("<b>Usage:</b> <code>/addforcesub [image_url]</code>")
        return
    url = message.command[1]
    # Basic URL validation
    if not url.startswith("http"):
        await message.reply("<b>Invalid URL. Please provide a valid image URL starting with http or https.</b>")
        return
    try:
        await db.add_force_pic(url)
        await message.reply(f"<b>Force Sub Picture added:</b> <code>{url}</code>")
    except Exception as e:
        await message.reply(f"<b>Failed to add Force Sub Picture:</b> <code>{str(e)}</code>")

# Add Start Sub Picture
@Bot.on_message(filters.command('addstartsub') & filters.private)  # Removed admin filter for testing
async def add_start_sub_pic(client: Bot, message: Message):
    logger.debug(f"Received /addstartsub command from user {message.from_user.id}")
    if len(message.command) != 2:
        await message.reply("<b>Usage:</b> <code>/addstartsub [image_url]</code>")
        return
    url = message.command[1]
    if not url.startswith("http"):
        await message.reply("<b>Invalid URL. Please provide a valid image URL starting with http or https.</b>")
        return
    try:
        await db.add_start_pic(url)
        await message.reply(f"<b>Start Sub Picture added:</b> <code>{url}</code>")
    except Exception as e:
        await message.reply(f"<b>Failed to add Start Sub Picture:</b> <code>{str(e)}</code>")

# Delete Force Sub Picture
@Bot.on_message(filters.command('delforcesub') & filters.private)  # Removed admin filter for testing
async def del_force_sub_pic(client: Bot, message: Message):
    logger.debug(f"Received /delforcesub command from user {message.from_user.id}")
    if len(message.command) != 2:
        await message.reply("<b>Usage:</b> <code>/delforcesub [image_url]</code>")
        return
    url = message.command[1]
    try:
        await db.del_force_pic(url)
        await message.reply(f"<b>Force Sub Picture deleted:</b> <code>{url}</code>")
    except Exception as e:
        await message.reply(f"<b>Failed to delete Force Sub Picture:</b> <code>{str(e)}</code>")

# Delete Start Sub Picture
@Bot.on_message(filters.command('delstartsub') & filters.private)  # Removed admin filter for testing
async def del_start_sub_pic(client: Bot, message: Message):
    logger.debug(f"Received /delstartsub command from user {message.from_user.id}")
    if len(message.command) != 2:
        await message.reply("<b>Usage:</b> <code>/delstartsub [image_url]</code>")
        return
    url = message.command[1]
    try:
        await db.del_start_pic(url)
        await message.reply(f"<b>Start Sub Picture deleted:</b> <code>{url}</code>")
    except Exception as e:
        await message.reply(f"<b>Failed to delete Start Sub Picture:</b> <code>{str(e)}</code>")

# Show All Force Sub Pictures
@Bot.on_message(filters.command('showforcesub') & filters.private)  # Removed admin filter for testing
async def show_force_sub_pics(client: Bot, message: Message):
    logger.debug(f"Received /showforcesub command from user {message.from_user.id}")
    try:
        pics = await db.get_all_force_pics()
        if not pics:
            await message.reply("<b>No Force Sub Pictures found.</b>")
            return
        pic_list = "\n".join([f"<code>{pic}</code>" for pic in pics])
        await message.reply(f"<b>Force Sub Pictures:</b>\n{pic_list}")
    except Exception as e:
        await message.reply(f"<b>Failed to fetch Force Sub Pictures:</b> <code>{str(e)}</code>")

# Show All Start Sub Pictures
@Bot.on_message(filters.command('showstartsub') & filters.private)  # Removed admin filter for testing
async def show_start_sub_pics(client: Bot, message: Message):
    logger.debug(f"Received /showstartsub command from user {message.from_user.id}")
    try:
        pics = await db.get_all_start_pics()
        if not pics:
            await message.reply("<b>No Start Sub Pictures found.</b>")
            return
        pic_list = "\n".join([f"<code>{pic}</code>" for pic in pics])
        await message.reply(f"<b>Start Sub Pictures:</b>\n{pic_list}")
    except Exception as e:
        await message.reply(f"<b>Failed to fetch Start Sub Pictures:</b> <code>{str(e)}</code>")

# Edit Shortener Settings
@Bot.on_message(filters.command('shortner') & filters.private)  # Removed admin filter for testing
async def edit_shortner(client: Bot, message: Message):
    logger.debug(f"Received /shortner command from user {message.from_user.id}")
    if len(message.command) != 3:
        await message.reply("<b>Usage:</b> <code>/shortner [SHORTLINK_API] [SHORTLINK_URL]</code>")
        return
    new_api = message.command[1]
    new_url = message.command[2]
    try:
        # Update environment variables (this change won't persist after a restart unless saved to the environment)
        os.environ['SHORTLINK_API'] = new_api
        os.environ['SHORTLINK_URL'] = new_url
        # Update the config variables
        globals()['SHORTLINK_API'] = new_api
        globals()['SHORTLINK_URL'] = new_url
        await message.reply(f"<b>Shortener settings updated:</b>\nSHORTLINK_API: <code>{new_api}</code>\nSHORTLINK_URL: <code>{new_url}</code>")
    except Exception as e:
        await message.reply(f"<b>Failed to update shortener settings:</b> <code>{str(e)}</code>")

# Edit Tutorial Video URL
@Bot.on_message(filters.command('edittutvid') & filters.private)  # Removed admin filter for testing
async def edit_tut_vid(client: Bot, message: Message):
    logger.debug(f"Received /edittutvid command from user {message.from_user.id}")
    if len(message.command) != 2:
        await message.reply("<b>Usage:</b> <code>/edittutvid [new_url]</code>")
        return
    new_url = message.command[1]
    if not new_url.startswith("http"):
        await message.reply("<b>Invalid URL. Please provide a valid URL starting with http or https.</b>")
        return
    try:
        os.environ['TUT_VID'] = new_url
        globals()['TUT_VID'] = new_url
        await message.reply(f"<b>Tutorial Video URL updated:</b> <code>{new_url}</code>")
    except Exception as e:
        await message.reply(f"<b>Failed to update Tutorial Video URL:</b> <code>{str(e)}</code>")

# Show Current Shortener Settings
@Bot.on_message(filters.command('showshortner') & filters.private)  # Removed admin filter for testing
async def show_shortner(client: Bot, message: Message):
    logger.debug(f"Received /showshortner command from user {message.from_user.id}")
    try:
        current_api = SHORTLINK_API
        current_url = SHORTLINK_URL
        await message.reply(f"<b>Current Shortener Settings:</b>\nSHORTLINK_API: <code>{current_api}</code>\nSHORTLINK_URL: <code>{current_url}</code>")
    except Exception as e:
        await message.reply(f"<b>Failed to fetch shortener settings:</b> <code>{str(e)}</code>")
