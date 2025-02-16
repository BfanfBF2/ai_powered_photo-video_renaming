import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ffmpeg
import xml.etree.ElementTree as ET
from datetime import datetime
import os
import base64
from zhipuai import ZhipuAI
import threading
import time


def extract_keyframe(video_path):
    try:
        # 使用 ffmpeg 提取视频的第一帧
        out, err = (
            ffmpeg
            .input(video_path)
            .filter('select', 'eq(pict_type,PICT_TYPE_I)')
            .output('pipe:', format='image2', vframes=1)
            .run(capture_stdout=True, capture_stderr=True)
        )
        if err:
            print(f"ffmpeg 错误信息: {err.decode('utf-8')}")
        return out
    except Exception as e:
        print(f"提取关键帧时出错: {e}")
        return None


# 调用智谱 AI 接口获取视频描述
def get_video_description(video_path, api_key, prompt):
    client = ZhipuAI(api_key=api_key)
    try:
        # 提取关键帧
        keyframes = extract_keyframe(video_path)
        if keyframes:
            # 对关键帧进行 Base64 编码
            img_base = base64.b64encode(keyframes).decode('utf-8')
            # 记录请求开始时间
            start_time = time.time()
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
            # 记录请求结束时间并计算耗时
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"请求耗时: {elapsed_time:.2f} 秒")
            return response.choices[0].message.content
    except Exception as e:
        messagebox.showerror("API 调用错误", f"调用智谱 AI 接口时出现错误: {str(e)}")
        return None


class VideoMetadataRenamer:
    def __init__(self, root):
        self.root = root
        self.root.title("视频元数据重命名工具")
        self.root.geometry("800x700")

        self.default_api_key_text = "Your-API-Code"

        # 创建 API Key 输入框
        self.create_api_key_input()
        # 创建 AI 提示词输入框
        self.create_ai_prompt_input()
        # 创建选择目录相关组件
        self.create_directory_selection()
        # 创建元数据选项相关组件
        self.create_metadata_options()
        # 创建处理按钮和日志区域等组件
        self.create_processing_components()

        self.selected_dir = ""
        self.total_files = 0
        self.cancel_flag = False
        self.api_key = ""
        self.ai_prompt = ""
        self.original_api_key = ""

    def create_api_key_input(self):
        api_frame = ttk.Frame(self.root)
        api_frame.pack(pady=10, padx=10, fill=tk.X)

        ttk.Label(api_frame, text="智谱 AI API Key:").pack(side=tk.LEFT, padx=5)
        self.api_entry = ttk.Entry(api_frame, width=50, show='*')
        self.api_entry.insert(0, self.default_api_key_text)
        self.api_entry.bind("<FocusIn>", self.show_api_key)
        self.api_entry.bind("<FocusOut>", self.hide_api_key)
        self.original_api_key = self.api_entry.get()
        self.api_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def create_ai_prompt_input(self):
        prompt_frame = ttk.Frame(self.root)
        prompt_frame.pack(pady=10, padx=10, fill=tk.X)

        ttk.Label(prompt_frame, text="AI 提示词:").pack(side=tk.LEFT, padx=5)
        self.prompt_entry = ttk.Entry(prompt_frame, width=50)
        self.prompt_entry.insert(0, "简洁描述关键帧 10 字内")
        self.prompt_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def create_directory_selection(self):
        self.dir_frame = ttk.Frame(self.root)
        self.dir_frame.pack(pady=10, padx=10, fill=tk.X)

        self.dir_entry = ttk.Entry(self.dir_frame, width=50)
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.select_dir_button = ttk.Button(
            self.dir_frame,
            text="选择文件夹",
            command=self.select_directory
        )
        self.select_dir_button.pack(side=tk.LEFT, padx=5)

    def create_metadata_options(self):
        self.metadata_frame = ttk.LabelFrame(self.root, text="元数据选项")
        self.metadata_frame.pack(pady=10, padx=10, fill=tk.X)

        self.modification_time_var = tk.BooleanVar(value=True)
        self.modification_time_check = ttk.Checkbutton(
            self.metadata_frame,
            text="修改日期时间",
            variable=self.modification_time_var
        )
        self.modification_time_check.pack(side=tk.LEFT, padx=5)

        self.model_var = tk.BooleanVar(value=True)
        self.model_check = ttk.Checkbutton(
            self.metadata_frame,
            text="拍摄机型",
            variable=self.model_var
        )
        self.model_check.pack(side=tk.LEFT, padx=5)

        self.resolution_var = tk.BooleanVar(value=True)
        self.resolution_check = ttk.Checkbutton(
            self.metadata_frame,
            text="分辨率",
            variable=self.resolution_var
        )
        self.resolution_check.pack(side=tk.LEFT, padx=5)

        self.frame_rate_var = tk.BooleanVar(value=True)
        self.frame_rate_check = ttk.Checkbutton(
            self.metadata_frame,
            text="帧率",
            variable=self.frame_rate_var
        )
        self.frame_rate_check.pack(side=tk.LEFT, padx=5)

        self.codec_var = tk.BooleanVar(value=True)
        self.codec_check = ttk.Checkbutton(
            self.metadata_frame,
            text="编码方式",
            variable=self.codec_var
        )
        self.codec_check.pack(side=tk.LEFT, padx=5)

        self.include_ai_description = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.metadata_frame,
            text="使用 AI 描述",
            variable=self.include_ai_description
        ).pack(side=tk.LEFT, padx=5)

    def create_processing_components(self):
        button_frame = ttk.Frame(self.root)
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

        self.log_text = tk.Text(self.root, state=tk.DISABLED)
        self.log_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        self.progress_bar = ttk.Progressbar(self.root, orient="horizontal", length=500, mode="determinate")
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

    def get_video_metadata(self, file_path):
        try:
            probe = ffmpeg.probe(file_path)
            resolution = None
            frame_rate = None
            codec = None
            model = None

            format_info = probe['format']
            tags = format_info.get('tags', {})

            possible_model_tags = ['model', 'Make', 'DeviceModelName', 'CameraModelName', 'ProductModel']
            for tag in possible_model_tags:
                if tag in tags:
                    model = tags[tag]
                    break

            xml_metadata = tags.get('com.panasonic.Semi-Pro.metadata.xml')
            if xml_metadata and not model:
                try:
                    root = ET.fromstring(xml_metadata)
                    for elem in root.findall('.//*'):
                        if elem.text and 'Model' in elem.tag:
                            model = elem.text
                            break
                    if not model:
                        print("未找到模型信息。")
                except ET.ParseError as e:
                    print(f"解析 XML 元数据时出错: {e}")

            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            if video_stream:
                width = video_stream.get('width')
                height = video_stream.get('height')
                if width and height:
                    resolution = f"{width}x{height}"

                r_frame_rate = video_stream.get('r_frame_rate')
                if r_frame_rate:
                    try:
                        num, den = map(int, r_frame_rate.split('/'))
                        frame_rate = num / den if den != 0 else None
                    except ValueError:
                        pass

                profile = video_stream.get('profile')
                codec_name = video_stream.get('codec_name')
                if profile and codec_name:
                    codec = f"{codec_name}_{profile}"

                if not codec:
                    codec_keywords = ['codec', 'encoding']
                    for keyword in codec_keywords:
                        for key, value in tags.items():
                            if keyword.lower() in key.lower():
                                codec = value
                                break
                        if codec:
                            break

                if not codec:
                    codec = codec_name

            return resolution, frame_rate, codec, model

        except Exception as e:
            self.log(f"读取元数据时出错: {e}")
            return None, None, None, None

    def start_processing(self):
        if not self.selected_dir:
            messagebox.showerror("错误", "请先选择目录")
            return

        if self.include_ai_description.get():
            # 获取真实的 API Key
            api_key_input = self.api_entry.get()
            if api_key_input == '*' * len(self.original_api_key):
                api_key = self.original_api_key
            else:
                api_key = api_key_input

            if api_key == self.default_api_key_text or not api_key.strip():
                messagebox.showerror("错误", "请输入有效的智谱 AI API Key")
                return

            # 简单验证 API Key 格式，可根据实际情况调整
            if len(api_key) < 20:
                messagebox.showerror("错误", "输入的 API Key 格式可能不正确，请检查。")
                return

            self.api_key = api_key

            ai_prompt = self.prompt_entry.get()
            if not ai_prompt.strip():
                messagebox.showerror("错误", "请输入有效的 AI 提示词")
                return
            self.ai_prompt = ai_prompt

        self.cancel_flag = False
        self.cancel_button.config(state=tk.NORMAL)
        threading.Thread(target=self.process_files).start()

    def cancel_processing(self):
        self.cancel_flag = True
        self.cancel_button.config(state=tk.DISABLED)
        self.log("处理已取消")

    def process_files(self):
        supported_ext = ('.mp4', '.mov', '.avi', '.mkv')
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

            self.root.after(0, self.update_progress, i + 1)

            try:
                resolution, frame_rate, codec, model = self.get_video_metadata(file_path)

                name_parts = []

                if self.modification_time_var.get():
                    mod_time = os.path.getmtime(file_path)
                    dt = datetime.fromtimestamp(mod_time)
                    name_parts.append(dt.strftime("%Y-%m-%d_%H.%M.%S"))

                if self.model_var.get() and model:
                    name_parts.append(model)

                if self.resolution_var.get() and resolution:
                    name_parts.append(resolution)

                if self.frame_rate_var.get() and frame_rate:
                    formatted_frame_rate = "{:.2f}".format(frame_rate)
                    name_parts.append(formatted_frame_rate)

                if self.codec_var.get() and codec:
                    name_parts.append(codec)

                if self.include_ai_description.get():
                    description = get_video_description(file_path, self.api_key, self.ai_prompt)
                    if description:
                        description = self.sanitize_filename(description)
                        name_parts.append(description)

                new_name = " | ".join(name_parts)
                if not new_name:
                    self.log(f"跳过 {filename}：未获取到有效元数据用于重命名")
                    error_count += 1
                    continue

                ext = os.path.splitext(filename)[1].lower()
                new_filename = self.get_unique_filename(new_name, ext)

                os.rename(
                    file_path,
                    os.path.join(self.selected_dir, new_filename)
                )
                self.log(f"重命名成功：{filename} -> {new_filename}")
                success_count += 1

            except Exception as e:
                self.log(f"处理失败 {filename}: {str(e)}")
                error_count += 1

        self.cancel_button.config(state=tk.DISABLED)
        self.log(f"处理完成！共处理 {file_count} 个文件，成功 {success_count} 个，失败 {error_count} 个")

    def update_progress(self, value):
        self.progress_bar["value"] = value

    def sanitize_filename(self, filename):
        filename = filename.replace("?", "_").replace("<", "_").replace(">", "_")
        filename = filename.replace("*", "_").replace("\"", "_").replace("'", "_")
        filename = filename.replace("&", "_").replace("%", "_").replace("#", "_")
        filename = filename.replace("+", "_")
        return filename

    def get_unique_filename(self, base_name, extension):
        new_name = f"{base_name}{extension}"
        if os.path.exists(os.path.join(self.selected_dir, new_name)):
            if " | " in base_name:
                return new_name
            counter = 1
            while True:
                temp_name = f"{base_name}_{counter}{extension}"
                if not os.path.exists(os.path.join(self.selected_dir, temp_name)):
                    return temp_name
                counter += 1
        return new_name

    def show_api_key(self, event):
        if self.api_entry.get() == '*' * len(self.original_api_key):
            self.api_entry.config(show='')
            self.api_entry.delete(0, tk.END)
            self.api_entry.insert(0, self.original_api_key)

    def hide_api_key(self, event):
        api_key = self.api_entry.get()
        if api_key != self.default_api_key_text and api_key.strip():
            self.original_api_key = api_key
        self.api_entry.config(show='*')
        self.api_entry.delete(0, tk.END)
        if self.original_api_key == self.default_api_key_text:
            self.api_entry.insert(0, self.default_api_key_text)
        else:
            self.api_entry.insert(0, '*' * len(self.original_api_key))


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoMetadataRenamer(root)
    root.mainloop()
