import subprocess
import sys
import os
import threading
import time

def run_bot():
    """تشغيل البوت"""
    subprocess.run([sys.executable, "bot.py"])

def run_admin():
    """تشغيل لوحة التحكم"""
    subprocess.run([sys.executable, "admin.py"])

if __name__ == "__main__":
    # تشغيل كل منهما في عملية منفصلة
    bot_thread = threading.Thread(target=run_bot)
    admin_thread = threading.Thread(target=run_admin)
    
    bot_thread.start()
    admin_thread.start()
    
    # الانتظار حتى انتهاء إحداهما (نظرياً لن تنتهي)
    bot_thread.join()
    admin_thread.join()