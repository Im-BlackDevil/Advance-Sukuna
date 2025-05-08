
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
import secrets
from bot import Bot
from database.db_premium import collection, list_premium_users

#=====================================================================================##

@Bot.on_message(filters.command('stats') & admin)
async def stats(bot: Bot, message: Message):
    now = datetime.now()
    delta = now - bot.uptime
    time = get_readable_time(delta.seconds)
    await message.reply(BOT_STATS_TEXT.format(uptime=time))


#=====================================================================================##

WAIT_MSG = "<b>Working....</b>"

#=====================================================================================##


@Bot.on_message(filters.command('users') & filters.private & admin)
async def get_users(client: Bot, message: Message):
    msg = await client.send_message(chat_id=message.chat.id, text=WAIT_MSG)
    users = await db.full_userbase()
    await msg.edit(f"{len(users)} users are using this bot")

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

#=====================================================================================##

#AUTO-DELETE

@Bot.on_message(filters.private & filters.command('dlt_time') & admin)
async def set_delete_time(client: Bot, message: Message):
    try:
        duration = int(message.command[1])

        await db.set_del_timer(duration)

        await message.reply(f"<b>Dᴇʟᴇᴛᴇ Tɪᴍᴇʀ ʜᴀs ʙᴇᴇɴ sᴇᴛ ᴛᴏ <blockquote>{duration} sᴇᴄᴏɴᴅs.</blockquote></b>")

    except (IndexError, ValueError):
        await message.reply("<b>Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ᴅᴜʀᴀᴛɪᴏɴ ɪɴ sᴇᴄᴏɴᴅs.</b> Usage: /dlt_time {duration}")

@Bot.on_message(filters.private & filters.command('check_dlt_time') & admin)
async def check_delete_time(client: Bot, message: Message):
    duration = await db.get_del_timer()

    await message.reply(f"<b><blockquote>Cᴜʀʀᴇɴᴛ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇʀ ɪs sᴇᴛ ᴛᴏ {duration}sᴇᴄᴏɴᴅs.</blockquote></b>")

@Bot.on_message(filters.command('stats') & filters.private & admin)
async def stats_command(client: Client, message: Message):
    try:
        total_files = await collection.count_documents({})
        total_size = sum(doc.get("size", 0) async for doc in collection.find())
        total_users = len(await db.full_userbase())

        stats_message = (
            f"<b>📊 Bot Stats</b>\n\n"
            f"📂 Total Files: <code>{total_files}</code>\n"
            f"💾 Total Size: <code>{total_size / (1024 * 1024):.2f} MB</code>\n"
            f"👥 Total Users: <code>{total_users}</code>"
        )
        await message.reply_text(stats_message, parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"⚠️ Error fetching stats: <code>{str(e)}</code>")

@Bot.on_message(filters.command('users') & filters.private & admin)
async def users_command(client: Client, message: Message):
    try:
        total_users = len(await db.full_userbase())
        premium_users = len(await list_premium_users())
        uptime = int(time.time() - client.uptime)

        stats_message = (
            f"<b>📊 Bot Statistics</b>\n\n"
            f"👥 Total Users: <code>{total_users}</code>\n"
            f"🌟 Premium Users: <code>{premium_users}</code>\n"
            f"📅 Uptime: <code>{get_readable_time(uptime)}</code>"
        )
        await message.reply_text(stats_message, parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"⚠️ Error fetching user stats: <code>{str(e)}</code>")

@Bot.on_message(filters.command('addstartphoto') & filters.private & admin)
async def addstartphoto_command(client: Client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply_text("Reply to a photo with /addstartphoto.")
        return
    try:
        photo_id = message.reply_to_message.photo.file_id
        photo_key = secrets.token_hex(8)
        await db.add_start_photo(photo_key, photo_id, message.from_user.id)
        await message.reply_text(f"✅ Start photo added with key <code>{photo_key}</code>.")
    except Exception as e:
        await message.reply_text(f"⚠️ Error adding start photo: <code>{str(e)}</code>")

@Bot.on_message(filters.command('showstartpic') & filters.private & admin)
async def showstartpic_command(client: Client, message: Message):
    try:
        start_photos = await db.get_start_photos()
        if not start_photos:
            await message.reply_text("❌ No start photos found.")
            return
        photos_list = "\n".join(
            f"🖼️ Key: <code>{key}</code>, Added by: <code>{data['added_by']}</code>"
            for key, data in start_photos.items()
        )
        await message.reply_text(f"<b>📸 Start Photos</b>\n\n{photos_list}", parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"⚠️ Error fetching start photos: <code>{str(e)}</code>")

@Bot.on_message(filters.command('delstartphoto') & filters.private & admin)
async def delstartphoto_command(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("Usage: /delstartphoto <photo_key>")
        return
    photo_key = message.command[1]
    try:
        start_photos = await db.get_start_photos()
        if photo_key not in start_photos:
            await message.reply_text(f"❌ Photo key <code>{photo_key}</code> not found.")
            return
        await db.delete_start_photo(photo_key)
        await message.reply_text(f"✅ Start photo <code>{photo_key}</code> deleted.")
    except Exception as e:
        await message.reply_text(f"⚠️ Error deleting start photo: <code>{str(e)}</code>")

@Bot.on_message(filters.command('addforcephoto') & filters.private & admin)
async def addforcephoto_command(client: Client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply_text("Reply to a photo with /addforcephoto.")
        return
    try:
        photo_id = message.reply_to_message.photo.file_id
        photo_key = secrets.token_hex(8)
        await db.add_force_photo(photo_key, photo_id, message.from_user.id)
        await message.reply_text(f"✅ Force sub photo added with key <code>{photo_key}</code>.")
    except Exception as e:
        await message.reply_text(f"⚠️ Error adding force sub photo: <code>{str(e)}</code>")

@Bot.on_message(filters.command('showforcepic') & filters.private & admin)
async def showforcepic_command(client: Client, message: Message):
    try:
        force_photos = await db.get_force_photos()
        if not force_photos:
            await message.reply_text("❌ No force sub photos found.")
            return
        photos_list = "\n".join(
            f"🖼️ Key: <code>{key}</code>, Added by: <code>{data['added_by']}</code>"
            for key, data in force_photos.items()
        )
        await message.reply_text(f"<b>📸 Force Sub Photos</b>\n\n{photos_list}", parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"⚠️ Error fetching force sub photos: <code>{str(e)}</code>")

@Bot.on_message(filters.command('delforcephoto') & filters.private & admin)
async def delforcephoto_command(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("Usage: /delforcephoto <photo_key>")
        return
    photo_key = message.command[1]
    try:
        force_photos = await db.get_force_photos()
        if photo_key not in force_photos:
            await message.reply_text(f"❌ Photo key <code>{photo_key}</code> not found.")
            return
        await db.delete_force_photo(photo_key)
        await message.reply_text(f"✅ Force sub photo <code>{photo_key}</code> deleted.")
    except Exception as e:
        await message.reply_text(f"⚠️ Error deleting force sub photo: <code>{str(e)}</code>")

@Bot.on_message(filters.command('version') & filters.private)
async def version_command(client: Client, message: Message):
    version_message = (
        f"<b>🤖 {client.username} Version</b>\n\n"
        f"🌟 Version: <code>1.0.0</code>\n"
        f"📅 Last Updated: <code>2025-05-08</code>\n"
        f"👑 Owner: <a href='https://t.me/{OWNER}'>{OWNER}</a>"
    )
    await message.reply_text(version_message, parse_mode=ParseMode.HTML)

@Bot.on_message(filters.command('shortner') & filters.private & admin)
async def shortner_command(client: Client, message: Message):
    if len(message.command) != 3:
        await message.reply_text(
            "Usage: /shortner <SHORTLINK_API> <SHORTLINK_URL>\n\n"
            "Example:\n"
            "/shortner abc123 https://shortlink.example.com"
        )
        return
    try:
        shortlink_api = message.command[1]
        shortlink_url = message.command[2]
        await db.set_shortlink_config(shortlink_api, shortlink_url)
        await message.reply_text(
            f"✅ Shortlink config updated:\n"
            f"API: <code>{shortlink_api}</code>\n"
            f"URL: <code>{shortlink_url}</code>"
        )
    except Exception as e:
        await message.reply_text(f"⚠️ Error updating shortlink config: <code>{str(e)}</code>")

@Bot.on_message(filters.command('showshortner') & filters.private & admin)
async def showshortner_command(client: Client, message: Message):
    try:
        config = await db.get_shortlink_config()
        shortlink_api = config.get('api', 'Not set')
        shortlink_url = config.get('url', 'Not set')
        await message.reply_text(
            f"<b>🔗 Shortlink Configuration</b>\n\n"
            f"API: <code>{shortlink_api}</code>\n"
            f"URL: <code>{shortlink_url}</code>"
        )
    except Exception as e:
        await message.reply_text(f"⚠️ Error fetching shortlink config: <code>{str(e)}</code>")

@Bot.on_message(filters.command('edittutvid') & filters.private & admin)
async def edittutvid_command(client: Client, message: Message):
    if len(message.command) != 2:
        await message.reply_text(
            "Usage: /edittutvid <TUT_VID_URL>\n\n"
            "Example:\n"
            "/edittutvid https://t.me/tutorial_video_new"
        )
        return
    try:
        tut_vid_url = message.command[1]
        # Basic URL validation
        if not tut_vid_url.startswith(('http://', 'https://')):
            await message.reply_text("⚠️ Please provide a valid URL starting with http:// or https://")
            return
        await db.set_tutorial_video(tut_vid_url)
        await message.reply_text(
            f"✅ Tutorial video URL updated:\n"
            f"New URL: <code>{tut_vid_url}</code>"
        )
    except Exception as e:
        await message.reply_text(f"⚠️ Error updating tutorial video URL: <code>{str(e)}</code>")        