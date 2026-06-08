import os


# 网络控制类
class NetworkController:

    @staticmethod
    def disable_wifi():
        os.system("adb shell svc wifi disable")

    @staticmethod
    def enable_wifi():
        os.system("adb shell svc wifi enable")

    @staticmethod
    def airplane_on():
        os.system("adb shell settings put global airplane_mode_on 1")
        os.system("adb shell am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true")

    @staticmethod
    def airplane_off():
        os.system("adb shell settings put global airplane_mode_on 0")
        os.system("adb shell am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false")