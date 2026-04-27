import subprocess
import sys
import os
import time

if __name__ == "__main__":
    print("🚀 تشغيل البوت ولوحة التحكم...")
    
    # تشغيل لوحة التحكم (Flask) في الخلفية
    admin_process = subprocess.Popen([sys.executable, "admin.py"])
    print("✅ لوحة التحكم تعمل على المنفذ 5000")
    
    # انتظار 5 ثوانٍ ليتأكد تشغيل لوحة التحكم
    time.sleep(5)
    
    # تشغيل البوت
    bot_process = subprocess.Popen([sys.executable, "bot.py"])
    print("✅ البوت يعمل")
    
    # الانتظار حتى انتهاء أي عملية
    bot_process.wait()
    admin_process.wait()