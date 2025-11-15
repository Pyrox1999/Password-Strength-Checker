import os
os.environ['SDL_VIDEO_WINDOW_POS'] = '100,100'
import random
import pgzrun
import pygame
import re
import math

pygame.mixer.music.load("song.mp3") #MintoDog
pygame.mixer.music.play(-1)

level = -1
target=""
pw=""

COMMON_PASSWORDS = {
    "password", "123456", "123456789", "qwerty", "111111", "abc123",
    "12345678", "iloveyou", "admin", "welcome", "monkey", "dragon",
    "letmein", "football", "baseball", "trustno1", "starwars", "hello",
    "freedom", "whatever", "qazwsx", "123123", "654321"
}

COMMON_PATTERNS = [
    re.compile(r"(.)\1{2,}"),            
    re.compile(r"[a-z]{4,}"),            
    re.compile(r"[A-Z]{4,}"),            
    re.compile(r"\d{4,}"),               
    re.compile(r"(?:password|qwerty|letmein|admin|welcome)", re.I),
    re.compile(r"(?:12345|123456|1234567|12345678|123456789)"),
]

def charset_size(pw: str) -> int:
    size = 0
    has_lower = any(c.islower() for c in pw)
    has_upper = any(c.isupper() for c in pw)
    has_digit = any(c.isdigit() for c in pw)
    has_symbol = any(not c.isalnum() for c in pw)
    if has_lower or has_upper:
        pass
    size += 26 if has_lower else 0
    size += 26 if has_upper else 0
    size += 10 if has_digit else 0
    size += 32 if has_symbol else 0
    return size or 1  

def estimate_entropy_bits(pw: str) -> float:
    return len(pw) * math.log2(charset_size(pw))

def zxcvbnish_penalties(pw: str) -> int:
    penalty = 0
    if pw.lower() in COMMON_PASSWORDS:
        penalty += 30
    for pat in COMMON_PATTERNS:
        if pat.search(pw):
            penalty += 10
    seqs = ["abcdefghijklmnopqrstuvwxyz", "qwertyuiop", "asdfghjkl", "zxcvbnm",
            "0123456789", "9876543210"]
    low = pw.lower()
    for s in seqs:
        for i in range(len(s) - 3):
            if s[i:i+4] in low:
                penalty += 10
                break
    return penalty

def strength_score(pw: str) -> dict:
    feedback = []
    score = 0

    if not pw:
        return {
            "score": 0, "label": "Very weak",
            "entropy_bits": 0.0,
            "feedback": ["Password has not to be empty."]
        }

    length = len(pw)
    classes = {
        "lower": any(c.islower() for c in pw),
        "upper": any(c.isupper() for c in pw),
        "digit": any(c.isdigit() for c in pw),
        "symbol": any(not c.isalnum() for c in pw),
    }
    class_count = sum(classes.values())

    score += min(length * 2, 40)                  
    score += (class_count - 1) * 10               

    if classes["symbol"]:
        score += 5
    if classes["upper"] and classes["lower"]:
        score += 5

    if length < 8:
        feedback.append("Minimum are 12 characters.")
        score -= 15
    if class_count < 3:
        feedback.append("Upper-/Lowcase, digits and symbols must be mixed.")
        score -= 10
    if pw.lower() in COMMON_PASSWORDS:
        feedback.append("Don't use a password too many times.")
        score -= 30
    if re.search(r"^\w+$", pw):
        feedback.append("Not only letters/digits. Add some symbols.")
    if re.search(r"(.)\1{2,}", pw):
        feedback.append("Avoid repeating (for example:aaa, 1111).")
        score -= 10
    if re.search(r"^\d+$", pw):
        feedback.append("Only-digits-passwords are easy to get.")
        score -= 15
    if re.search(r"^[A-Za-z]+$", pw):
        feedback.append("Only-character-passwords are predictable.")
        score -= 10

    score -= zxcvbnish_penalties(pw)

    score = max(0, min(100, score))

    entropy = estimate_entropy_bits(pw)

    if score < 25 or entropy < 35:
        label = "Very weak"
    elif score < 50 or entropy < 50:
        label = "Weak"
    elif score < 75 or entropy < 65:
        label = "Average"
    else:
        label = "Strong!"

    if label != "Strong!":
        if length < 14:
            feedback.append("Target: 14–20 characters for robust security.")
        if class_count < 4:
            feedback.append("Use minimal three sign-groups. Four are ideal.")
        feedback.append("Don't use personal data or patterns, which are used often.")
        feedback.append("A passphrase with unnormal words is more secure.")
    else:
        feedback.append("Good: Length and Mixture are solide.")

    return {
        "score": score,
        "label": label,
        "entropy_bits": round(entropy, 2),
        "feedback": list(dict.fromkeys(feedback))  
    }

def draw():
    global level,y,target
    screen.clear()
    if level == -1:
        y=0
        screen.blit("title", (0, 0))
    elif level == 0:
        screen.blit("intro", (0, 0))
    elif level == 1:
        screen.blit("back", (0, 0))
        screen.draw.text("Enter your password:", center=(400, 130), fontsize=24, color=(25, 200, 255))
        screen.draw.text(target, center=(400, 180), fontsize=24, color=(255, 255, 0))
    elif level==2:
        result = strength_score(target)
        screen.draw.text(f"Score: {result['score']}", center=(400, 130), fontsize=24, color=(25, 200, 255))
        screen.draw.text(f"Rank: {result['label']}", center=(400, 180), fontsize=24, color=(25, 200, 255))
        screen.draw.text(f"Entropy: {result['entropy_bits']} Bits", center=(400, 230), fontsize=24, color=(25, 200, 255))
        screen.draw.text("Hints: ", center=(400, 280), fontsize=24, color=(25, 200, 255))
        y=0
        for tip in result["feedback"]:
            y+=1
            screen.draw.text(f"- {tip}", center=(400, 330+y*30), fontsize=24, color=(25, 200, 255))
    
def on_key_down(key, unicode=None):
    global level, target
    if key==keys.ESCAPE:
        pygame.quit()
    if key == keys.BACKSPACE:
        target = ""
    elif key == keys.RETURN and level == 1:
        level = 2
    elif unicode and key != keys.RETURN and level==1:
        target += unicode

def update():
    global level
    if (level == 0 or level==-2) and keyboard.RETURN:
        level +=1
    elif level == -1 and keyboard.space:
        level = 0
    elif level==2 and keyboard.space:
        level=0

pgzrun.go()

