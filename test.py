from airtest.core import android as andr
from tkinter import filedialog
from lxml import etree
from io import StringIO
from tkinter import messagebox
import multiprocessing
import cv2
import re
import numpy as np
import tkinter as tk


class Config(tk.Toplevel):
    def __init__(self, original):
        tk.Toplevel.__init__(self)
        self.original_frame = original
        self.master.protocol("WM_DELETE_WINDOW", self.on_destroy)
        self.grid()
        self.initUI()

    def on_destroy(self):
        if messagebox.askokcancel("Quit", "Do u want to save config?"):
            print("action on destr")
        else:
            print("no")
            self.quit()

    def save_and_quit(self):
        self.database = self.e2txt.get()
        self.group_name = self.e1txt.get()
        self.destroy()
        self.original_frame.config = {"database": self.database, "group_name":self.group_name}
        self.original_frame.show()

    def onClose(self):
        """"""
        self.destroy()
        self.original_frame.show()

    def browsefile(self, e):
        filepath = filedialog.askopenfilename(initialdir=".", title="Select file",
                                           filetypes=(("config file", "*.json"), ("all files", "*.*")))
        self.e2txt.set(filepath)
        self.database=filepath

    def initUI(self):
        self.master.title("Config")
        self.database = ''
        self.group_name =''

        group_name = tk.Label(self, text="group name")
        database_file = tk.Label(self, text="database file:")
        group_name.grid(row=0)
        database_file.grid(row=1)

        self.e1txt = tk.StringVar()
        self.e2txt = tk.StringVar()

        e1 = tk.Entry(self,textvariable=self.e1txt)
        e2 = tk.Entry(self, textvariable=self.e2txt)
        e1.grid(row=0, column=1)
        e2.grid(row=1, column=1)
        e2.bind("<ButtonPress>", self.browsefile)

        save = tk.Button(self, text="save and back to main window", command=lambda: self.save_and_quit())
        back = tk.Button(self, text="back", command=lambda:self.onClose())

        save.grid(row=2, column=0)
        back.grid(row=2, column=1)


shared_screen = "Screen Mirror"

class Window:
    def __init__(self):
        self.root = tk.Tk()
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.config = {}

        self.device = None
        self.best_aspect_ration = None

        self.menue_frame = tk.Frame(self.root)
        self.__build_frame()
        self.__build_status_bar()

        self.menue_frame.grid(row=0, column=0, sticky=tk.N + tk.S + tk.E + tk.W, columnspan=2)

        self.is_mirror = False
        self.zoom_in = 0

    def __build_frame(self):
        self.refresh_btn = tk.Button(self.menue_frame, text="Refresh", command=lambda: self.__connection_status())
        self.refresh_btn.grid(row=0,  sticky=tk.N + tk.S + tk.E + tk.W)

        self.mirrow_screen_textvar = tk.StringVar()
        self.mirrow_screen_textvar.set("Show screen")

        self.show_screen_btn = tk.Button(self.menue_frame, textvariable=self.mirrow_screen_textvar)
        self.show_screen_btn.config(command=lambda: self.__show_screen(), state=tk.DISABLED)
        self.show_screen_btn.grid(row=1, sticky=tk.N + tk.S + tk.E + tk.W)

        self.show_running = tk.Button(self.menue_frame, text="show process")
        self.show_running.config(state=tk.DISABLED)
        self.show_running.grid(row=2,sticky=tk.N + tk.S + tk.E + tk.W)

        self.record_action_text = tk.StringVar()
        self.record_action_text.set("record action")
        self.record_action = tk.Button(self.menue_frame, textvariable=self.record_action_text)
        self.record_action.config(state=tk.DISABLED)
        self.record_action.grid(row=3, sticky=tk.N + tk.S + tk.E + tk.W)

        self.config_btn = tk.Button(self.menue_frame, text="configuration", command=lambda: self.on_config())
        self.config_btn.grid(row=4, sticky=tk.N + tk.S + tk.E + tk.W)


        columns, rows = self.root.grid_size()
        for x in range(columns):
            self.menue_frame.grid_columnconfigure(x, weight=1)
        for y in range(rows):
            self.menue_frame.grid_rowconfigure(y, weight=1)

    def on_config(self):
        self.root.withdraw()
        subFrame = Config(self)

    def show(self):
        self.root.update()
        self.root.deiconify()

    def hide_screen(self):
        self.is_mirror = False

    def calc_aspect(self):
        device_data = self.device.display_info

        screen = (self.root.winfo_screenwidth(), self.root.winfo_screenheight())
        screen_android = (device_data['width'], device_data['height'])

        min_h = min(screen[1], screen_android[1])
        min_w = min(screen[0], screen_android[0])
        best_ration = min(min_w / screen_android[0], min_h / screen_android[1])

        if screen[0] > screen_android[0] and screen[1] > screen_android[1]:
            return 1

        return best_ration

    def __show_screen(self):
        self.is_mirror = not self.is_mirror
        self.mirrow_screen_textvar.set("Hide Screen")
        self.show_screen_btn.config(command=lambda: self.hide_screen())
        if self.is_mirror:
            for stream in self.device.minicap.get_stream():
                # here might be a bug in the library so that it consume all the stream and stops, in new re
                if not self.is_mirror:
                    cv2.destroyAllWindows()
                    break
                if cv2.waitKey(43):
                    self.zoom_in = self.zoom_in+1

                img = cv2.imdecode(np.frombuffer(stream, np.uint8), -1)
                img = cv2.resize(img, (0, 0), fx=0.7, fy=0.7)
                cv2.imshow(shared_screen, img)
                self.root.update()

        self.show_screen_btn.config(command=lambda: self.__show_screen())
        self.mirrow_screen_textvar.set("Show screen")



    def __build_status_bar(self):
        columns, rows = self.root.grid_size()

        self.label = tk.Label(self.root, text="device status", relief=tk.FLAT)
        self.label.grid(row=rows)

        self.device_status = tk.StringVar()
        self.device_status.set("not connected")
        self.device_status_label = tk.Label(textvariable=self.device_status, relief=tk.FLAT)
        self.device_status_label.config(background="gray", state=tk.DISABLED)
        self.device_status_label.grid(row=rows, column=columns, sticky='nsew')


    def run(self):
        self.root.mainloop()

    def __connection_status(self):
        try:
            if not self.device:
                self.device = andr.android.Android()
                self.best_aspect_ration = self.calc_aspect()

            device_model = self.device.adb.devices()
            if device_model:
                self.device_status.set(device_model[0])
                self.device_status_label.config(background="green")

                self.record_action.config(state="normal")
                self.show_screen_btn.config(state="normal")
                self.show_running.config(state="normal")
        except:
                self.device_status.set("not found")
                self.device_status_label.config(background="red")


    def extract_metadata(self):
        parser = etree.XMLParser(recover=True, encoding='utf-8')
        stream = self.device.shell("uiautomator dump  && cat /sdcard/window_dump.xml").\
            split("<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>")[1]
        xml = etree.parse(StringIO(stream), parser)
        return xml

    def device_up(self):
        self.device.keyevent('POWER')
        xml = self.extract_metadata()
        lockWindowBounds = xml.xpath('//*[@resource-id="com.android.keyguard:id/keyguard_selector_view_frame"]')[0].get('bounds')
        lockWindowBounds = boundary = list(map(int, re.findall('\d+', lockWindowBounds)))

        data = dict(zip(['left', 'bottom','right','top'], lockWindowBounds))
        startPoint_x = (data['right'] + data['left']) / 2
        startPoint_y = (data['bottom'] + data['top']) / 2
        self.device.swipe((startPoint_x, startPoint_y), (data['right'], startPoint_y))

window = Window()
window.run()
