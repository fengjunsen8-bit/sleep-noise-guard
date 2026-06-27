import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from sleep_noise_guard.audio import MicrophoneLevelStream
from sleep_noise_guard.monitor import MonitorService
from sleep_noise_guard.noise_log import NoiseLogger
from sleep_noise_guard.player import SoundPlayer
from sleep_noise_guard.policy import NoisePolicy
from sleep_noise_guard.sound_library import SoundLibrary


class WindowsDesktopApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("睡眠噪音守卫")
        self.geometry("980x680")
        self.minsize(900, 620)
        self.configure(bg="#f6f8fb")

        self.service = None
        self.worker = None
        self.updates = queue.Queue()

        self.threshold = tk.StringVar(value="45")
        self.duration = tk.StringVar(value="")
        self.noise_events = tk.StringVar(value="")
        self.feedback_repeats = tk.StringVar(value="")
        self.cooldown = tk.StringVar(value="60")
        self.calibration = tk.StringVar(value="94")
        self.input_device = tk.StringVar(value="")
        self.output_device = tk.StringVar(value="")
        self.sounds_dir = tk.StringVar(value="sounds")
        self.log_path = tk.StringVar(value="logs/noise_events.csv")

        self.status = tk.StringVar(value="就绪")
        self.current_db = tk.StringVar(value="--")
        self.dbfs = tk.StringVar(value="--")
        self.trigger_count = tk.StringVar(value="0")
        self.last_sound = tk.StringVar(value="暂无")
        self.hour_noise = tk.StringVar(value="0")
        self.hour_triggers = tk.StringVar(value="0")
        self.day_noise = tk.StringVar(value="0")
        self.day_triggers = tk.StringVar(value="0")

        self._configure_style()
        self._build()
        self.after(150, self._drain_updates)

    def _configure_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f6f8fb")
        style.configure("Panel.TFrame", background="#ffffff")
        style.configure("TLabel", background="#f6f8fb", foreground="#20242c", font=("Microsoft YaHei UI", 10))
        style.configure("Panel.TLabel", background="#ffffff", foreground="#20242c", font=("Microsoft YaHei UI", 10))
        style.configure("Title.TLabel", background="#f6f8fb", foreground="#20242c", font=("Microsoft YaHei UI", 22, "bold"))
        style.configure("Metric.TLabel", background="#ffffff", foreground="#20242c", font=("Segoe UI", 52, "bold"))
        style.configure("TButton", font=("Microsoft YaHei UI", 10), padding=(12, 7))
        style.configure("Primary.TButton", background="#1677ff", foreground="#ffffff")
        style.configure("TEntry", padding=7)

    def _build(self):
        root = ttk.Frame(self, padding=22)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=3)
        root.columnconfigure(1, weight=2)
        root.rowconfigure(1, weight=1)

        header = ttk.Frame(root)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="睡眠噪音守卫", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, textvariable=self.status).grid(row=0, column=1, sticky="e")

        meter = ttk.Frame(root, style="Panel.TFrame", padding=20)
        meter.grid(row=1, column=0, sticky="nsew", padx=(0, 16))
        meter.columnconfigure(0, weight=1)

        ttk.Label(meter, text="当前噪音", style="Panel.TLabel").grid(row=0, column=0, sticky="w")
        metric = ttk.Frame(meter, style="Panel.TFrame")
        metric.grid(row=1, column=0, sticky="ew", pady=(10, 12))
        ttk.Label(metric, textvariable=self.current_db, style="Metric.TLabel").pack(side="left")
        ttk.Label(metric, text="估算分贝", style="Panel.TLabel").pack(side="left", padx=14, pady=(42, 0))

        self.bar = ttk.Progressbar(meter, maximum=90, value=0)
        self.bar.grid(row=2, column=0, sticky="ew", pady=(0, 16))

        stats = ttk.Frame(meter, style="Panel.TFrame")
        stats.grid(row=3, column=0, sticky="ew")
        for i in range(4):
            stats.columnconfigure(i, weight=1)
        self._stat(stats, "触发次数", self.trigger_count, 0)
        self._stat(stats, "本小时噪音", self.hour_noise, 1)
        self._stat(stats, "今日噪音", self.day_noise, 2)
        self._stat(stats, "今日触发", self.day_triggers, 3)

        stats2 = ttk.Frame(meter, style="Panel.TFrame")
        stats2.grid(row=4, column=0, sticky="ew", pady=(12, 0))
        for i in range(3):
            stats2.columnconfigure(i, weight=1)
        self._stat(stats2, "上次音效", self.last_sound, 0)
        self._stat(stats2, "dBFS", self.dbfs, 1)
        self._stat(stats2, "本小时触发", self.hour_triggers, 2)

        actions = ttk.Frame(meter, style="Panel.TFrame")
        actions.grid(row=5, column=0, sticky="ew", pady=(18, 0))
        self.start_button = ttk.Button(actions, text="开始监听", style="Primary.TButton", command=self.start)
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(actions, text="停止", command=self.stop, state="disabled")
        self.stop_button.pack(side="left", padx=10)
        ttk.Button(actions, text="测试音效", command=self.test_sound).pack(side="left")

        self.log_box = tk.Text(meter, height=9, bg="#ffffff", fg="#5b6472", relief="flat", font=("Consolas", 9))
        self.log_box.grid(row=6, column=0, sticky="nsew", pady=(18, 0))
        meter.rowconfigure(6, weight=1)

        settings = ttk.Frame(root, style="Panel.TFrame", padding=18)
        settings.grid(row=1, column=1, sticky="nsew")
        settings.columnconfigure(1, weight=1)
        ttk.Label(settings, text="设置", style="Panel.TLabel", font=("Microsoft YaHei UI", 16, "bold")).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))
        fields = [
            ("噪音阈值 dB", self.threshold),
            ("出现几秒后触发", self.duration),
            ("出现几次后触发", self.noise_events),
            ("每次反馈播放次数", self.feedback_repeats),
            ("冷却时间 秒", self.cooldown),
            ("校准偏移", self.calibration),
            ("输入设备", self.input_device),
            ("输出设备", self.output_device),
            ("日志路径", self.log_path),
            ("音效目录", self.sounds_dir),
        ]
        for row, (label, variable) in enumerate(fields, start=1):
            ttk.Label(settings, text=label, style="Panel.TLabel").grid(row=row, column=0, sticky="w", pady=5)
            ttk.Entry(settings, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=5)
            if label == "音效目录":
                ttk.Button(settings, text="浏览", command=self.choose_sounds).grid(row=row, column=2, padx=(8, 0))
        ttk.Label(
            settings,
            text="出现几秒、出现几次、播放次数留空时，监测到噪音就反馈一次。",
            style="Panel.TLabel",
            wraplength=300,
        ).grid(row=len(fields) + 1, column=0, columnspan=3, sticky="ew", pady=(14, 0))

    def _stat(self, parent, title, variable, column):
        frame = ttk.Frame(parent, style="Panel.TFrame", padding=10)
        frame.grid(row=0, column=column, sticky="ew", padx=4)
        ttk.Label(frame, text=title, style="Panel.TLabel").pack(anchor="w")
        ttk.Label(frame, textvariable=variable, style="Panel.TLabel", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w")

    def choose_sounds(self):
        directory = filedialog.askdirectory(initialdir=self.sounds_dir.get() or ".")
        if directory:
            self.sounds_dir.set(directory)

    def _optional_float(self, value):
        return float(value) if value.strip() else None

    def _optional_int(self, value):
        return int(value) if value.strip() else None

    def start(self):
        try:
            library = SoundLibrary(Path(self.sounds_dir.get() or "sounds"))
            if not library.files():
                messagebox.showerror("没有音效", "音效目录中没有可播放文件")
                return
            policy = NoisePolicy(
                threshold_db=float(self.threshold.get()),
                min_duration_seconds=self._optional_float(self.duration.get()),
                cooldown_seconds=float(self.cooldown.get()),
                min_noise_events=self._optional_int(self.noise_events.get()),
            )
            service = MonitorService(
                policy=policy,
                library=library,
                player=SoundPlayer(output_device=self.output_device.get().strip() or None),
                logger=NoiseLogger(Path(self.log_path.get() or "logs/noise_events.csv")),
                feedback_repeats=self._optional_int(self.feedback_repeats.get()),
            )
            stream = MicrophoneLevelStream(
                input_device=self.input_device.get().strip() or None,
                calibration_offset_db=float(self.calibration.get()),
            )
        except Exception as exc:
            messagebox.showerror("启动失败", str(exc))
            return

        self.service = service
        self.worker = threading.Thread(target=service.run, kwargs={"stream": stream, "on_update": self.updates.put}, daemon=True)
        self.worker.start()
        self.status.set("监听中")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")

    def stop(self):
        if self.service:
            self.service.stop()
        self.status.set("正在停止")

    def test_sound(self):
        try:
            sound = SoundLibrary(Path(self.sounds_dir.get() or "sounds")).next_sound()
            SoundPlayer(output_device=self.output_device.get().strip() or None).play(sound)
            self.last_sound.set(sound.name)
        except Exception as exc:
            messagebox.showerror("播放失败", str(exc))

    def _drain_updates(self):
        while True:
            try:
                state = self.updates.get_nowait()
            except queue.Empty:
                break
            self._apply_state(state)
        self.after(150, self._drain_updates)

    def _apply_state(self, state):
        if state.current_db is not None:
            self.current_db.set(f"{state.current_db:.1f}")
            self.dbfs.set(f"{state.current_dbfs:.1f}")
            self.bar.configure(value=max(0, min(90, state.current_db)))
        self.trigger_count.set(str(state.trigger_count))
        self.hour_noise.set(str(state.hourly_noise_count))
        self.hour_triggers.set(str(state.hourly_trigger_count))
        self.day_noise.set(str(state.daily_noise_count))
        self.day_triggers.set(str(state.daily_trigger_count))
        if state.last_sound:
            self.last_sound.set(state.last_sound.name)
        if state.error:
            self.status.set("错误")
            self._log(state.error)
        elif not state.running and self.service:
            self.status.set("已停止")
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")

    def _log(self, line):
        self.log_box.insert("end", line + "\n")
        self.log_box.see("end")


def main():
    app = WindowsDesktopApp()
    app.mainloop()


if __name__ == "__main__":
    main()
