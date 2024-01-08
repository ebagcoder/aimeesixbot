import re
import logging
from discord.ext import commands
import deepl
import config  # Ensure config.py with DEEPL_API_KEY is defined
from googletrans import Translator, LANGUAGES
from spellchecker import SpellChecker

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Google Translator
translator = Translator()
spell = SpellChecker()

class AutoTranslateCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spell = SpellChecker()
        self.deepl_translator = deepl.Translator(config.DEEPL_API_KEY)

    def clean_message_content(self, content):
        # Remove custom Discord static emojis: <:name:id>
        content = re.sub(r'<:\w+:\d+>', '', content)
        # Remove custom Discord animated emojis: <a:name:id>
        content = re.sub(r'<a:\w+:\d+>', '', content)
        # Remove Unicode emojis and other unwanted characters as before
        content = re.sub(
            '['
            u'\U0001F600-\U0001F64F'  # emoticons
            u'\U0001F300-\U0001F5FF'  # symbols & pictographs
            u'\U0001F680-\U0001F6FF'  # transport & map symbols
            u'\U0001F700-\U0001F77F'  # alchemical symbols
            u'\U0001F780-\U0001F7FF'  # Geometric Shapes Extended
            u'\U0001F800-\U0001F8FF'  # Supplemental Arrows-C
            u'\U0001F900-\U0001F9FF'  # Supplemental Symbols and Pictographs
            u'\U0001FA00-\U0001FA6F'  # Chess Symbols
            u'\U0001FA70-\U0001FAFF'  # Symbols and Pictographs Extended-A
            u'\U00002702-\U000027B0'  # Dingbats
            u'\U000024C2-\U0001F251'  # Enclosed characters
            ']+', '', content, flags=re.UNICODE
        )
        return content.strip()


    def is_english(self, text):
        try:
            # Use googletrans to detect the language
            detected_lang = translator.detect(text).lang
            return detected_lang in ['en', 'EN', 'EN-US', 'EN-GB']
        except Exception as e:
            logging.error(f"Language detection error: {e}")
            # In case of an error, assume it's not English to be safe
            return False

    def spell_check(self, text):
        try:
            words = text.split()
            corrected_words = [self.spell.correction(word) for word in words]
            return ' '.join(corrected_words)
        except Exception as e:
            logging.error(f"Spell check error: {e}")
            return text  # Return the original text if spell check fails


    @commands.Cog.listener()
    async def on_message(self, message):
        if self.should_ignore_message(message):
            return

        cleaned_content = self.clean_message_content(message.content)
        if not cleaned_content:
            return  # Skip empty or emoji-only messages

        if self.is_english(cleaned_content):
            spell_checked_content = self.spell_check(cleaned_content)
            # Check if the content changed after spell check
            if spell_checked_content.lower() != cleaned_content.lower():
                # If there's a difference, it means there was a spelling mistake
                # Since it's English and only a spelling error, do nothing
                return
            else:
                # If there's no difference, it means it's proper English, so do nothing
                return

        # If the message is not in English, attempt to translate
        try:
            translated_text = self.translate_text(cleaned_content, 'EN-US')
            if translated_text and translated_text.lower() != cleaned_content.lower():
                # Only send a reply if the translated text is different from the original
                await message.reply(f"Translated text: {translated_text}", mention_author=False)
        except Exception as e:
            logging.error(f"Error during translation: {e}")




    def translate_text(self, text, target_language):
        try:
            result = self.deepl_translator.translate_text(text, target_lang=target_language)
            return result.text
        except Exception as e:
            logging.error(f"DeepL translation error: {e}")
            return None

    def should_ignore_message(self, message):
        return (
            message.author.bot or
            message.is_system() or
            self.bot.user.mentioned_in(message) or
            message.content.startswith(self.bot.command_prefix)
        )

def setup(bot):
    bot.add_cog(AutoTranslateCog(bot))
