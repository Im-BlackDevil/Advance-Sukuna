from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot import Bot
from pyrogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from asyncio import TimeoutError
from helper_func import encode, get_message_id, admin
import base64
import time
import random
import string

# Function to generate a random padding string
def generate_padding(length=50):
    """Generate random padding to make the encoded string longer"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Function to add timestamp for uniqueness
def get_timestamp():
    """Get current timestamp in milliseconds"""
    return str(int(time.time() * 1000))

@Bot.on_message(filters.private & admin & filters.command('batch'))
async def batch(client: Client, message: Message):
    while True:
        try:
            first_message = await client.ask(text = "Forward the First Message from DB Channel (with Quotes)..\n\nor Send the DB Channel Post Link", chat_id = message.from_user.id, filters=(filters.forwarded | (filters.text & ~filters.forwarded)), timeout=60)
        except:
            return
        f_msg_id = await get_message_id(client, first_message)
        if f_msg_id:
            break
        else:
            await first_message.reply("❌ Error\n\nthis Forwarded Post is not from my DB Channel or this Link is taken from DB Channel", quote = True)
            continue

    while True:
        try:
            second_message = await client.ask(text = "Forward the Last Message from DB Channel (with Quotes)..\nor Send the DB Channel Post link", chat_id = message.from_user.id, filters=(filters.forwarded | (filters.text & ~filters.forwarded)), timeout=60)
        except:
            return
        s_msg_id = await get_message_id(client, second_message)
        if s_msg_id:
            break
        else:
            await second_message.reply("❌ Error\n\nthis Forwarded Post is not from my DB Channel or this Link is taken from DB Channel", quote = True)
            continue

    # Method 1: Add timestamp and padding for longer strings
    timestamp = get_timestamp()
    padding = generate_padding(30)  # Add 30 random characters
    string = f"get-{f_msg_id * abs(client.db_channel.id)}-{s_msg_id * abs(client.db_channel.id)}-{timestamp}-{padding}"
    
    # Method 2: Alternative - multiply IDs by larger numbers
    # multiplier = 1000000  # Make this larger for longer strings
    # string = f"get-{f_msg_id * abs(client.db_channel.id) * multiplier}-{s_msg_id * abs(client.db_channel.id) * multiplier}"
    
    # Method 3: Alternative - add more metadata
    # user_id = message.from_user.id
    # chat_id = abs(message.chat.id)
    # string = f"get-{f_msg_id * abs(client.db_channel.id)}-{s_msg_id * abs(client.db_channel.id)}-{user_id}-{chat_id}-{timestamp}"
    
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
    await second_message.reply_text(f"<b>Here is your link</b>\n\n{link}", quote=True, reply_markup=reply_markup)


@Bot.on_message(filters.private & admin & filters.command('genlink'))
async def link_generator(client: Client, message: Message):
    while True:
        try:
            channel_message = await client.ask(text = "Forward Message from the DB Channel (with Quotes)..\nor Send the DB Channel Post link", chat_id = message.from_user.id, filters=(filters.forwarded | (filters.text & ~filters.forwarded)), timeout=60)
        except:
            return
        msg_id = await get_message_id(client, channel_message)
        if msg_id:
            break
        else:
            await channel_message.reply("❌ Error\n\nthis Forwarded Post is not from my DB Channel or this Link is not taken from DB Channel", quote = True)
            continue

    # Add timestamp and padding for longer strings
    timestamp = get_timestamp()
    padding = generate_padding(40)  # Add 40 random characters for single messages
    string = f"get-{msg_id * abs(client.db_channel.id)}-{timestamp}-{padding}"
    
    # Alternative methods (uncomment to use):
    # Method 2: Use larger multiplier
    # multiplier = 10000000
    # string = f"get-{msg_id * abs(client.db_channel.id) * multiplier}"
    
    # Method 3: Add user and chat info
    # user_id = message.from_user.id
    # string = f"get-{msg_id * abs(client.db_channel.id)}-{user_id}-{timestamp}"
    
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
    await channel_message.reply_text(f"<b>Here is your link</b>\n\n{link}", quote=True, reply_markup=reply_markup)


@Bot.on_message(filters.private & admin & filters.command("custom_batch"))
async def custom_batch(client: Client, message: Message):
    collected = []
    STOP_KEYBOARD = ReplyKeyboardMarkup([["STOP"]], resize_keyboard=True)

    await message.reply("Send all messages you want to include in batch.\n\nPress STOP when you're done.", reply_markup=STOP_KEYBOARD)

    while True:
        try:
            user_msg = await client.ask(
                chat_id=message.chat.id,
                text="Waiting for files/messages...\nPress STOP to finish.",
                timeout=60
            )
        except asyncio.TimeoutError:
            break

        if user_msg.text and user_msg.text.strip().upper() == "STOP":
            break

        try:
            sent = await user_msg.copy(client.db_channel.id, disable_notification=True)
            collected.append(sent.id)
        except Exception as e:
            await message.reply(f"❌ Failed to store a message:\n<code>{e}</code>")
            continue

    await message.reply("✅ Batch collection complete.", reply_markup=ReplyKeyboardRemove())

    if not collected:
        await message.reply("❌ No messages were added to batch.")
        return

    # Add timestamp and padding for longer custom batch strings
    timestamp = get_timestamp()
    padding = generate_padding(35)
    start_id = collected[0] * abs(client.db_channel.id)
    end_id = collected[-1] * abs(client.db_channel.id)
    
    # Include number of files in the batch and other metadata
    file_count = len(collected)
    string = f"get-{start_id}-{end_id}-{file_count}-{timestamp}-{padding}"
    
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
    await message.reply(f"<b>Here is your custom batch link:</b>\n\n{link}", reply_markup=reply_markup)