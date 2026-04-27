import subprocess
import sys
import time
import threading

if __name__ == "__main__":
    print("🚀 تشغيل البوت ولوحة التحكم...")
    
    # تشغيل لوحة التحكم (المنفذ 10000)
    admin_process = subprocess.Popen([sys.executable, "admin.py"])
    print("✅ لوحة التحكم تعمل")
    
    time.sleep(3)
    
    # تشغيل البوت
    bot_process = subprocess.Popen([sys.executable, "bot.py"])
    print("✅ البوت يعمل")
    
    bot_process.wait()
    admin_process.wait()
