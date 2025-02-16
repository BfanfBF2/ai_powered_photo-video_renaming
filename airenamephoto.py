import base64
import time
from zhipuai import ZhipuAI
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import subprocess
from datetime import datetime
import threading
from PIL import Image
import io


def compress_image(image_path, max_size=1 * 1024 * 1024):
    """
    压缩图片到指定大小以内
    :param image_path: 图片文件的路径
    :param max_size: 最大允许的文件大小（字节），默认为1MB
    :return: 压缩后图片的Base64编码字符串
    """
    img = Image.open(image_path)
    quality = 90
    while True:
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=quality)
        buffer.seek(0)
        data = buffer.read()
        if len(data) <= max_size or quality < 10:
            break
        quality -= 10
    encoded_string = base64.b64encode(data).decode('utf-8')
    return encoded_string


def get_image_description(img_path, api_key, prompt):
    client = ZhipuAI(api_key=api_key)
    img_base = compress_image(img_path)

    # 记录开始时间
    start_time = time.time()

    try:
        response = client.chat.completions.create(
            model="glm-4v-plus",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": img_base
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        # 记录结束时间
        end_time = time.time()
        # 计算耗时
        elapsed_time = end_time - start_time
        print(f"请求耗时: {elapsed_time:.2f} 秒")
        return response.choices[0].message.content
    except Exception as e:
        print(f"调用API时发生错误: {e}")
        return None


class PhotoRenamerApp:
    def __init__(self, master):
        self.master = master
        master.title("照片EXIF重命名工具")
        master.geometry("800x700")

        # 创建界面组件
        self.create_widgets()
        self.selected_dir = ""
        self.total_files = 0
        self.cancel_flag = False
        self.api_key = ""
        self.ai_prompt = ""
        self.original_api_key = ""
        self.is_showing_api = False  # 用于标记当前API Key是否显示

    def create_widgets(self):
        # API Key输入框
        api_frame = ttk.Frame(self.master)
        api_frame.pack(pady=10, padx=10, fill=tk.X)

        ttk.Label(api_frame, text="智谱AI API Key:").pack(side=tk.LEFT, padx=5)
        self.api_entry = ttk.Entry(api_frame, width=50, show='*')
        self.api_entry.insert(0, "Your-API-Code")
        self.api_entry.bind("<FocusIn>", self.show_api_key)
        self.api_entry.bind("<FocusOut>", self.hide_api_key)
        self.original_api_key = self.api_entry.get()
        self.api_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # AI提示词输入框
        prompt_frame = ttk.Frame(self.master)
        prompt_frame.pack(pady=10, padx=10, fill=tk.X)

        ttk.Label(prompt_frame, text="AI提示词:").pack(side=tk.LEFT, padx=5)
        self.prompt_entry = ttk.Entry(prompt_frame, width=50)
        self.prompt_entry.insert(0, "简洁的描述图片字数10字以内，不要有任何断句")
        self.prompt_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 目录选择部分
        dir_frame = ttk.Frame(self.master)
        dir_frame.pack(pady=10, padx=10, fill=tk.X)

        self.dir_entry = ttk.Entry(dir_frame, width=50)
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(
            dir_frame,
            text="选择文件夹",
            command=self.select_directory
        ).pack(side=tk.LEFT, padx=5)

        # 参数选择部分
        param_frame = ttk.LabelFrame(self.master, text="文件名参数")
        param_frame.pack(pady=10, padx=10, fill=tk.X)

        self.include_datetime = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            param_frame,
            text="包含日期时间",
            variable=self.include_datetime
        ).pack(side=tk.LEFT, padx=5)

        self.include_camera = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            param_frame,
            text="包含相机型号",
            variable=self.include_camera
        ).pack(side=tk.LEFT, padx=5)

        self.include_lens = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            param_frame,
            text="包含镜头型号",
            variable=self.include_lens
        ).pack(side=tk.LEFT, padx=5)

        self.include_focal = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            param_frame,
            text="包含焦段",
            variable=self.include_focal
        ).pack(side=tk.LEFT, padx=5)

        self.include_aperture = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            param_frame,
            text="包含光圈",
            variable=self.include_aperture
        ).pack(side=tk.LEFT, padx=5)

        self.include_exposure = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            param_frame,
            text="包含曝光时间",
            variable=self.include_exposure
        ).pack(side=tk.LEFT, padx=5)

        self.include_iso = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            param_frame,
            text="包含ISO",
            variable=self.include_iso
        ).pack(side=tk.LEFT, padx=5)

        self.include_ai_description = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            param_frame,
            text="使用AI描述",
            variable=self.include_ai_description
        ).pack(side=tk.LEFT, padx=5)

        # 处理按钮
        button_frame = ttk.Frame(self.master)
        button_frame.pack(pady=5)

        ttk.Button(
            button_frame,
            text="开始重命名",
            command=self.start_processing
        ).pack(side=tk.LEFT, padx=5)

        self.cancel_button = ttk.Button(
            button_frame,
            text="取消",
            command=self.cancel_processing,
            state=tk.DISABLED
        )
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        # 日志区域
        self.log_text = tk.Text(self.master, state=tk.DISABLED)
        self.log_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # 进度条
        self.progress_bar = ttk.Progressbar(self.master, orient="horizontal", length=500, mode="determinate")
        self.progress_bar.pack(pady=10, padx=10)

    def select_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.selected_dir = directory
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)

    def log(self, message):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def start_processing(self):
        if not self.selected_dir:
            messagebox.showerror("错误", "请先选择目录")
            return

        if self.include_ai_description.get():
            self.api_key = self.original_api_key
            if not self.api_key or self.api_key == "Your-API-Code":
                messagebox.showerror("错误", "请输入智谱AI API Key")
                return

            self.ai_prompt = self.prompt_entry.get()
            if not self.ai_prompt:
                messagebox.showerror("错误", "请输入AI提示词")
                return

        self.cancel_flag = False
        self.cancel_button.config(state=tk.NORMAL)
        # 启动线程来处理文件
        threading.Thread(target=self.process_files).start()

    def cancel_processing(self):
        self.cancel_flag = True
        self.cancel_button.config(state=tk.DISABLED)
        self.log("处理已取消")

    def process_files(self):
        supported_ext = ('.jpg', '.jpeg', '.png', '.nef', '.tiff', '.dng')
        file_count = 0
        success_count = 0
        error_count = 0

        files = [filename for filename in os.listdir(self.selected_dir) if filename.lower().endswith(supported_ext)]
        self.total_files = len(files)

        self.progress_bar["maximum"] = self.total_files
        self.log("开始处理...")

        for i, filename in enumerate(files):
            if self.cancel_flag:
                break
            file_count += 1
            file_path = os.path.join(self.selected_dir, filename)

            # 更新进度条
            self.master.after(0, self.update_progress, i + 1)

            try:
                exif_data = self.get_exif_data(file_path)

                if not exif_data:
                    self.log(f"跳过 {filename}：无EXIF信息")
                    error_count += 1
                    continue

                name_parts = self.create_filename_parts(exif_data)

                if self.include_ai_description.get():
                    description = get_image_description(file_path, self.api_key, self.ai_prompt)
                    if description:
                        description = self.sanitize_filename(description)
                        name_parts.append(description)

                new_name = " ｜ ".join(name_parts)
                new_name = self.sanitize_filename(new_name)

                ext = os.path.splitext(filename)[1].lower()
                new_filename = self.get_unique_filename(new_name, ext)

                os.rename(file_path, os.path.join(self.selected_dir, new_filename))
                self.log(f"重命名成功：{filename} -> {new_filename}")
                success_count += 1

            except Exception as e:
                self.log(f"处理失败 {filename}: {str(e)}")
                error_count += 1

        self.cancel_button.config(state=tk.DISABLED)
        self.log(f"处理完成！共处理 {file_count} 个文件，成功 {success_count} 个，失败 {error_count} 个")

    def update_progress(self, value):
        """确保进度条在主线程更新"""
        self.progress_bar["value"] = value

    def get_exif_data(self, file_path):
        try:
            result = subprocess.run(
                ['exiftool', '-json', file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.stderr:
                self.log(f"EXIFTool Error: {result.stderr}")

            exif_data = result.stdout.strip()

            if exif_data:
                return eval(exif_data)[0]
            else:
                self.log(f"EXIF数据为空 {file_path}")
                return None

        except Exception as e:
            self.log(f"EXIF读取失败: {str(e)}")
            return None

    def sanitize_filename(self, filename):
        filename = filename.replace("?", "_").replace("<", "_").replace(">", "_")
        filename = filename.replace("*", "_").replace("\"", "_").replace("'", "_")
        filename = filename.replace("&", "_").replace("%", "_").replace("#", "_")
        filename = filename.replace("+", "_")
        return filename

    def get_unique_filename(self, base_name, extension):
        existing_files = os.listdir(self.selected_dir)
        new_name = f"{base_name}{extension}"
        if new_name in existing_files and " ｜ " in new_name:
            # 如果文件名已经存在且是之前重命名生成的，直接使用该文件名
            return new_name
        counter = 1
        while new_name in existing_files:
            new_name = f"{base_name}_{counter}{extension}"
            counter += 1
        return new_name

    def create_filename_parts(self, exif_data):
        name_parts = []

        if self.include_datetime.get() and 'DateTimeOriginal' in exif_data:
            dt_str = exif_data['DateTimeOriginal']
            dt = datetime.strptime(dt_str, '%Y:%m:%d %H:%M:%S')
            name_parts.append(dt.strftime("%Y-%m-%d_%H.%M.%S"))

        if self.include_camera.get() and 'Model' in exif_data:
            camera_model = exif_data['Model'].strip().replace(" ", "")
            name_parts.append(camera_model)

        if self.include_lens.get():
            lens_model = exif_data.get('LensModel') or exif_data.get('LensType')
            if lens_model:
                lens_model = lens_model.strip().replace(" ", "")
                name_parts.append(lens_model)

        if self.include_focal.get() and 'FocalLength' in exif_data:
            try:
                focal_value = exif_data['FocalLength'].split(' ')[0]
                focal_float = float(focal_value)
                focal_str = f"{focal_float:.1f}".rstrip('0').rstrip('.') + "mm"
                name_parts.append(focal_str)
            except (ValueError, KeyError) as e:
                self.log(f"焦距解析失败: {str(e)}")

        if self.include_exposure.get() and 'ExposureTime' in exif_data:
            exposure = exif_data['ExposureTime']
            try:
                if '/' in exposure:
                    numerator, denominator = exposure.split('/')
                    exposure_str = f"{numerator}:{denominator}s"
                elif float(exposure) >= 1.0:
                    exposure_str = f"{float(exposure):.0f}s"
                else:
                    exposure_str = f"{float(exposure):.3f}s".rstrip('0').rstrip('.') + 's'
                name_parts.append(exposure_str)
            except (ValueError, KeyError) as e:
                self.log(f"快门解析失败: {str(e)}")

        if self.include_aperture.get() and 'FNumber' in exif_data:
            aperture = str(exif_data['FNumber'])
            name_parts.append(f"F{aperture}")

        if self.include_iso.get():
            iso = exif_data.get('ISOSpeedRatings') or exif_data.get('ISO')
            if iso:
                name_parts.append(f"ISO{iso}")

        return name_parts

    def show_api_key(self, event):
        """当用户选中输入框时，显示真实的API Key"""
        current_text = self.api_entry.get()
        if current_text == "Your-API-Code" or current_text == "*" * len(current_text):
            self.api_entry.config(show='')
            self.api_entry.delete(0, tk.END)
            self.api_entry.insert(0, self.original_api_key)
            self.is_showing_api = True

    def hide_api_key(self, event):
        """当用户离开输入框时，隐藏API Key并保存原始内容"""
        new_api_key = self.api_entry.get()
        if new_api_key != "Your-API-Code":
            self.original_api_key = new_api_key
        self.api_entry.config(show='*')
        self.api_entry.delete(0, tk.END)
        self.api_entry.insert(0, '*' * len(self.original_api_key))
        self.is_showing_api = False


if __name__ == "__main__":
    root = tk.Tk()
    app = PhotoRenamerApp(root)
    root.mainloop()
