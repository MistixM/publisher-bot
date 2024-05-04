# Import all important libraries
import telebot
import csv
import config # Config with all information about bot (TOKEN, BOT_OWNER, etc.)
import time

# Init Telebot with token from config
bot = telebot.TeleBot(config.TOKEN)

# Set up in advance parse mode
bot.parse_mode = 'HTML'

# Create a special flag for posting
posting = False

def main():
    # Create a greeting command and check if user is admin of channel
    @bot.message_handler(commands=['start'])
    def say_hi(msg):
        # If user is not admin, just send warning message
        if not check_permission(msg.chat.id):
            bot.send_message(msg.chat.id, "Sorry, you're not allowed to talk 😢")
            return

        # Otherwise, welcome to admin
        bot.send_message(msg.chat.id, 
                         f"Hey, <b>{msg.from_user.full_name}</b>!\n\nI'm <b>{bot.get_my_name().name}</b> and I'll help you publish posts to your Crypto channel!\n\nJust use this commands to publish some content to your channel:\n\n/manual_post: Just publish your own post\n/post: Publish posts via csv file\n/cancel: Missclick? Just use this command to cancel manual post\n/interval: Just set needed time interval between post publishin (in seconds)\n\n<i>Current bot version: {config.BOT_VERSION}</i>")

    # Create an interval command to change post interval
    @bot.message_handler(commands=['interval'])
    def interval_info(msg):
        # If user is not admin, send warning message
        if not check_permission(msg.chat.id):
            bot.send_message(msg.chat.id, "Sorry, you're not allowed to talk 😢")
            return

        # Continue working with admin
        sent_msg = bot.send_message(msg.chat.id,
                         f"Post intervals can help you to manage publishing time (works only for /post command)\nCurrent interval: {config.INTERVAL}\n\nJust type your own inteval (in seconds) and drink some cup of tea! 😄")
        bot.register_next_step_handler(sent_msg, set_new_interval)

    # Create a function that will set interval to the new value
    def set_new_interval(msg):
        global posting

        # Get user interval 
        info = msg.text

        # Check if interval is number
        if info.isdigit():
            config.INTERVAL = int(info)
            bot.send_message(msg.chat.id,
                             f"Your interval was changed successfully! ✅")
            
        # Otherwise just send warning message and add an exception
        else:
            if info == '/cancel':
                posting = False
                bot.send_message(msg.chat.id, f"Sure! I won't post anything yet 👾")
                return
            
            sent_msg = bot.send_message(msg.chat.id, 
                             f"Please, provide correct time (use numbers) 👀")
            bot.register_next_step_handler(sent_msg, set_new_interval)

    """
      Create '/cancel' command to stop post anythin to the channel 
      This command will stop interval and turns posting flag to the False
    """
    @bot.message_handler(commands=['cancel'])
    def cancel_posting(msg):
        global posting

        if posting:
            posting = False
            bot.send_message(msg.chat.id, f"Sure! I won't post anything yet 👾")
        else:
            bot.send_message(msg.chat.id, f"There's no publishing yet.. Type /post or /manual_post to publish some content!⚡")
    
    # Admin can send this command, if wants to publish manually
    @bot.message_handler(commands=['manual_post'])
    def manual_post(msg):
        # Check again permissions
        if not check_permission(msg.chat.id):
            bot.send_message(msg.chat.id, "Sorry, you're not allowed to talk 😢")
            return   
            
        # Continue working with admin
        sent_msg = bot.send_message(msg.chat.id, "Alright, give me all needed information to post (it's optional to use images) ⚡")
        # Register next step
        bot.register_next_step_handler(sent_msg, get_info_manual)
    
    # Step to get info from admin
    def get_info_manual(msg):
        global posting

        # Get info
        info = msg.text

        # Here check if info is not the command.
        if info != '/cancel':
            # Check if message is image with caption or without
            photo_id = msg.photo[-1].file_id if msg.photo else None
            caption = msg.caption if msg.caption else None

            # If post with photo and caption use InputMediaPhoto class to send
            if photo_id and caption:
                media = telebot.types.InputMediaPhoto(photo_id, caption=caption)
                bot.send_media_group(config.CHANNEL_ID, [media])

            # If just photo, use send_photo() to send
            elif photo_id:
                bot.send_photo(config.CHANNEL_ID, photo_id)

            # Otherwise, it's a message
            else:
                bot.send_message(config.CHANNEL_ID, info)

            # Send success message
            bot.send_message(msg.chat.id, f'Post successfully published! ✅')
        
        # If it's '/cancel' command set posting flag to False state
        else:
            posting = False
            bot.send_message(msg.chat.id, f"CTRL + Z.. Hold on..")

    # This function will scrap all information from the csv file and send it with the interval
    @bot.message_handler(commands=['post'])
    def post(msg):
        global posting

        # Check permissions again
        if not check_permission(msg.chat.id):
            bot.send_message(msg.chat.id, "Sorry, you're not allowed to talk 😢")
            return  
        
        # User-friendly message
        bot.send_message(msg.chat.id, f"Alright, I'll post all information from {config.DATA_FILE}..")

        posting = True # Set posting flag
        start_post_from_csv(msg.chat.id)

    # Start scraping csv and post
    def start_post_from_csv(chat_id):
        global posting
        
        # Open csv file
        with open(config.DATA_FILE, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter=',',lineterminator='\n')

            # Check each row in this file
            for row in reader:
                # If posting flag is True, post
                if posting:
                    time.sleep(config.INTERVAL)

                    # If row with Image is None, just send only text
                    if row['Image'] is None:
                        bot.send_message(config.CHANNEL_ID, row['Text'])
                    else:
                        try:
                            # Publish if image with caption exists
                            with open(row['Image'], 'rb') as img:
                                media = telebot.types.InputMediaPhoto(img, caption=row['Text'], parse_mode='HTML')
                                bot.send_media_group(config.CHANNEL_ID, [media])
                        
                        # Otherwise just pass the problem
                        except Exception as e:
                            print(f"No such file or directory: {e}")
                            pass
        
        # Eventually set posting flag to False and send success message
        posting = False
        bot.send_message(chat_id, f"<b>Sheduled posting has been finished!</b> ✅\n\n<b>For the next time, please, update your {config.DATA_FILE} file!</b> 😊")

# Just check if current chat_id bot is chatting with owner's id
def check_permission(chat_id):
    return chat_id == config.BOT_OWNER

if __name__ == '__main__':
    main()
    bot.infinity_polling()