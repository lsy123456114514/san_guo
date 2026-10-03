#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
上传工具 - 支持 FTP 和 pCloud API
"""

import os
import sys
import ftplib
from ftplib import FTP_TLS
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

class UploadTool:
    def __init__(self, master):
        self.master = master
        self.master.title("上传工具")
        self.master.geometry("600x550")
        self.master.configure(bg="#f0f0f0")
        
        # API 配置
        self.api_base_url = "https://send.now/api"
        self.pcloud_token = "599844ihwbpv2n9ueru13g"
        self.pcloud_folder_id = 0  # 根目录
        
        # FTP 配置
        self.ftp_host = "ftp.send.now"
        self.ftp_port = 992
        self.ftp_user = "lsy123456114514"
        self.ftp_pass = ""
        self.ftp_path = "/"
        
        # 文件列表
        self.files_to_upload = []
        
        self.create_widgets()
    
    def create_widgets(self):
        """创建界面组件"""
        # 标题
        title = tk.Label(self.master, text="上传工具", font=("Arial", 20, "bold"), bg="#f0f0f0")
        title.pack(pady=10)
        
        # 模式选择
        mode_frame = tk.Frame(self.master, bg="#f0f0f0")
        mode_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Label(mode_frame, text="选择上传方式:", font=("Arial", 11, "bold"), bg="#f0f0f0").pack(anchor="w")
        
        self.mode_var = tk.StringVar(value="pcloud")
        
        mode_btn_frame = tk.Frame(mode_frame, bg="#f0f0f0")
        mode_btn_frame.pack(fill="x", pady=5)
        
        tk.Radiobutton(mode_btn_frame, text="📬 send.now API (推荐)", variable=self.mode_var, 
                      value="pcloud", font=("Arial", 10), bg="#f0f0f0",
                      command=self.on_mode_change).pack(side="left", padx=10)
        
        tk.Radiobutton(mode_btn_frame, text="🖥️ FTP 服务器", variable=self.mode_var, 
                      value="ftp", font=("Arial", 10), bg="#f0f0f0",
                      command=self.on_mode_change).pack(side="left", padx=10)
        
        # send.now 配置框架
        self.pcloud_frame = tk.LabelFrame(self.master, text="send.now 配置", font=("Arial", 10), bg="#f0f0f0")
        self.pcloud_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Label(self.pcloud_frame, text=f"API 密钥: {self.pcloud_token[:10]}...{self.pcloud_token[-5:]}",
                font=("Arial", 9), bg="#f0f0f0").pack(anchor="w", padx=5)
        
        # FTP 配置框架
        self.ftp_frame = tk.LabelFrame(self.master, text="FTP 配置", font=("Arial", 10), bg="#f0f0f0")
        self.ftp_frame.pack(fill="x", padx=20, pady=5)
        
        ftp_info = f"主机: {self.ftp_host}\n端口: {self.ftp_port}\n用户名: {self.ftp_user}"
        tk.Label(self.ftp_frame, text=ftp_info, font=("Arial", 9), bg="#f0f0f0", justify="left").pack(anchor="w", padx=5)
        
        pass_frame = tk.Frame(self.ftp_frame, bg="#f0f0f0")
        pass_frame.pack(fill="x", padx=5, pady=5)
        
        tk.Label(pass_frame, text="密码:", font=("Arial", 10), bg="#f0f0f0").pack(side="left")
        self.ftp_pass_entry = tk.Entry(pass_frame, show="*", width=25)
        self.ftp_pass_entry.pack(side="left", padx=5)
        
        tk.Button(pass_frame, text="测试连接", command=self.test_ftp_connection, 
                  bg="#4CAF50", fg="white").pack(side="left")
        
        # 隐藏 FTP 框架
        self.ftp_frame.pack_forget()
        
        # 文件拖拽区域
        self.drop_frame = tk.Frame(self.master, bg="white", relief="solid", bd=2)
        self.drop_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.drop_label = tk.Label(self.drop_frame, text="拖拽文件到此处\n\n或者", font=("Arial", 14), bg="white")
        self.drop_label.pack(expand=True)
        
        self.setup_drag_drop()
        
        # 按钮
        btn_frame = tk.Frame(self.master, bg="#f0f0f0")
        btn_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Button(btn_frame, text="📁 选择文件", command=self.select_files, bg="#2196F3", fg="white",
                  font=("Arial", 11), width=15).pack(side="left", padx=5)
        
        tk.Button(btn_frame, text="🗑️ 清空列表", command=self.clear_list, bg="#ff9800", fg="white",
                  font=("Arial", 11), width=15).pack(side="left", padx=5)
        
        # 文件列表
        list_frame = tk.Frame(self.master)
        list_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.file_listbox = tk.Listbox(list_frame, width=70, height=8, font=("Arial", 10))
        self.file_listbox.pack(side="left", fill="both", expand=True)
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.file_listbox.yview)
        
        # 上传按钮
        self.upload_btn = tk.Button(self.master, text="⬆️ 开始上传", command=self.start_upload,
                                   bg="#4CAF50", fg="white", font=("Arial", 14, "bold"),
                                   height=2, cursor="hand2")
        self.upload_btn.pack(fill="x", padx=20, pady=10)
        
        # 进度条框架
        progress_frame = tk.Frame(self.master, bg="#f0f0f0")
        progress_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Label(progress_frame, text="上传进度:", font=("Arial", 9), bg="#f0f0f0").pack(anchor="w")
        
        self.progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", 
                                           length=400, mode="determinate")
        self.progress_bar.pack(fill="x", pady=2)
        
        self.progress_label = tk.Label(progress_frame, text="0%", font=("Arial", 9), bg="#f0f0f0", fg="blue")
        self.progress_label.pack(anchor="w")
        
        # 状态
        self.status_label = tk.Label(self.master, text="准备就绪", font=("Arial", 9), bg="#f0f0f0", fg="gray")
        self.status_label.pack()
    
    def on_mode_change(self):
        """切换上传模式"""
        mode = self.mode_var.get()
        if mode == "pcloud":
            self.pcloud_frame.pack(fill="x", padx=20, pady=5)
            self.ftp_frame.pack_forget()
        else:
            self.pcloud_frame.pack_forget()
            self.ftp_frame.pack(fill="x", padx=20, pady=5)
    
    def setup_drag_drop(self):
        """设置拖拽功能"""
        def on_drag_over(event):
            self.drop_frame.config(bg="#e8f5e9")
            self.drop_label.config(bg="#e8f5e9")
        
        def on_drag_leave(event):
            self.drop_frame.config(bg="white")
            self.drop_label.config(bg="white")
        
        def on_drop(event):
            self.drop_frame.config(bg="white")
            self.drop_label.config(bg="white")
            files = self.master.tk.splitlist(event.data)
            for file_path in files:
                if os.path.isfile(file_path):
                    self.add_file(file_path)
        
        self.drop_frame.bind("<Enter>", on_drag_over)
        self.drop_frame.bind("<Leave>", on_drag_leave)
        self.drop_frame.bind("<ButtonRelease-1>", on_drop)
    
    def add_file(self, file_path):
        """添加文件"""
        if file_path not in self.files_to_upload:
            self.files_to_upload.append(file_path)
            self.file_listbox.insert(tk.END, os.path.basename(file_path))
            self.status_label.config(text=f"已添加 {len(self.files_to_upload)} 个文件", fg="green")
    
    def select_files(self):
        """选择文件"""
        files = filedialog.askopenfilenames(title="选择要上传的文件")
        for file in files:
            self.add_file(file)
    
    def clear_list(self):
        """清空列表"""
        self.files_to_upload.clear()
        self.file_listbox.delete(0, tk.END)
        self.status_label.config(text="列表已清空", fg="gray")
    
    def test_ftp_connection(self):
        """测试 FTP 连接"""
        password = self.ftp_pass_entry.get()
        if not password:
            messagebox.showwarning("提示", "请输入密码")
            return
        
        self.status_label.config(text="正在测试连接...", fg="blue")
        self.master.update()
        
        try:
            if self.ftp_port == 992:
                ftp = FTP_TLS()
                ftp.connect(self.ftp_host, self.ftp_port)
                ftp.login(self.ftp_user, password)
            else:
                ftp = ftplib.FTP()
                ftp.connect(self.ftp_host, self.ftp_port)
                ftp.login(self.ftp_user, password)
            
            ftp.quit()
            messagebox.showinfo("成功", "FTP 连接测试成功！")
            self.status_label.config(text="连接测试成功", fg="green")
        except Exception as e:
            messagebox.showerror("错误", f"连接失败:\n{str(e)}")
            self.status_label.config(text="连接失败", fg="red")
    
    def upload_to_pcloud(self, file_path, progress_callback=None):
        """上传文件到 send.now API"""
        import urllib.parse
        
        filename = os.path.basename(file_path)
        
        abs_path = os.path.abspath(file_path)
        abs_path = abs_path.replace('\\', '/')
        local_url = "file:///" + abs_path
        encoded_url = urllib.parse.quote(local_url, safe='')
        
        url = f"{self.api_base_url}/upload/url?key={self.pcloud_token}&url={encoded_url}"
        
        if progress_callback:
            progress_callback(0, 100)
        
        response = requests.get(url, timeout=300)
        
        if progress_callback:
            progress_callback(100, 100)
        
        if response.status_code != 200:
            try:
                data = response.json()
                error_msg = data.get('msg', data.get('error', f"HTTP {response.status_code}"))
            except:
                error_msg = f"HTTP {response.status_code}"
            if response.status_code == 404:
                error_msg = "API 端点不存在，请检查 API 配置"
            elif response.status_code == 403:
                error_msg = "API 密钥无效或权限不足"
            elif response.status_code == 400:
                error_msg = "请求参数错误"
            raise Exception(f"上传失败: {error_msg}")
        
        result = response.json()
        if result.get('status') != 200:
            error_msg = result.get('msg', '未知错误')
            raise Exception(f"上传失败: {error_msg}")
        
        return True
    
    def upload_to_ftp(self, file_path):
        """上传文件到 FTP"""
        filename = os.path.basename(file_path)
        password = self.ftp_pass_entry.get()
        
        if self.ftp_port == 992:
            ftp = FTP_TLS()
            ftp.connect(self.ftp_host, self.ftp_port)
            ftp.login(self.ftp_user, password)
        else:
            ftp = ftplib.FTP()
            ftp.connect(self.ftp_host, self.ftp_port)
            ftp.login(self.ftp_user, password)
        
        if self.ftp_path != "/":
            ftp.cwd(self.ftp_path)
        
        with open(file_path, 'rb') as f:
            ftp.storbinary(f"STOR {filename}", f)
        
        ftp.quit()
        return True
    
    def start_upload(self):
        """开始上传"""
        if not self.files_to_upload:
            messagebox.showwarning("提示", "请先添加要上传的文件")
            return
        
        mode = self.mode_var.get()
        
        if mode == "ftp":
            password = self.ftp_pass_entry.get()
            if not password:
                messagebox.showwarning("提示", "请输入 FTP 密码")
                return
        
        self.upload_btn.config(state="disabled", text="上传中...")
        
        upload_thread = threading.Thread(target=self._upload_worker, args=(mode,))
        upload_thread.daemon = True
        upload_thread.start()
    
    def _upload_worker(self, mode):
        """后台上传工作线程"""
        total_files = len(self.files_to_upload)
        total_size = sum(os.path.getsize(f) for f in self.files_to_upload)
        uploaded_size = 0
        success = 0
        failed = []
        
        def progress_callback(uploaded, file_size):
            nonlocal uploaded_size
            uploaded_size += uploaded - (uploaded_size % file_size)
            percentage = int((uploaded_size / total_size) * 100)
            self.master.after(0, lambda p=percentage: self.progress_bar.config(value=p))
            self.master.after(0, lambda p=percentage: self.progress_label.config(text=f"{p}%"))
        
        for i, file_path in enumerate(self.files_to_upload):
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            self.master.after(0, lambda fn=filename, idx=i+1, t=total_files: 
                             self.status_label.config(text=f"上传 [{idx}/{t}]: {fn}", fg="blue"))
            
            try:
                if mode == "pcloud":
                    self.upload_to_pcloud(file_path, progress_callback)
                else:
                    self.upload_to_ftp(file_path)
                    uploaded_size += file_size
                    percentage = int((uploaded_size / total_size) * 100)
                    self.master.after(0, lambda p=percentage: self.progress_bar.config(value=p))
                    self.master.after(0, lambda p=percentage: self.progress_label.config(text=f"{p}%"))
                
                success += 1
                
            except Exception as e:
                failed.append(f"{filename}: {str(e)}")
        
        self.master.after(0, self._upload_complete, total_files, success, failed)
    
    def _upload_complete(self, total, success, failed):
        """上传完成后的回调"""
        self.upload_btn.config(state="normal", text="⬆️ 开始上传")
        self.progress_bar.config(value=0)
        self.progress_label.config(text="0%")
        
        if success == total:
            messagebox.showinfo("成功", f"全部 {total} 个文件上传成功！")
            self.status_label.config(text=f"上传完成！成功 {success} 个", fg="green")
            self.clear_list()
        else:
            msg = f"成功: {success}/{total}\n\n失败:\n" + "\n".join(failed)
            messagebox.showwarning("部分失败", msg)
            self.status_label.config(text=f"完成，成功 {success}，失败 {len(failed)}", fg="orange")

def main():
    """主函数"""
    if not HAS_REQUESTS:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("错误", "请安装 requests 库：\npip install requests")
        return
    
    root = tk.Tk()
    app = UploadTool(root)
    root.mainloop()

if __name__ == "__main__":
    main()
