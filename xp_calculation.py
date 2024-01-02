import time
import math

def calculate_xp(message_content, last_message_timestamp):
    word_count = len(message_content.split())
    xp_from_words = word_count * 2

    current_timestamp = int(time.time())
    if current_timestamp - last_message_timestamp < 60:
        return min(xp_from_words, 250)
    else:
        return xp_from_words

def sigmoid_xp_curve(level):
    steepness = 0.04
    xp_offset = 5

    return int(1000 / (1 + math.exp(-steepness * (level - xp_offset))))
