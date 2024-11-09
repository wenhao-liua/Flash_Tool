import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import re
import threading
import os
import json
from datetime import datetime
import traceback  # 用于获取详细的错误信息

class FlashTool(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Flash Tool")
        self.geometry("900x600")

        self.selected_partitions = {}
        self.device_product = ""

        self.auto_select = tk.BooleanVar()
        self.auto_reboot = tk.BooleanVar()

        self.load_settings()

        self.check_create_log_directory()  # 检测并创建日志文件夹

        self.create_widgets()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.save_settings()
        self.destroy()

    def check_create_log_directory(self):
        log_dir = os.path.join(os.getcwd(), "刷机日志")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    def create_widgets(self):
        # 创建主框架
        main_frame = tk.Frame(self)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # 创建上部分框架（分区选择和日志显示）
        self.upper_frame = tk.Frame(main_frame)
        self.upper_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # 创建下部分框架（按钮）
        lower_frame = tk.Frame(main_frame)
        lower_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # 创建左右两个框架在上部分框架中
        self.left_frame = tk.Frame(self.upper_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame = tk.Frame(self.upper_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 创建左侧框架中的可滚动分区选择框架
        self.canvas = tk.Canvas(self.left_frame)
        scrollbar = tk.Scrollbar(self.left_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # 创建右侧框架中的日志显示区域
        self.log_text = tk.Text(right_frame, state="disabled", width=50, height=30)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 创建“选择刷机脚本”按钮
        load_button = tk.Button(lower_frame, text="选择刷机脚本", command=self.load_script)
        load_button.pack(side=tk.LEFT, padx=10, pady=10)

        # 创建“开始刷入”按钮
        flash_button = tk.Button(lower_frame, text="开始刷入", command=self.start_flash_thread)
        flash_button.pack(side=tk.RIGHT, padx=10, pady=10)
        # 创建“重启到fastboot”按钮
        reboot_button_fastboot = tk.Button(lower_frame, text="重启到fastboot", command=self.reboot_system_fastboot_thread)
        reboot_button_fastboot.pack(side=tk.RIGHT, padx=10, pady=10)
        # 创建“重启系统”按钮
        reboot_button = tk.Button(lower_frame, text="在fastboot重启到系统", command=self.reboot_system_thread)
        reboot_button.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # 创建“切换a分区”按钮
        switch_button = tk.Button(lower_frame, text="切换a分区", command=self.switch_to_a_partition_thread)
        switch_button.pack(side=tk.LEFT, padx=10, pady=10)

        # 创建输入命令的输入框
        self.command_entry = tk.Entry(lower_frame)
        self.command_entry.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.X, expand=True)
        self.command_entry.bind("<Return>", self.execute_command)

        # 创建“高级选项”按钮
        # advanced_button = tk.Button(lower_frame, text="高级选项", command=self.toggle_advanced_options)
        # advanced_button.pack(side=tk.RIGHT, padx=10, pady=10)

        # 创建“教程”按钮
        tutorial_button = tk.Button(lower_frame, text="教程", command=self.show_tutorial)
        tutorial_button.pack(side=tk.LEFT, padx=10, pady=10)

        # 创建高级选项框架
        # self.advanced_frame = tk.Frame(self)
        # advanced_label = tk.Label(self.advanced_frame, text="高级选项", font=("Helvetica", 14))
        # advanced_label.pack(pady=10)
        # advanced_option_1 = tk.Checkbutton(self.advanced_frame, text="自动勾选所有分区", variable=self.auto_select)
        # advanced_option_1.pack(anchor="w")
        # advanced_option_2 = tk.Checkbutton(self.advanced_frame, text="刷完后自动重启", variable=self.auto_reboot)
        # advanced_option_2.pack(anchor="w")

        # 创建“打开日志目录”按钮
        # open_log_button = tk.Button(self.advanced_frame, text="打开日志目录", command=self.open_log_directory)
        # open_log_button.pack(pady=10)

        # 默认情况下隐藏高级选项框架
        # self.advanced_frame.pack_forget()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def load_script(self):
        try:
            script_path = filedialog.askopenfilename(title="选择脚本文件", filetypes=[("批处理文件", "*.bat"), ("所有文件", "*.*")])
            if not script_path:
                return

            script_dir = os.path.dirname(script_path)
            subprocess.run([script_path])
            # with open(script_path, 'r') as file:
            #     script_content = file.read()

            # script_content = script_content.replace("%~dp0", script_dir + "\\")

            # match = re.search(r"fastboot %\* getvar product 2>&1 \| findstr /r /c:\"^product: *(\S+)\"", script_content)
            # if match:
            #     self.device_product = match.group(1)
            #     print(f"Found device product: {self.device_product}")

            # flash_commands = re.findall(r"fastboot %\* flash (\S+) (\S+)", script_content)

            # for widget in self.scrollable_frame.winfo_children():
            #     widget.destroy()

            # self.selected_partitions.clear()

            # for partition, file_path in flash_commands:
            #     abs_file_path = os.path.abspath(file_path)
            #     var = tk.BooleanVar(value=self.auto_select.get())
            #     self.selected_partitions[partition] = (var, abs_file_path)

            #     partition_frame = tk.Frame(self.scrollable_frame)
            #     partition_frame.pack(fill=tk.X, pady=5)

            #     checkbutton = tk.Checkbutton(partition_frame, text=partition, variable=var)
            #     checkbutton.pack(side=tk.LEFT, padx=5)

            #     change_button = tk.Button(partition_frame, text="更改路径", command=lambda p=partition: self.update_partition_path(p))
            #     change_button.pack(side=tk.RIGHT, padx=5)
        except Exception as e:
            messagebox.showerror("错误", f"加载脚本时出错: {str(e)}")

    def update_partition_path(self, partition):
        try:
            file_path = filedialog.askopenfilename(title=f"选择 {partition} 的刷入文件", filetypes=[("所有文件", "*.*")])
            if file_path:
                abs_file_path = os.path.abspath(file_path)
                self.selected_partitions[partition] = (self.selected_partitions[partition][0], abs_file_path)
        except Exception as e:
            messagebox.showerror("错误", f"更新分区路径时出错: {str(e)}")

    def start_flash_thread(self):
        try:
            self.log_text.config(state="normal")
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, "开始刷机\n")
            self.log_text.config(state="disabled")

            flash_thread = threading.Thread(target=self.flash_selected_partitions)
            flash_thread.start()
        except Exception as e:
            messagebox.showerror("错误", f"启动刷机线程时出错: {str(e)}")

    def flash_selected_partitions(self):
        try:
            log_filename = datetime.now().strftime("%Y%m%d%H%M%S") + "_刷机日志.log"
            log_path = os.path.join(os.getcwd(), "刷机日志", log_filename)

            with open(log_path, "w", encoding="utf-8") as log_file:
                if self.device_product:
                    command = "fastboot getvar product"
                    process = subprocess.run(command, shell=True, capture_output=True, text=True)
                    current_product = re.search(r"^product:\s*(\S+)", process.stdout, re.MULTILINE)
                    if not current_product or current_product.group(1)!= self.device_product:
                        message = f"设备产品不匹配。当前产品: {current_product.group(1) if current_product else '未知'}"
                        self.log_text.config(state="normal")
                        self.log_text.insert(tk.END, message + "\n")
                        self.log_text.see(tk.END)
                        self.log_text.config(state="disabled")
                        messagebox.showerror("错误", message)
                        return

                commands = []
                for partition, (var, file_path) in self.selected_partitions.items():
                    if var.get():
                        command = f"fastboot flash {partition} {file_path}"
                        commands.append((partition, command))

                if commands:
                    for partition, command in commands:
                        self.log_text.config(state="normal")
                        self.log_text.insert(tk.END, f"执行命令: {command}\n")
                        self.log_text.config(state="disabled")

                        process = subprocess.run(command, shell=True, capture_output=True, text=True)
                        log_file.write(process.stdout)
                        log_file.write(process.stderr)
                        log_file.write("\n\n")

                        self.log_text.config(state="normal")
                        self.log_text.insert(tk.END, process.stdout + "\n" + process.stderr + "\n\n")
                        self.log_text.see(tk.END)
                        self.log_text.config(state="disabled")

                    self.log_text.config(state="normal")
                    self.log_text.insert(tk.END, "刷机完成\n")
                    self.log_text.see(tk.END)
                    self.log_text.config(state="disabled")
                    self.reboot_system_thread()

                else:
                    self.log_text.config(state="normal")
                    self.log_text.insert(tk.END, "没有选中任何分区\n")
                    self.log_text.see(tk.END)
                    self.log_text.config(state="disabled")
        except Exception as e:
            error_message = f"刷机过程中出错: {str(e)}\n{traceback.format_exc()}"  # 打印详细的错误跟踪信息
            self.log_text.config(state="normal")
            self.log_text.insert(tk.END, error_message + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state="disabled")
            messagebox.showerror("错误", error_message)

    def reboot_system_thread(self):
        try:
            reboot_thread = threading.Thread(target=self.reboot_system)
            reboot_thread.start()
        except Exception as e:
            messagebox.showerror("错误", f"启动重启线程时出错: {str(e)}")
    
    def reboot_system_fastboot(self):
            try:
                self.log_text.config(state="normal")
                self.log_text.insert(tk.END, "重启到fastboot\n")
                self.log_text.config(state="disabled")

                command = "adb reboot bootloader"
                process = subprocess.run("adb reboot bootloader")
                self.log_text.config(state="normal")
                self.log_text.insert(tk.END, f"执行命令: {command}\n")
                self.log_text.insert(tk.END, process.stdout + "\n" + process.stderr + "\n\n")
                self.log_text.see(tk.END)
                self.log_text.config(state="disabled")
            except Exception as e:
                pass
                # messagebox.showerror("错误", f"重启系统时出错: {str(e)}")

    def reboot_system_fastboot_thread(self):
        try:
            reboot_thread = threading.Thread(target=self.reboot_system_fastboot)
            reboot_thread.start()
        except Exception as e:
            messagebox.showerror("错误", f"启动重启线程时出错: {str(e)}")

    def reboot_system(self):
        try:
            self.log_text.config(state="normal")
            self.log_text.insert(tk.END, "在fastboot重启到系统\n")
            self.log_text.config(state="disabled")

            command = "fastboot reboot"
            process = subprocess.run("fastboot reboot")
            self.log_text.config(state="normal")
            self.log_text.insert(tk.END, f"执行命令: {command}\n")
            self.log_text.insert(tk.END, process.stdout + "\n" + process.stderr + "\n\n")
            self.log_text.see(tk.END)
            self.log_text.config(state="disabled")
        except Exception as e:
            pass
            # messagebox.showerror("错误", f"重启系统时出错: {str(e)}")
        

    def switch_to_a_partition_thread(self):
        try:
            switch_thread = threading.Thread(target=self.switch_to_a_partition)
            switch_thread.start()
        except Exception as e:
            messagebox.showerror("错误", f"启动切换分区线程时出错: {str(e)}")

    def switch_to_a_partition(self):
        try:
            self.log_text.config(state="normal")
            self.log_text.insert(tk.END, "切换到a分区\n")
            self.log_text.config(state="disabled")

            command = "fastboot set_active a"
            process = subprocess.run(command, shell=True, capture_output=True, text=True)
            self.log_text.config(state="normal")
            self.log_text.insert(tk.END, f"执行命令: {command}\n")
            self.log_text.insert(tk.END, process.stdout + "\n" + process.stderr + "\n\n")
            self.log_text.see(tk.END)
            self.log_text.config(state="disabled")
        except Exception as e:
            messagebox.showerror("错误", f"切换分区时出错: {str(e)}")

    def execute_command(self, event):
        try:
            command = self.command_entry.get()
            self.command_entry.delete(0, tk.END)
            self.log_text.config(state="normal")
            self.log_text.insert(tk.END, f"执行命令: {command}\n")
            self.log_text.config(state="disabled")

            process = subprocess.run(command, shell=True, capture_output=True, text=True)
            self.log_text.config(state="normal")
            self.log_text.insert(tk.END, process.stdout + "\n" + process.stderr + "\n\n")
            self.log_text.see(tk.END)
            self.log_text.config(state="disabled")
        except Exception as e:
            messagebox.showerror("错误", f"执行自定义命令时出错: {str(e)}")

    def toggle_advanced_options(self):
        if self.advanced_frame.winfo_ismapped():
            self.advanced_frame.pack_forget()
        else:
            self.advanced_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def open_log_directory(self):
        log_dir = os.path.join(os.getcwd(), "刷机日志")
        if os.path.exists(log_dir):
            subprocess.Popen(['explorer', log_dir])

    def save_settings(self):
        try:
            settings = {
                "auto_select": self.auto_select.get(),
                "auto_reboot": self.auto_reboot.get()
            }
            settings_file = os.path.join(os.getcwd(), "settings.json")
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f)
        except Exception as e:
            messagebox.showerror("错误", f"保存设置时出错: {str(e)}")

    def load_settings(self):
        try:
            settings_file = os.path.join(os.getcwd(), "settings.json")
            if os.path.exists(settings_file):
                with open(settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    self.auto_select.set(settings.get("auto_select", False))
                    self.auto_reboot.set(settings.get("auto_reboot", False))
            else:
                # 如果 settings.json 文件不存在，创建一个新文件并保存默认设置
                print(f"Settings file '{settings_file}' does not exist. Creating default settings.")
                self.save_settings()  # 保存默认设置到新创建的文件
        except Exception as e:
            messagebox.showerror("错误", f"加载设置时出错: {str(e)}")

    def show_tutorial(self):
        tutorial_window = tk.Toplevel(self)
        tutorial_window.title("刷机工具教程")

        tutorial_label = tk.Label(tutorial_window, text="""
        以下是本刷机工具的使用教程：
        1. 点击“选择刷机脚本”按钮，选择您的刷机脚本文件。
        2. 脚本加载后，界面将显示分区信息，您可以选择要刷入的分区，并可更改分区文件路径。
        3. 勾选“高级选项”中的“自动勾选所有分区”和“刷完后自动重启”，根据您的需求进行设置。
        4. 点击“开始刷入”按钮开始刷机过程，刷机日志将显示在右侧区域。
        5. 您还可以通过“重启系统”和“切换a分区”按钮执行相应操作。
        6. 在输入框中输入命令并按回车键，可执行自定义命令。
        """, justify="left")
        tutorial_label.pack(padx=10, pady=10)
if __name__ == "__main__":
    app = FlashTool()
    app.mainloop()