import ctypes, sys
import PySimpleGUI as sg
import mdt_service as service
import pyperclip
import configparser

config_file = "config.ini"
font_size = 12
window_alpha = 0.96
keep_on_top = True
cfg = configparser.ConfigParser()
sync_ui = 0


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def uac_reload():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()


def config_load():
    global font_size
    global window_alpha
    global keep_on_top
    global cfg
    try:
        cfg.read(config_file, encoding="utf-8")
        config = cfg.items("gui")
        config = dict(config)
        font_size = int(config["font_size"])
        window_alpha = float(config["window_alpha"])
        keep_on_top = bool(config["keep_on_top"])
    except:
        print(f"未找到{config_file}配置文件或配置文件格式有误。")


def config_set(option: str, value: str):
    cfg.set("gui", option, value)
    with open(config_file, "w+") as f:
        cfg.write(f)


def main():
    uac_reload()
    service.start()
    config_load()
    cards_db = None
    cid_temp = 0
    text_keys = ["-cn_name-", "-pdesc-", "-desc-", "-types-", "-en_name-", "-jp_name-"]
    option_slider = [
        [
            sg.Slider(
                key="-window_alpha-",
                range=[0.15, 1],
                default_value=0.96,
                resolution=0.01,
                orientation="horizontal",
                disable_number_display=True,
                enable_events=True,
                tooltip="调整透明度",
            )
        ],
        [
            sg.Slider(
                key="-font_size-",
                range=(6, 25),
                default_value=12,
                resolution=1,
                orientation="horizontal",
                disable_number_display=True,
                enable_events=True,
                tooltip="调整字体大小",
            )
        ],
    ]
    option_checkbox = [
        [sg.Checkbox(key="-keep_on_top-", text="置顶", default=True, enable_events=True)],
        [
            sg.Checkbox(
                key="-restore_default-",
                text="恢复默认并锁定",
                default=False,
                enable_events=True,
            )
        ],
    ]
    card_frame = [
        [
            sg.Frame(
                "卡名",
                [
                    [
                        sg.T(
                            text="等待检测",
                            key="-cn_name-",
                            s=(38, None),
                            enable_events=True,
                        )
                    ],
                ],
                title_color="#61E7DC",
            )
        ],
        [
            sg.pin(
                sg.Frame(
                    "灵摆",
                    [
                        [
                            sg.Multiline(
                                key="-pdesc-",
                                s=(40, 5),
                                background_color="#64778D",
                                text_color="white",
                                write_only=True,
                            )
                        ],
                    ],
                    title_color="#61E7DC",
                    visible=False,
                    key="-pdesc_frame-",
                )
            )
        ],
        [
            sg.Frame(
                "效果",
                [
                    [
                        sg.Multiline(
                            key="-desc-",
                            s=(40, 10),
                            background_color="#64778D",
                            text_color="white",
                            write_only=True,
                        )
                    ]
                ],
                title_color="#61E7DC",
            )
        ],
        [
            sg.Frame(
                "类型",
                [
                    [sg.T(key="-types-", s=(38, None), enable_events=True)],
                ],
                title_color="#61E7DC",
            )
        ],
        [
            sg.Frame(
                "英文名",
                [
                    [sg.T(key="-en_name-", s=(38, None), enable_events=True)],
                ],
                title_color="#61E7DC",
            )
        ],
        [
            sg.Frame(
                "日文名",
                [
                    [sg.T(key="-jp_name-", s=(38, None), enable_events=True)],
                ],
                title_color="#61E7DC",
            )
        ],
    ]

    layout = [[card_frame], [sg.Column(option_slider), sg.Column(option_checkbox)]]

    window = sg.Window(
        "MDT v0.2.1 @SkywalkerJi GPLv3",
        layout,
        default_element_size=(12, 1),
        font=("Microsoft YaHei", font_size),
        keep_on_top=bool(keep_on_top),
        resizable=True,
        alpha_channel=window_alpha,
    )

    while True:
        global sync_ui
        event, values = window.read(timeout=1000)
        cid = service.get_cid()
        # print(event, values)
        if sync_ui == 0:
            window["-keep_on_top-"].update(value=bool(keep_on_top))
            window["-window_alpha-"].update(value=window_alpha)
            window["-font_size-"].update(value=font_size)
            sync_ui = 1
        if not cards_db:
            cards_db = service.get_cards_db()
        if cid != cid_temp:
            cid_temp = cid
            try:
                card_t = cards_db[str(cid)]
                window["-cn_name-"].update(card_t["cn_name"])
                window["-en_name-"].update(card_t["en_name"])
                window["-jp_name-"].update(card_t["jp_name"])
                window["-types-"].update(card_t["text"]["types"])
                if card_t["text"]["pdesc"]:
                    window["-pdesc_frame-"].update(visible=True)
                    window["-pdesc-"].update(card_t["text"]["pdesc"])
                else:
                    window["-pdesc_frame-"].update(visible=False)
                window["-desc-"].update(card_t["text"]["desc"])
            except:
                print("数据库中未查到该卡")
        if event in (sg.WIN_CLOSED, "Exit"):
            break
        elif event in ("-en_name-", "-cn_name-", "-jp_name-", "-types-"):
            pyperclip.copy(window[event].get())
        # 透明度滑块
        elif event == "-window_alpha-":
            window.set_alpha(values["-window_alpha-"])
            config_set("window_alpha", str(values["-window_alpha-"]))
        # 字体滑块
        elif event == "-font_size-":
            for key in text_keys:
                window[key].update(font=("Microsoft YaHei", int(values["-font_size-"])))
            config_set("font_size", str(int(values["-font_size-"])))
        # 置顶选项
        elif event == "-keep_on_top-":
            if values["-keep_on_top-"] == True:
                window.keep_on_top_set()
            elif values["-keep_on_top-"] == False:
                window.keep_on_top_clear()
            config_set("keep_on_top", str(int(values["-keep_on_top-"])))
        # 恢复默认
        elif event == "-restore_default-":
            if values["-restore_default-"] == True:
                window.keep_on_top_set()
                window["-keep_on_top-"].update(value=True, disabled=True)
                window.set_alpha(0.96)
                window["-window_alpha-"].update(value=0.96, disabled=True)
                for key in text_keys:
                    window[key].update(font=("Microsoft YaHei", 12))
                window["-font_size-"].update(value=12.0, disabled=True)
                config_set("keep_on_top", "1")
                config_set("font_size", "12")
                config_set("window_alpha", "0.96")
            else:
                window["-window_alpha-"].update(disabled=False)
                window["-keep_on_top-"].update(disabled=False)
                window["-font_size-"].update(disabled=False)
    service.exit()
    window.close()


if __name__ == "__main__":
    main()
