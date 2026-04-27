import subprocess
import sys
import time

if __name__ == "__main__":
    print("🚀 تشغيل البوت ولوحة التحكم...")
    
    # تشغيل Flask (لوحة التحكم) على منفذ 10001
    admin_process = subprocess.Popen([sys.executable, "admin.py"])
    print("✅ لوحة التحكم تعمل على المنفذ 10001")
    
    time.sleep(3)
    
    # تشغيل البوت
    bot_process = subprocess.Popen([sys.executable, "bot.py"])
    print("✅ البوت يعمل")
    
    bot_process.wait()
    admin_process.wait()
