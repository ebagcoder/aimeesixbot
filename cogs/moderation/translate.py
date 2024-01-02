from discord.ext import commands
import deepl
from googletrans import Translator as GoogleTranslator
import config  # This imports config.py
import logging
import re

class AutoTranslateCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.deepl_translator = deepl.Translator(config.DEEPL_API_KEY) if config.DEEPL_API_KEY else None
        self.google_translator = GoogleTranslator()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.is_system() or message.content.startswith('!'):
            return

        # Remove mentions from the message
        content = re.sub(r'<@!?(\d+)>', '', message.content).strip()

        if self.deepl_translator and content:
            try:
                # First, detect the language using Google Translator
                detected_language = self.google_translator.detect(content).lang

                # Proceed with translation if the detected language is not English
                if detected_language != "en":
                    translation = self.deepl_translator.translate_text(content, target_lang="EN-US")
                    await message.reply(f"Translated from {translation.detected_source_lang}: {translation.text}", mention_author=False)
                else:
                    logging.info("Message is already in English. No translation performed.")
            except deepl.DeepLException as e:
                logging.error(f"DeepL translation failed: {e}")
                try:
                    # Google Translate fallback
                    if detected_language != "en":
                        translated = self.google_translator.translate(content, dest='en')
                        await message.reply(f"Translated (fallback to Google): {translated.text}", mention_author=False)
                except Exception as e:
                    logging.error(f"Error during translation with fallback service: {e}")

def setup(bot):
    bot.add_cog(AutoTranslateCog(bot))
