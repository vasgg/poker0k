from enum import Enum


class Coords(Enum):
    ANDROID_ME_SECTION = (1100, 865)
    ANDROID_CASHIER_BUTTON = (1346, 316)
    ANDROID_CASHIER_SETTINGS = (1075, 277)
    ANDROID_TRANSFER_SECTION = (1165, 460)
    ANDROID_NICKNAME_SECTION = (1350, 360)
    ANDROID_AMOUNT_SECTION = (1350, 530)
    ANDROID_CLOSE_CASHIER_BUTTON = (1435, 218)

    LOGIN_BUTTON = (1710, 435)
    CONFIRM_LOGIN_BUTTON = (1145, 550)
    RESTART_BUTTON = (0, 0)
    CLOSE_AD_BUTTON = (1005, 325)
    CASHIER_BUTTON = (1741, 423)
    NEXT_SECTION_BUTTON = (680, 235)
    HOME_SECTION_BUTTON = (615, 230)
    CLOSE_CASHIER_BUTTON = (1642, 32)
    CASHIER_FULLSCREEN_BUTTON = (1555, 145)

    TRANSFER_SECTION = (570, 158)
    NICKNAME_SECTION = (450, 275)
    AMOUNT_SECTION = (500, 480)
    TRANSFER_BUTTON = (500, 555)
    TRANSFER_CONFIRM_BUTTON = (1000, 630)
    CONFIRM_TRANSFER_SECTION = (760, 195)
    TRANSFER_HISTORY_SECTION = (0, 0)


class Colors:
    LIGHT_GREEN = 57, 132, 95
    DARK_GREEN = 44, 98, 71
    GRAY = 181, 181, 181
    RUST = 152, 61, 61
    WHITE = 245, 255, 235
    FINAL_GREEN = 206, 234, 214
    RED = 189, 63, 60
    MENU_RED = 89, 0, 0

    ANDROID_RUST = 255, 48, 48
    ANDROID_RED = 136, 21, 22
    ANDROID_GREEN = 68, 143, 105
