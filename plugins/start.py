
import asyncio
import os
import random
import sys
import re
import string 
import string as rohit
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
from database.db_premium import *

BAN_SUPPORT = f"{BAN_SUPPORT}"
TUT_VID = f"{TUT_VID}"

async def short_url(client: Client, message: Message, base64_string):
    try:
        prem_link = f"https://t.me/{client.username}?start=yu3elk{base64_string}7"
        short_link = await get_shortlink(SHORTLINK_URL, SHORTLINK_API, prem_link)

        buttons = [
            [
                InlineKeyboardButton(text="ᴅᴏᴡɴʟᴏᴀᴅ", url=short_link),
                InlineKeyboardButton(text="ᴛᴜᴛᴏʀɪᴀʟ", url=TUT_VID)
            ],
            [
                InlineKeyboardButton(text="ᴘʀᴇᴍɪᴜᴍ", callback_data="premium")
            ]
        ]

        await message.reply_photo(
            photo=SHORTENER_PIC,
            caption=SHORT_MSG.format(),
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    except IndexError:
        pass

@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    id = message.from_user.id
    is_premium = await is_premium_user(id)

    # Check if user is banned
    banned_users = await db.get_ban_users()
    if user_id in banned_users:
        return await message.reply_text(
            "<b>⛔️ You are Bᴀɴɴᴇᴅ from using this bot.</b>\n\n"
            "<i>Contact support if you think this is a mistake.</i>",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Contact Support", url=BAN_SUPPORT)]]
            )
        )

    # ✅ Check Force Subscription
    if not await is_subscribed(client, user_id):
        return await not_joined(client, message)

    # File auto-delete time in seconds
    FILE_AUTO_DELETE = await db.get_del_timer()

    # Add user if not already present
    if not await db.present_user(user_id):
        try:
            await db.add_user(user_id)
        except:
            pass

    # Fetch all start sub pictures from the database
    start_pics = await db.get_start_pics()
    if start_pics:
        # Randomly select one image from the list
        start_pic = random.choice(start_pics)['url']
    else:
        start_pic = START_PIC  # Fallback to default if no photos in DB

    # Handle normal message flow
    text = message.text

    if len(text) > 7:
        try:
            basic = text.split(" ", 1)[1]
            print(f"🔍 Received payload: {basic}")  # Debug log
            
            # Handle premium links (yu3elk prefix)
            if basic.startswith("yu3elk") and basic.endswith("7"):
                base64_string = basic[6:-1]  # Remove yu3elk prefix and 7 suffix
                print(f"✅ Premium link detected, base64: {base64_string}")  # Debug log
            else:
                base64_string = basic
                print(f"📝 Regular link, base64: {base64_string}")  # Debug log

            # For non-premium users, redirect to shortener
            if not is_premium and user_id != OWNER_ID and not basic.startswith("yu3elk"):
                print(f"🔒 Non-premium user, redirecting to shortener")
                await short_url(client, message, base64_string)
                return

        except Exception as e:
            print(f"❌ Error processing start payload: {e}")
            await message.reply_text("❌ Invalid link format!")
            return

        # Decode the base64 string
        try:
            decoded_string = await decode(base64_string)
            print(f"🔓 Decoded string: {decoded_string}")  # Debug log
        except Exception as e:
            print(f"❌ Base64 decode error: {e}")
            await message.reply_text("❌ Invalid link! Could not decode.")
            return

        # Extract message IDs using your existing function
        try:
            raw_ids = extract_message_ids(decoded_string)
            print(f"📋 Extracted raw IDs: {raw_ids}")  # Debug log
            
            if not raw_ids:
                print(f"❌ No IDs extracted from: {decoded_string}")
                await message.reply_text("❌ Invalid link format! Could not extract message IDs.")
                return
            
            # Convert raw IDs to actual message IDs
            ids = []
            if len(raw_ids) == 1:
                # Single message
                actual_id = int(raw_ids[0] / abs(client.db_channel.id))
                ids = [actual_id]
                print(f"📄 Single message ID: {actual_id}")
            elif len(raw_ids) == 2:
                # Batch of messages
                start_raw = raw_ids[0]
                end_raw = raw_ids[1]
                start = int(start_raw / abs(client.db_channel.id))
                end = int(end_raw / abs(client.db_channel.id))
                ids = list(range(start, end + 1)) if start <= end else list(range(start, end - 1, -1))
                print(f"📚 Batch IDs: {start} to {end} (total: {len(ids)})")
            else:
                print(f"⚠️ Unexpected number of raw IDs: {len(raw_ids)}")
                await message.reply_text("❌ Invalid link format!")
                return
                
        except Exception as e:
            print(f"❌ Error extracting message IDs: {e}")
            
            # Fallback to old decoding method
            try:
                print(f"🔄 Trying fallback method...")
                parts = decoded_string.split("-")
                print(f"🔧 Split parts: {parts}")
                
                if len(parts) == 2 and parts[0] == "get":
                    # Single message: get-msgid
                    msg_id = int(parts[1])
                    actual_id = int(msg_id / abs(client.db_channel.id))
                    ids = [actual_id]
                    print(f"📄 Fallback single ID: {actual_id}")
                elif len(parts) == 3 and parts[0] == "get":
                    # Batch: get-start-end
                    start_id = int(parts[1])
                    end_id = int(parts[2])
                    start = int(start_id / abs(client.db_channel.id))
                    end = int(end_id / abs(client.db_channel.id))
                    ids = list(range(start, end + 1)) if start <= end else list(range(start, end - 1, -1))
                    print(f"📚 Fallback batch: {start} to {end}")
                else:
                    print(f"❌ Unrecognized format in fallback: {parts}")
                    await message.reply_text("❌ Invalid link format!")
                    return
                    
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {fallback_error}")
                await message.reply_text("❌ Failed to process the link!")
                return

        # Show loading message
        temp_msg = await message.reply("<b>📥 Fetching your files...</b>")
        
        try:
            print(f"📡 Getting messages with IDs: {ids[:5]}{'...' if len(ids) > 5 else ''}")
            messages = await get_messages(client, ids)
            
            if not messages:
                await temp_msg.edit("<b>❌ No messages found!</b>")
                print(f"❌ No messages retrieved for IDs: {ids}")
                return
                
            print(f"✅ Retrieved {len(messages)} messages")
            
        except Exception as e:
            await temp_msg.edit(f"<b>❌ Error retrieving messages: {str(e)}</b>")
            print(f"❌ Error getting messages: {e}")
            return
        finally:
            try:
                await temp_msg.delete()
            except:
                pass

        # Send messages to user
        codeflix_msgs = []
        successful_sends = 0
        
        for i, msg in enumerate(messages):
            if not msg:
                print(f"⚠️ Message {i} is None, skipping")
                continue
                
            try:
                # Prepare caption
                caption = ""
                if CUSTOM_CAPTION and msg.document:
                    caption = CUSTOM_CAPTION.format(
                        previouscaption="" if not msg.caption else msg.caption.html,
                        filename=msg.document.file_name if msg.document.file_name else "Unknown File"
                    )
                elif msg.caption:
                    caption = msg.caption.html

                # Prepare reply markup
                reply_markup = msg.reply_markup if not DISABLE_CHANNEL_BUTTON else None

                # Copy message to user
                copied_msg = await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=PROTECT_CONTENT
                )
                codeflix_msgs.append(copied_msg)
                successful_sends += 1
                print(f"✅ Sent message {i+1}/{len(messages)}")
                
            except FloodWait as e:
                print(f"⏳ FloodWait: {e.x} seconds for message {i}")
                await asyncio.sleep(e.x)
                try:
                    copied_msg = await msg.copy(
                        chat_id=message.from_user.id,
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                        reply_markup=reply_markup,
                        protect_content=PROTECT_CONTENT
                    )
                    codeflix_msgs.append(copied_msg)
                    successful_sends += 1
                    print(f"✅ Sent message {i+1}/{len(messages)} after FloodWait")
                except Exception as retry_e:
                    print(f"❌ Retry failed for message {i}: {retry_e}")
                    
            except Exception as e:
                print(f"❌ Failed to send message {i}: {e}")

        print(f"📊 Successfully sent {successful_sends}/{len(messages)} messages")

        # Handle auto-delete if enabled and files were sent
        if FILE_AUTO_DELETE > 0 and codeflix_msgs:
            try:
                notification_msg = await message.reply(
                    f"<b>⏰ This file will be deleted in {get_exp_time(FILE_AUTO_DELETE)}. "
                    f"Please save or forward it to your saved messages before it gets deleted.</b>"
                )

                print(f"⏰ Auto-delete timer set for {FILE_AUTO_DELETE} seconds")
                await asyncio.sleep(FILE_AUTO_DELETE)

                # Delete all sent files
                deleted_count = 0
                for snt_msg in codeflix_msgs:    
                    if snt_msg:
                        try:    
                            await snt_msg.delete()
                            deleted_count += 1
                        except Exception as e:
                            print(f"❌ Error deleting message {snt_msg.id}: {e}")

                print(f"🗑️ Deleted {deleted_count}/{len(codeflix_msgs)} messages")

                # Update notification with "Get File Again" button
                try:
                    reload_url = f"https://t.me/{client.username}?start={message.command[1]}"
                    keyboard = InlineKeyboardMarkup(
                        [[InlineKeyboardButton("🔄 Get File Again!", url=reload_url)]]
                    )

                    await notification_msg.edit(
                        "<b>🗑️ Your files have been successfully deleted!\n\n"
                        "Click the button below to get your files again 👇</b>",
                        reply_markup=keyboard
                    )
                except Exception as e:
                    print(f"❌ Error updating notification: {e}")
                    
            except Exception as e:
                print(f"❌ Error in auto-delete process: {e}")
                
    else:
        # No payload - show start message
        reply_markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("• ᴍᴏʀᴇ ᴄʜᴀɴɴᴇʟs •", url="https://t.me/Infinix_Adult")],
                [
                    InlineKeyboardButton("• ᴀʙᴏᴜᴛ", callback_data="about"),
                    InlineKeyboardButton('ʜᴇʟᴘ •', callback_data="help")
                ]
            ]
        )
        await message.reply_photo(
            photo=start_pic,
            caption=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=reply_markup,
            message_effect_id=5104841245755180586  # 🔥
        )
        print(f"👋 Sent start message to user {user_id}")
        return
#=====================================================================================##

@Bot.on_message(filters.command('myplan') & filters.private)
async def check_plan(client: Client, message: Message):
    user_id = message.from_user.id  # Get user ID from the message

    # Get the premium status of the user
    status_message = await check_user_plan(user_id)

    # Send the response message to the user
    await message.reply(status_message)

#=====================================================================================##
# Command to add premium user
@Bot.on_message(filters.command('addpremium') & filters.private & admin)
async def add_premium_user_command(client, msg):
    if len(msg.command) != 4:
        await msg.reply_text(
            "Usage: /addpaid <user_id> <time_value> <time_unit>\n\n"
            "Time Units:\n"
            "s - seconds\n"
            "m - minutes\n"
            "h - hours\n"
            "d - days\n"
            "y - years\n\n"
            "Examples:\n"
            "/addpremium 123456789 30 m → 30 minutes\n"
            "/addpremium 123456789 2 h → 2 hours\n"
            "/addpremium 123456789 1 d → 1 day\n"
            "/addpremium 123456789 1 y → 1 year"
        )
        return

    try:
        user_id = int(msg.command[1])
        time_value = int(msg.command[2])
        time_unit = msg.command[3].lower()  # supports: s, m, h, d, y

        # Call add_premium function
        expiration_time = await add_premium(user_id, time_value, time_unit)

        # Notify the admin
        await msg.reply_text(
            f"✅ User `{user_id}` added as a premium user for {time_value} {time_unit}.\n"
            f"Expiration Time: `{expiration_time}`"
        )

        # Notify the user
        await client.send_message(
            chat_id=user_id,
            text=(
                f"🎉 Premium Activated!\n\n"
                f"You have received premium access for `{time_value} {time_unit}`.\n"
                f"Expires on: `{expiration_time}`"
            ),
        )

    except ValueError:
        await msg.reply_text("❌ Invalid input. Please ensure user ID and time value are numbers.")
    except Exception as e:
        await msg.reply_text(f"⚠️ An error occurred: `{str(e)}`")


# Command to remove premium user
@Bot.on_message(filters.command('remove_premium') & filters.private & admin)
async def pre_remove_user(client: Client, msg: Message):
    if len(msg.command) != 2:
        await msg.reply_text("useage: /remove_premium user_id ")
        return
    try:
        user_id = int(msg.command[1])
        await remove_premium(user_id)
        await msg.reply_text(f"User {user_id} has been removed.")
    except ValueError:
        await msg.reply_text("user_id must be an integer or not available in database.")


# Command to list active premium users
@Bot.on_message(filters.command('premium_users') & filters.private & admin)
async def list_premium_users_command(client, message):
    # Define IST timezone
    ist = timezone("Asia/Kolkata")

    # Retrieve all users from the collection
    premium_users_cursor = collection.find({})
    premium_user_list = ['Active Premium Users in database:']
    current_time = datetime.now(ist)  # Get current time in IST

    # Use async for to iterate over the async cursor
    async for user in premium_users_cursor:
        user_id = user["user_id"]
        expiration_timestamp = user["expiration_timestamp"]

        try:
            # Convert expiration_timestamp to a timezone-aware datetime object in IST
            expiration_time = datetime.fromisoformat(expiration_timestamp).astimezone(ist)

            # Calculate remaining time
            remaining_time = expiration_time - current_time

            if remaining_time.total_seconds() <= 0:
                # Remove expired users from the database
                await collection.delete_one({"user_id": user_id})
                continue  # Skip to the next user if this one is expired

            # If not expired, retrieve user info
            user_info = await client.get_users(user_id)
            username = user_info.username if user_info.username else "No Username"
            first_name = user_info.first_name
            mention=user_info.mention

            # Calculate days, hours, minutes, seconds left
            days, hours, minutes, seconds = (
                remaining_time.days,
                remaining_time.seconds // 3600,
                (remaining_time.seconds // 60) % 60,
                remaining_time.seconds % 60,
            )
            expiry_info = f"{days}d {hours}h {minutes}m {seconds}s left"

            # Add user details to the list
            premium_user_list.append(
                f"UserID: <code>{user_id}</code>\n"
                f"User: @{username}\n"
                f"Name: {mention}\n"
                f"Expiry: {expiry_info}"
            )
        except Exception as e:
            premium_user_list.append(
                f"UserID: <code>{user_id}</code>\n"
                f"Error: Unable to fetch user details ({str(e)})"
            )

    if len(premium_user_list) == 1:  # No active users found
        await message.reply_text("I found 0 active premium users in my DB")
    else:
        await message.reply_text("\n\n".join(premium_user_list), parse_mode=None)


#=====================================================================================##

@Bot.on_message(filters.command("count") & filters.private & admin)
async def total_verify_count_cmd(client, message: Message):
    total = await db.get_total_verify_count()
    await message.reply_text(f"Tᴏᴛᴀʟ ᴠᴇʀɪғɪᴇᴅ ᴛᴏᴋᴇɴs ᴛᴏᴅᴀʏ: <b>{total}</b>")


#=====================================================================================##

@Bot.on_message(filters.command('commands') & filters.private & admin)
async def bcmd(bot: Bot, message: Message):        
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("• ᴄʟᴏsᴇ •", callback_data = "close")]])
    await message.reply(text=CMD_TXT, reply_markup = reply_markup, quote= True)