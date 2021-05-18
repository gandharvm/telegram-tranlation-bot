from credentials import TOKEN
from googletrans import Translator
from googletrans.constants import LANGCODES
import logging
import re
from telegram import InlineQueryResultArticle, InputTextMessageContent, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, Filters, InlineQueryHandler, MessageHandler, Updater
from telegram.ext.conversationhandler import ConversationHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

translator = Translator()

reply_keyboard_source = [
        ["Spanish", "German"],
        ["English", "Hindi"],
        ["French", "Auto Detect"],
    ]

reply_keyboard_dest = [
        ["Spanish", "German"],
        ["English", "Hindi"],
        ["French"],
    ]

source_markup = ReplyKeyboardMarkup(reply_keyboard_source, one_time_keyboard=True)
dest_markup = ReplyKeyboardMarkup(reply_keyboard_dest, one_time_keyboard=True)
lang_list = list(LANGCODES.keys())
source_list = lang_list + ["Auto Detect"]

source_filter = r'^(' + "|".join(source_list) + r')$'
dest_filter = r'^(' + "|".join(lang_list) + r')$'

def cancel(update, context):
    try:
        del context.user_data['source']
    except KeyError:
        pass
    try:
        del context.user_data['dest']
    except KeyError:
        pass
    update.message.reply_text("Deleted the source and target languages (if they were set)")
    logger.info("Cancel called")

    return ConversationHandler.END

def conv_helper(update, context):
    helper(update, context)
    return ConversationHandler.END

def dest_lang(update, context):
    context.user_data['dest'] = update.message.text
    update.message.reply_text("Languages set!")
    logger.info("Target language set as " + update.message.text)

    return ConversationHandler.END

def helper(update, context):
    update.message.reply_text(
        "Hi, I am a Translation Bot!\nYou can use me to translate sentences using Google Translate\n\n"
        "Use the /start command to set the source and target languages\n\n"
        "Use the /listlanguages command to list all the languages supported\n\n"
        "When selecting the source and target language, you can either click on the most commonly used languages from the custom kyboard or type any of the supported languages from the default keyboard\n\n"
        "Note that the source language can also be auto detected by the system\n\n"
        "You can use /cancel to delete your language selections anytime\n\n"
        "You can use /help to view this message anytime"
        )
    logger.info("Help called")

def inline_translate(update, context):
    msg = update.inline_query.query

    if not msg:
        return
    try:
        source = context.user_data['source']
    except KeyError:
        source = "Auto Detect"
    try:
        dest = context.user_data['dest']
    except:
        context.bot.answer_inline_query(update.inline_query.id, None, switch_pm_text="Set Source and Target Languages", switch_pm_parameter="useless")
        return

    logger.info("Executing inline query")

    msg = translate_helper(source, dest, msg)

    results = list()
    results.append(
        InlineQueryResultArticle(
            id=msg,
            title='Translate',
            input_message_content=InputTextMessageContent(msg)
        )
    )
    
    context.bot.answer_inline_query(update.inline_query.id, results)

def language_list(update, context):
    logger.info("Started printing supported languages list")
    update.message.reply_text('The following languages are supported as source and destination languages:\n')
    i = 0
    while i < len(lang_list):
        update.message.reply_text("\n".join(lang_list[i:i+10]))
        i+=10
    logger.info("Printed the supported language list")

def source_lang(update, context):
    context.user_data['source'] = update.message.text
    logger.info("Source language set as " + update.message.text)
    update.message.reply_text("Choose a target language",
        reply_markup=dest_markup
    )

    return 1

def start(update, context):
    update.message.reply_text("Hi, I am a Translation Bot!\nYou can use me to translate sentences using Google Translate.\n"
    "Use the command /help to see more information\n\n"
    "Lets start by selecting the source language",
    reply_markup=source_markup)
    logger.info("Start called")
    return 0

def translate(update, context):
    try:
        source = context.user_data['source']
    except KeyError:
        source = "Auto Detect"
    try:
        dest = context.user_data['dest']
    except:
        update.message.reply_text("Please set the source and target languages using /start")
        return
    
    msg = update.message.text
    msg = translate_helper(source, dest, msg)
    update.message.reply_text(msg)

def translate_helper(source, dest, msg):
    log = msg + " " + source + " " 
    if source == "Auto Detect":
        dest_code = LANGCODES[dest.lower()]
        log += dest + " " + dest_code
        msg = translator.translate(msg, dest=dest_code).text

    elif source == dest:
        log += dest
    
    else:
        dest_code = LANGCODES[dest.lower()]
        src_code = LANGCODES[source.lower()]
        log += src_code + " " + dest + " " + dest_code
        msg = translator.translate(msg, dest=dest_code, src=src_code).text
    
    log +=  " -> " + msg
    logger.info(log)
    return msg

def main():
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points= [CommandHandler(('start'), start)],
        states={
            0: [
                MessageHandler(Filters.regex(re.compile(source_filter, re.IGNORECASE)), source_lang)
            ],
            1: [
                MessageHandler(Filters.regex(re.compile(dest_filter, re.IGNORECASE)), dest_lang)
            ]
        },
        fallbacks=[CommandHandler('help', conv_helper), MessageHandler(Filters.text, cancel)],
    )
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler(('help'), helper))
    translate_handler = MessageHandler(Filters.text & (~Filters.command), translate)
    dispatcher.add_handler(translate_handler)
    dispatcher.add_handler(CommandHandler('cancel', cancel))
    inline_translate_handler = InlineQueryHandler(inline_translate)
    dispatcher.add_handler(inline_translate_handler)
    dispatcher.add_handler(CommandHandler('listlanguages', language_list))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
