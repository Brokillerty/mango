import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, ConversationHandler

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# States
RECEIVING_VIDEO, SELECTING_GENRES = range(2)

# Dictionary to store user data
user_data = {}

# Genre categories and options
GENRES = {
    "🎬 Тип контента": [
        "Foto", "Video", "GIF", "Clips", "Selfie", "Mirror", "Loop"
    ],
    "🧑‍🎨 Тематика и атмосфера": [
        "Erotica", "NSFArt", "Art", "Aesthetic", "Mood", "Soft", "Hard", "Light", "Vintage"
    ],
    "🧬 Персонажи / фетиши": [
        "Cosplay", "Hentai", "Latex", "Lingerie", "BDSM", "Feet", "Toys", "Roleplay"
    ],
    "🌍 По внешности / этнотипу": [
        "Brunette", "Blonde", "Redhead", "Asian", "Latina", "Euro", "Natural"
    ],
    "💎 Специальные": [
        "Top", "Exclusive", "Private"
    ]
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask user to send a video."""
    await update.message.reply_text(
        "Привет! Отправь мне видео, и я помогу тебе добавить к нему хэштеги."
    )
    return RECEIVING_VIDEO

async def receive_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store the video and ask for genres."""
    user_id = update.effective_user.id
    
    # Store video file_id
    if update.message.video:
        video_file_id = update.message.video.file_id
    else:
        await update.message.reply_text("Пожалуйста, отправь видео.")
        return RECEIVING_VIDEO
    
    # Initialize user data
    user_data[user_id] = {
        "video_file_id": video_file_id,
        "selected_genres": []
    }
    
    # Create keyboard with genre categories
    keyboard = []
    for category, genres in GENRES.items():
        for genre in genres:
            keyboard.append([
                InlineKeyboardButton(f"#{genre}", callback_data=f"genre_{genre}")
            ])
    
    # Add "Done" button
    keyboard.append([InlineKeyboardButton("Готово ✅", callback_data="done")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Выбери жанры для твоего видео:", 
        reply_markup=reply_markup
    )
    
    return SELECTING_GENRES

async def genre_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle genre selection."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if query.data == "done":
        # User is done selecting genres
        if user_id in user_data and "video_file_id" in user_data[user_id]:
            video_file_id = user_data[user_id]["video_file_id"]
            selected_genres = user_data[user_id]["selected_genres"]
            
            # Create caption with hashtags
            caption = " ".join([f"#{genre}" for genre in selected_genres])
            
            # Send video back with hashtags
            await query.message.reply_video(
                video=video_file_id,
                caption=caption
            )
            
            # Clean up user data
            if user_id in user_data:
                del user_data[user_id]
            
            await query.message.reply_text("Готово! Отправь мне еще видео, если хочешь.")
            return RECEIVING_VIDEO
        else:
            await query.message.reply_text("Произошла ошибка. Пожалуйста, начни заново.")
            return ConversationHandler.END
    else:
        # User selected a genre
        genre = query.data.replace("genre_", "")
        
        if user_id in user_data:
            if genre in user_data[user_id]["selected_genres"]:
                # Remove genre if already selected
                user_data[user_id]["selected_genres"].remove(genre)
                await query.message.edit_text(
                    f"Жанр #{genre} удален. Выбери жанры для твоего видео:",
                    reply_markup=query.message.reply_markup
                )
            else:
                # Add genre to selected list
                user_data[user_id]["selected_genres"].append(genre)
                await query.message.edit_text(
                    f"Жанр #{genre} добавлен. Выбери жанры для твоего видео:",
                    reply_markup=query.message.reply_markup
                )
        
        return SELECTING_GENRES

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel and end the conversation."""
    user_id = update.effective_user.id
    if user_id in user_data:
        del user_data[user_id]
    
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

def main() -> None:
    """Run the bot."""
    # Create the Application
    application = Application.builder().token("8016720296:AAHV3uF5IPw2b4J0x-2za6IQ7-x75jo90d8").build()

    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            RECEIVING_VIDEO: [MessageHandler(filters.VIDEO, receive_video)],
            SELECTING_GENRES: [CallbackQueryHandler(genre_selection)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == "__main__":
    main()
