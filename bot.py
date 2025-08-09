import os
import google.generativeai as genai
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
image_model = genai.GenerativeModel("image-alpha-001")  # For image generation

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hey! 👋 I’m your Gemini-powered bot.\n"
        "Created By Tasfiqul Alam Pabel \n"
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

            # Generate image (updated and debugged logic)
            try:
                # Remove the model argument if not needed
                response = image_model.generate_image(prompt=prompt, max_output_tokens=256)
                # Debug: print the raw response to the console
                print("Image response:", response)

                # Try to handle various possible response structures
                image_url = None
                if hasattr(response, "artifacts") and response.artifacts:
                    # Standard expected structure
                    image_url = response.artifacts[0].uri
                elif hasattr(response, "image_url"):
                    # Alternate structure (future-proof)
                    image_url = response.image_url
                elif hasattr(response, "images") and response.images:
                    # Sometimes images list is returned
                    image_url = response.images[0].url
                else:
                    await update.message.reply_text("The image response format is unrecognized. Please check your Gemini API access and response.")
                    return

                await update.message.reply_photo(photo=image_url)
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
