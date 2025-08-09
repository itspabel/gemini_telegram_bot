import os
import google.generativeai as genai
from PIL import Image
from io import BytesIO
import base64
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
)

# Load env variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID"))

# Configure Gemini with the latest model for text and image
genai.configure(api_key=GEMINI_API_KEY)
text_model = genai.GenerativeModel("gemini-1.5-flash")  # For text

# Use the newer Gemini image generation model
image_model = genai.GenerativeModel("gemini-2.0-flash-preview-image-generation")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hey! 👋 I’m your Gemini-powered bot.\n by @TasfiqulAlamPabel"
        "Send me any text to chat, or start your message with /image to generate pictures!\n\n"
        "Example:\n/image a beautiful sunset over mountains"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()
    try:
        if user_message.lower().startswith("/image"):
            prompt = user_message[len("/image"):].strip()
            if not prompt:
                await update.message.reply_text("Please provide a prompt after /image command.")
                return

            try:
                response = image_model.generate_content(
                    prompt,
                    generation_config={
                        "response_mime_type": "image/png",
                        "response_modalities": ["TEXT", "IMAGE"]
                    }
                )
                # Try to handle both TEXT and IMAGE responses
                image_found = False
                text_found = False
                for part in response.parts:
                    if hasattr(part, "text") and part.text is not None and not text_found:
                        await update.message.reply_text(part.text)
                        text_found = True
                    elif hasattr(part, "inline_data") and part.inline_data is not None and not image_found:
                        # Decode base64 image data
                        img_data = base64.b64decode(part.inline_data.data)
                        image = Image.open(BytesIO(img_data))
                        # Save to a temp file and send
                        temp_path = "gemini-native-image.png"
                        image.save(temp_path)
                        with open(temp_path, "rb") as img_file:
                            await update.message.reply_photo(photo=img_file)
                        image_found = True
                if not image_found:
                    await update.message.reply_text("❌ No image returned by Gemini. Please try a different prompt.")
            except Exception as e:
                await update.message.reply_text(f"⚠️ Image generation error: {str(e)}")
        else:
            # Generate text response
            response = text_model.generate_content(user_message)
            await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {str(e)}")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_USER_ID:
        await update.message.reply_text("Shutting down... 🛑")
        quit()
    else:
        await update.message.reply_text("⛔ You are not authorized to stop me.")

# Build bot
app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("stop", stop))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🚀 Bot is running...")
app.run_polling()
