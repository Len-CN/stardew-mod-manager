import winreg
import os
import platform
import zipfile
import json
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import sys
import threading
import shutil
import webbrowser

class StardewModManager:
    def __init__(self, root):
        self.root = root
        self.root.title("星露谷Mod管理器")
        self.root.geometry("900x650")
        self.root.resizable(True, True)
        
        # 设置中文字体
        self.setup_fonts()
        
        # 变量初始化
        self.stardew_path = None
        self.mods_path = None
        self.selected_zip_files = []
        self.mods_list = []  # 存储Mod信息的列表
        
        # 创建界面
        self.create_main_widgets()
        
        # 启动时自动查找游戏路径
        self.auto_find_stardew_on_start()
        
    def setup_fonts(self):
        """设置支持中文的字体"""
        default_font = ("SimHei", 10)
        self.root.option_add("*Font", default_font)
        self.root.option_add("*Button.Font", ("SimHei", 10, "bold"))
        self.root.option_add("*Label.Font", ("SimHei", 10))
        
    def create_main_widgets(self):
        """创建主界面组件，包含选项卡"""
        # 创建选项卡控件
        self.tab_control = ttk.Notebook(self.root)
        
        # 创建安装选项卡
        self.install_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.install_tab, text="安装Mod")
        
        # 创建管理选项卡
        self.manage_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.manage_tab, text="管理Mod")
        
        # 显示选项卡
        self.tab_control.pack(expand=1, fill="both")
        
        # 创建各个选项卡的内容
        self.create_install_tab()
        self.create_manage_tab()
        
        # 底部状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_install_tab(self):
        """创建安装Mod选项卡的内容，将查找按钮改为选择按钮"""
        # 创建主框架
        main_frame = ttk.Frame(self.install_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部信息区域
        info_frame = ttk.LabelFrame(main_frame, text="游戏信息", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(info_frame, text="星露谷安装路径:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.stardew_path_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.stardew_path_var, width=70, state="readonly").grid(row=0, column=1, sticky=tk.W, pady=5)
        # 修改：将"查找游戏路径"按钮改为"选择游戏路径"
        ttk.Button(info_frame, text="选择游戏路径", command=self.manual_select_stardew_path).grid(row=0, column=2, padx=10, pady=5)
        
        ttk.Label(info_frame, text="Mods文件夹路径:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.mods_path_var = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.mods_path_var, width=70, state="readonly").grid(row=1, column=1, sticky=tk.W, pady=5)
        ttk.Button(info_frame, text="检查Mods文件夹", command=self.check_mods_folder).grid(row=1, column=2, padx=10, pady=5)
        
        # Mod选择区域
        mod_selection_frame = ttk.LabelFrame(main_frame, text="Mod选择", padding="10")
        mod_selection_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(mod_selection_frame, text="选择Mod压缩包", command=self.select_zip_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(mod_selection_frame, text="清除选择", command=self.clear_selected_files).pack(side=tk.LEFT, padx=5)
        
        # 选中的文件列表
        self.files_listbox = tk.Listbox(mod_selection_frame, width=70, height=3)
        self.files_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 安装按钮
        install_frame = ttk.Frame(main_frame)
        install_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.install_button = ttk.Button(install_frame, text="安装选中的Mod", command=self.install_mods_thread, state=tk.DISABLED)
        self.install_button.pack(pady=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="操作日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state="disabled")
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def create_manage_tab(self):
        """创建管理Mod选项卡的内容"""
        # 创建主框架
        main_frame = ttk.Frame(self.manage_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部控制区域
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(control_frame, text="刷新Mod列表", command=self.refresh_mods_list_thread).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="启用选中的Mod", command=self.enable_selected_mods).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="禁用选中的Mod", command=self.disable_selected_mods).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="删除选中的Mod", command=self.delete_selected_mods).pack(side=tk.LEFT, padx=5)
        
        # 打开N网Mod页面按钮
        self.open_nexus_button = ttk.Button(
            control_frame, 
            text="打开N网Mod页面", 
            command=self.open_nexus_page,
            state=tk.DISABLED  # 默认禁用，选中Mod后启用
        )
        self.open_nexus_button.pack(side=tk.LEFT, padx=5)
        
        # 搜索框
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="搜索Mod:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_mods)
        ttk.Entry(search_frame, textvariable=self.search_var, width=50).pack(side=tk.LEFT, padx=5)
        
        # Mod列表区域
        mods_frame = ttk.LabelFrame(main_frame, text="已安装的Mod", padding="10")
        mods_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建Treeview显示Mod列表
        columns = ("enabled", "name", "version", "nexus_id", "path")
        self.mods_tree = ttk.Treeview(mods_frame, columns=columns, show="headings")
        
        # 设置列标题
        self.mods_tree.heading("enabled", text="状态")
        self.mods_tree.heading("name", text="Mod名称")
        self.mods_tree.heading("version", text="版本")
        self.mods_tree.heading("nexus_id", text="Nexus ID")
        self.mods_tree.heading("path", text="路径")
        
        # 设置列宽
        self.mods_tree.column("enabled", width=80, anchor=tk.CENTER)
        self.mods_tree.column("name", width=200, anchor=tk.W)
        self.mods_tree.column("version", width=80, anchor=tk.CENTER)
        self.mods_tree.column("nexus_id", width=100, anchor=tk.CENTER)
        self.mods_tree.column("path", width=250, anchor=tk.W)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(mods_frame, orient=tk.VERTICAL, command=self.mods_tree.yview)
        self.mods_tree.configure(yscroll=scrollbar.set)
        
        # 布局
        self.mods_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Mod信息区域
        info_frame = ttk.LabelFrame(main_frame, text="Mod信息", padding="10")
        info_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.mod_info_text = scrolledtext.ScrolledText(info_frame, wrap=tk.WORD, state="disabled", height=6)
        self.mod_info_text.pack(fill=tk.BOTH, expand=True)
        
        # 绑定选择事件
        self.mods_tree.bind("<<TreeviewSelect>>", self.on_mod_select)
    
    # 新增：启动时自动查找游戏路径
    def auto_find_stardew_on_start(self):
        """软件启动时自动查找游戏路径"""
        self.log("程序启动，正在自动查找星露谷安装路径...")
        self.set_status("正在自动查找游戏路径...")
        # 在新线程中执行查找，避免界面卡顿
        threading.Thread(target=self.find_stardew_path, daemon=True).start()
    
    # 修改：手动选择游戏路径
    def manual_select_stardew_path(self):
        """让用户手动选择星露谷安装路径"""
        self.log("手动选择星露谷安装路径...")
        manual_path = filedialog.askdirectory(title="选择星露谷安装文件夹")
        
        if manual_path:
            # 验证手动选择的路径
            exe_name = "Stardew Valley.exe" if platform.system() == "Windows" else "Stardew Valley" if platform.system() == "Darwin" else "StardewValley"
            if os.path.exists(os.path.join(manual_path, exe_name)):
                self.stardew_path = manual_path
                self.stardew_path_var.set(manual_path)
                self.log(f"已选择路径：{manual_path}")
                self.check_mods_folder()
                # 刷新Mod列表
                self.refresh_mods_list_thread()
            else:
                messagebox.showerror("路径无效", "所选路径中未找到星露谷主程序")
                self.log("所选路径无效，未找到星露谷主程序")
        else:
            self.log("用户取消了路径选择")
    
    def open_nexus_page(self):
        """打开选中Mod的Nexus Mods网页"""
        selected_items = self.mods_tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请先选择一个Mod")
            return
        
        # 获取选中Mod的Nexus ID
        selected_item = selected_items[0]
        values = self.mods_tree.item(selected_item, "values")
        nexus_id = values[3]
        mod_name = values[1]
        
        if nexus_id == "N/A" or not nexus_id:
            messagebox.showinfo("无法打开", f"Mod '{mod_name}' 没有提供Nexus ID")
            return
        
        # 构建N网URL
        nexus_url = f"https://www.nexusmods.com/stardewvalley/mods/{nexus_id}"
        
        try:
            # 打开网页
            webbrowser.open(nexus_url)
            self.log(f"已打开Mod '{mod_name}' 的N网页面: {nexus_url}")
        except Exception as e:
            messagebox.showerror("错误", f"无法打开网页: {str(e)}")
            self.log(f"打开N网页面失败: {str(e)}")
    
    def log(self, message):
        """在日志区域添加消息"""
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)  # 滚动到最后
        self.log_text.config(state="disabled")
        self.root.update_idletasks()
    
    def set_status(self, status):
        """更新状态栏消息"""
        self.status_var.set(status)
        self.root.update_idletasks()
    
    def find_stardew_path(self):
        """查找Stardew Valley安装路径"""
        stardew_path = None
        
        if platform.system() == "Windows":
            stardew_path = self.find_stardew_from_registry()
        else:
            # 非Windows系统处理
            home_dir = os.path.expanduser("~")
            possible_paths = []
            
            if platform.system() == "Darwin":  # macOS
                possible_paths = [
                    os.path.join(home_dir, "Library", "Application Support", "Steam", "steamapps", "common", "Stardew Valley"),
                    os.path.join("/", "Applications", "Stardew Valley.app", "Contents", "Resources")
                ]
                exe_name = "Stardew Valley"
            else:  # Linux
                possible_paths = [
                    os.path.join(home_dir, ".steam", "steam", "steamapps", "common", "Stardew Valley"),
                    os.path.join(home_dir, ".local", "share", "Steam", "steamapps", "common", "Stardew Valley")
                ]
                exe_name = "StardewValley"
                    
            for path in possible_paths:
                if os.path.exists(os.path.join(path, exe_name)):
                    stardew_path = path
                    break
        
        # 在主线程中更新UI
        self.root.after(0, self.update_stardew_path, stardew_path)
    
    def update_stardew_path(self, path):
        """更新星露谷路径显示"""
        if path:
            self.stardew_path = path
            self.stardew_path_var.set(path)
            self.log(f"自动找到星露谷安装路径：{path}")
            # 自动检查Mods文件夹
            self.check_mods_folder()
            # 刷新Mod列表
            self.refresh_mods_list_thread()
        else:
            self.log("自动查找失败，未找到Stardew Valley的安装路径")
            self.log("请使用'选择游戏路径'按钮手动指定")
            messagebox.showinfo("未找到路径", "自动查找失败，请使用'选择游戏路径'按钮手动指定星露谷安装位置")
        
        self.set_status("就绪")
    
    def find_stardew_from_registry(self):
        """通过Windows注册表查找Stardew Valley安装路径"""
        registry_paths = [
            # Steam游戏注册表路径
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 413150",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 413150",
            
            # GOG版本可能的路径
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\GOG.com - Stardew Valley",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\GOG.com - Stardew Valley",
            
            # Epic Games商店版本可能的路径
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Stardew Valley",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Stardew Valley"
        ]
        
        for reg_path in registry_paths:
            try:
                # 尝试打开32位注册表项
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_32KEY) as key:
                    try:
                        install_location = winreg.QueryValueEx(key, "InstallLocation")[0]
                        if os.path.exists(os.path.join(install_location, "Stardew Valley.exe")):
                            return install_location
                    except FileNotFoundError:
                        continue
            
            except FileNotFoundError:
                # 尝试打开64位注册表项
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
                        install_location = winreg.QueryValueEx(key, "InstallLocation")[0]
                        if os.path.exists(os.path.join(install_location, "Stardew Valley.exe")):
                            return install_location
                except FileNotFoundError:
                    continue
        
        # 尝试从Steam的注册表项查找
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
                steam_path = winreg.QueryValueEx(key, "SteamPath")[0]
                steam_library_path = os.path.join(steam_path, "steamapps", "common", "Stardew Valley")
                if os.path.exists(os.path.join(steam_library_path, "Stardew Valley.exe")):
                    return steam_library_path
        except Exception:
            pass
        
        return None
    
    def check_mods_folder(self):
        """检查Mods文件夹是否存在"""
        if not self.stardew_path:
            messagebox.showwarning("警告", "请先选择星露谷安装路径")
            return
        
        self.mods_path = os.path.join(self.stardew_path, "Mods")
        self.mods_path_var.set(self.mods_path)
        
        if os.path.exists(self.mods_path) and os.path.isdir(self.mods_path):
            self.log(f"找到Mods文件夹：{self.mods_path}")
            self.install_button.config(state=tk.NORMAL)
            self.set_status("就绪 - 可以安装Mod")
        else:
            self.log(f"未找到Mods文件夹：{self.mods_path}")
            self.log("这可能意味着未安装SMAPI")
            
            # 询问用户是否创建Mods文件夹
            if messagebox.askyesno("创建文件夹", "未找到Mods文件夹，是否创建？"):
                try:
                    os.makedirs(self.mods_path)
                    self.log(f"已创建Mods文件夹：{self.mods_path}")
                    self.mods_path_var.set(self.mods_path)
                    self.install_button.config(state=tk.NORMAL)
                    self.set_status("就绪 - 可以安装Mod")
                except Exception as e:
                    self.log(f"创建Mods文件夹失败: {str(e)}")
                    messagebox.showerror("错误", f"创建Mods文件夹失败: {str(e)}")
                    self.install_button.config(state=tk.DISABLED)
            else:
                self.install_button.config(state=tk.DISABLED)
        
        self.set_status("就绪")
    
    def select_zip_files(self):
        """让用户选择一个或多个zip压缩包文件"""
        file_paths = filedialog.askopenfilenames(
            title="选择Mod压缩包",
            filetypes=[("ZIP压缩包", "*.zip"), ("所有文件", "*.*")]
        )
        
        if file_paths:
            self.selected_zip_files = list(file_paths)
            self.update_files_listbox()
            self.log(f"已选择 {len(file_paths)} 个Mod压缩包")
    
    def update_files_listbox(self):
        """更新选中文件的列表显示"""
        self.files_listbox.delete(0, tk.END)
        for file_path in self.selected_zip_files:
            self.files_listbox.insert(tk.END, os.path.basename(file_path))
    
    def clear_selected_files(self):
        """清除已选择的文件"""
        self.selected_zip_files = []
        self.files_listbox.delete(0, tk.END)
        self.log("已清除选中的Mod文件")
    
    def install_mods_thread(self):
        """在新线程中安装Mod，避免界面卡顿"""
        if not self.selected_zip_files:
            messagebox.showwarning("警告", "请先选择Mod压缩包")
            return
            
        if not self.mods_path or not os.path.exists(self.mods_path):
            messagebox.showwarning("警告", "Mods文件夹不存在，请先检查或创建")
            return
        
        self.install_button.config(state=tk.DISABLED)
        self.set_status("正在安装Mod...")
        threading.Thread(target=self.install_mods, daemon=True).start()
    
    def install_mods(self):
        """安装选中的Mod压缩包"""
        success_count = 0
        fail_count = 0
        
        for i, zip_file in enumerate(self.selected_zip_files, 1):
            self.root.after(0, self.log, f"\n处理文件 {i}/{len(self.selected_zip_files)}: {os.path.basename(zip_file)}")
            
            success, message = self.extract_zip(zip_file, self.mods_path)
            self.root.after(0, self.log, message)
            
            if success:
                success_count += 1
            else:
                fail_count += 1
        
        # 安装完成后更新UI
        self.root.after(0, self.complete_installation, success_count, fail_count)
    
    def complete_installation(self, success_count, fail_count):
        """完成安装后的处理"""
        total = success_count + fail_count
        self.log(f"\n安装完成 - 成功: {success_count}/{total}, 失败: {fail_count}/{total}")
        
        if success_count > 0:
            messagebox.showinfo("安装完成", f"成功安装 {success_count} 个Mod，失败 {fail_count} 个")
            # 刷新Mod列表
            self.refresh_mods_list_thread()
        
        self.install_button.config(state=tk.NORMAL)
        self.set_status("就绪")
    
    def list_zip_contents(self, zip_path):
        """列出zip压缩包中的所有文件和文件夹"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                return zip_ref.namelist()
        except Exception as e:
            return None
    
    def is_single_folder(self, zip_contents):
        """判断压缩包中是否只包含一个文件夹"""
        if not zip_contents:
            return False, None
        
        # 获取所有条目的根目录
        root_dirs = set()
        for item in zip_contents:
            # 分割路径，获取根目录
            parts = item.split('/')
            if parts[0]:  # 忽略空路径
                root_dirs.add(parts[0])
        
        # 如果只有一个根目录，且这个目录是所有条目的前缀
        if len(root_dirs) == 1:
            root_dir = root_dirs.pop()
            # 检查是否所有条目都以这个目录开头
            for item in zip_contents:
                if not item.startswith(root_dir) and item.strip() != "":
                    return False, None
            return True, root_dir
        
        return False, None
    
    def extract_zip(self, zip_path, target_dir):
        """解压zip文件到目标目录，根据内容结构决定解压方式"""
        # 获取压缩包内容
        zip_contents = self.list_zip_contents(zip_path)
        if not zip_contents:
            return False, "无法读取压缩包内容，可能是损坏的文件"
        
        # 判断是否只包含一个文件夹
        single_folder, folder_name = self.is_single_folder(zip_contents)
        
        try:
            if single_folder:
                # 如果只有一个文件夹，直接解压
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(target_dir)
                return True, f"成功解压到: {os.path.join(target_dir, folder_name)}"
            else:
                # 如果是零散文件，创建一个以zip文件名命名的文件夹
                zip_name = os.path.splitext(os.path.basename(zip_path))[0]
                new_folder = os.path.join(target_dir, zip_name)
                
                # 确保文件夹不存在，避免覆盖
                counter = 1
                original_new_folder = new_folder
                while os.path.exists(new_folder):
                    new_folder = f"{original_new_folder}_{counter}"
                    counter += 1
                
                # 创建文件夹并解压
                os.makedirs(new_folder, exist_ok=True)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(new_folder)
                
                return True, f"成功解压到: {new_folder}"
        except Exception as e:
            return False, f"解压失败: {str(e)}"
    
    # 处理JSON注释和提取特定字段的方法
    def clean_json_comments(self, json_text):
        """清理JSON文本中的注释"""
        # 处理多行注释 /* ... */
        json_text = re.sub(r'/\*.*?\*/', '', json_text, flags=re.DOTALL)
        
        # 处理单行注释 //...
        lines = []
        for line in json_text.split('\n'):
            # 只匹配不在引号内的//
            line = re.sub(r'(?<!")//.*$', '', line)
            lines.append(line)
        
        return '\n'.join(lines)
    
    def extract_specific_fields(self, manifest_path):
        """
        从manifest.json中提取特定字段
        只关注"Name"、"Version"、"UpdateKeys"三个字段
        """
        result = {
            "Name": None,
            "Version": None,
            "UpdateKeys": None,
            "error": None
        }
        
        # 检查文件是否存在
        if not os.path.exists(manifest_path):
            result["error"] = f"文件不存在"
            return result
        
        try:
            # 尝试多种编码读取文件
            encodings = ['utf-8', 'utf-16', 'latin-1', 'gbk']
            content = None
            
            for encoding in encodings:
                try:
                    with open(manifest_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                result["error"] = "无法解析文件，尝试了多种编码格式"
                return result
            
            # 清理注释
            cleaned_content = self.clean_json_comments(content)
            
            # 尝试完整解析JSON
            try:
                data = json.loads(cleaned_content)
                
                # 提取需要的字段
                if "Name" in data:
                    result["Name"] = data["Name"]
                if "Version" in data:
                    result["Version"] = data["Version"]
                if "UpdateKeys" in data:
                    result["UpdateKeys"] = data["UpdateKeys"]
                
                return result
                
            except json.JSONDecodeError:
                # 如果完整解析失败，尝试使用正则表达式提取字段
                result["error"] = "JSON格式存在错误，已尝试提取关键字段"
                
                # 正则表达式提取字段（处理格式错误的情况）
                patterns = {
                    "Name": re.compile(r'"Name"\s*:\s*"([^"]+)"'),
                    "Version": re.compile(r'"Version"\s*:\s*"([^"]+)"'),
                    "UpdateKeys": re.compile(r'"UpdateKeys"\s*:\s*\[(.*?)\]', re.DOTALL)
                }
                
                # 提取Name
                name_match = patterns["Name"].search(cleaned_content)
                if name_match:
                    result["Name"] = name_match.group(1)
                
                # 提取Version
                version_match = patterns["Version"].search(cleaned_content)
                if version_match:
                    result["Version"] = version_match.group(1)
                
                # 提取UpdateKeys
                update_keys_match = patterns["UpdateKeys"].search(cleaned_content)
                if update_keys_match:
                    keys_content = update_keys_match.group(1)
                    # 提取所有引号中的内容
                    keys = re.findall(r'"([^"]+)"', keys_content)
                    result["UpdateKeys"] = keys if keys else None
                
                return result
                
        except Exception as e:
            result["error"] = f"处理文件时出错: {str(e)}"
            return result
    
    # Mod管理相关功能
    def refresh_mods_list_thread(self):
        """在新线程中刷新Mod列表"""
        self.set_status("正在刷新Mod列表...")
        threading.Thread(target=self.refresh_mods_list, daemon=True).start()
    
    def refresh_mods_list(self):
        """刷新Mod列表，只提取需要的字段"""
        if not self.mods_path or not os.path.exists(self.mods_path):
            self.root.after(0, lambda: messagebox.showwarning("警告", "未找到Mods文件夹，请先设置正确的游戏路径"))
            self.root.after(0, lambda: self.set_status("就绪"))
            return
        
        # 扫描Mods文件夹
        mods = []
        for item in os.listdir(self.mods_path):
            item_path = os.path.join(self.mods_path, item)
            if os.path.isdir(item_path):
                # 检查是否是禁用的Mod（文件夹名以.开头）
                is_disabled = item.startswith('.')
                mod_name = item[1:] if is_disabled else item
                
                # 尝试读取manifest中的特定字段
                manifest_path = os.path.join(item_path, "manifest.json")
                manifest_data = self.extract_specific_fields(manifest_path)
                
                # 提取Nexus ID
                nexus_id = "N/A"
                if manifest_data["UpdateKeys"]:
                    for key in manifest_data["UpdateKeys"]:
                        if isinstance(key, str) and key.startswith("Nexus:"):
                            nexus_id = key.split(":", 1)[1].strip()
                            break
                
                mods.append({
                    'name': manifest_data["Name"] or mod_name,  # 使用manifest中的名称或文件夹名
                    'version': manifest_data["Version"] or "未知",
                    'path': item_path,
                    'folder_name': item,
                    'enabled': not is_disabled,
                    'nexus_id': nexus_id,
                    'manifest_error': manifest_data["error"]
                })
        
        self.mods_list = mods
        self.root.after(0, self.update_mods_treeview)
        self.root.after(0, lambda: self.set_status("就绪"))
    
    def update_mods_treeview(self):
        """更新Mod列表视图，显示所需字段"""
        # 清空现有内容
        for item in self.mods_tree.get_children():
            self.mods_tree.delete(item)
        
        # 添加所有Mod，包含所需字段
        for mod in self.mods_list:
            status = "启用" if mod['enabled'] else "禁用"
            self.mods_tree.insert("", tk.END, values=(
                status, 
                mod['name'],
                mod['version'],
                mod['nexus_id'],
                mod['path']
            ))
    
    def filter_mods(self, *args):
        """根据搜索框内容过滤Mod列表"""
        search_text = self.search_var.get().lower()
        
        # 清空现有内容
        for item in self.mods_tree.get_children():
            self.mods_tree.delete(item)
        
        # 添加符合条件的Mod
        for mod in self.mods_list:
            # 搜索条件：名称、版本、Nexus ID或路径包含搜索文本
            if (search_text in mod['name'].lower() or 
                search_text in mod['version'].lower() or
                search_text in mod['nexus_id'].lower() or 
                search_text in mod['path'].lower()):
                status = "启用" if mod['enabled'] else "禁用"
                self.mods_tree.insert("", tk.END, values=(
                    status, 
                    mod['name'],
                    mod['version'],
                    mod['nexus_id'],
                    mod['path']
                ))
    
    def on_mod_select(self, event):
        """当选择Mod时显示其信息，并启用N网按钮"""
        selected_items = self.mods_tree.selection()
        
        # 根据选择状态启用/禁用N网按钮
        if selected_items and len(selected_items) == 1:
            self.open_nexus_button.config(state=tk.NORMAL)
        else:
            self.open_nexus_button.config(state=tk.DISABLED)
        
        if not selected_items:
            return
        
        # 获取选中的Mod
        selected_item = selected_items[0]
        values = self.mods_tree.item(selected_item, "values")
        mod_path = values[4]
        name = values[1]
        version = values[2]
        nexus_id = values[3]
        
        # 查找完整的Mod信息
        mod_info = next((m for m in self.mods_list if m['path'] == mod_path), None)
        
        # 构建信息字符串
        info = f"Mod路径: {mod_path}\n"
        info += f"名称: {name}\n"
        info += f"版本: {version}\n"
        
        if nexus_id and nexus_id != "N/A":
            info += f"Nexus ID: {nexus_id}\n"
            info += f"Nexus链接: https://www.nexusmods.com/stardewvalley/mods/{nexus_id}\n"
        else:
            info += "Nexus ID: 未提供\n"
        
        # 如果有manifest错误，显示错误信息
        if mod_info and mod_info['manifest_error']:
            info += f"\n注意: {mod_info['manifest_error']}"
        
        # 显示信息
        self.mod_info_text.config(state="normal")
        self.mod_info_text.delete(1.0, tk.END)
        self.mod_info_text.insert(tk.END, info)
        self.mod_info_text.config(state="disabled")
    
    def enable_selected_mods(self):
        """启用选中的Mod"""
        selected_items = self.mods_tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请先选择要启用的Mod")
            return
        
        enabled_count = 0
        
        for item in selected_items:
            mod_path = self.mods_tree.item(item, "values")[4]
            mod_folder = os.path.basename(mod_path)
            
            # 如果是禁用状态（文件夹名以.开头）
            if mod_folder.startswith('.'):
                new_folder_name = mod_folder[1:]
                new_path = os.path.join(os.path.dirname(mod_path), new_folder_name)
                
                try:
                    os.rename(mod_path, new_path)
                    enabled_count += 1
                except Exception as e:
                    messagebox.showerror("错误", f"启用Mod失败: {str(e)}")
        
        if enabled_count > 0:
            messagebox.showinfo("成功", f"已启用 {enabled_count} 个Mod")
            self.refresh_mods_list_thread()
    
    def disable_selected_mods(self):
        """禁用选中的Mod"""
        selected_items = self.mods_tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请先选择要禁用的Mod")
            return
        
        disabled_count = 0
        
        for item in selected_items:
            mod_path = self.mods_tree.item(item, "values")[4]
            mod_folder = os.path.basename(mod_path)
            
            # 如果是启用状态（文件夹名不以.开头）
            if not mod_folder.startswith('.'):
                new_folder_name = f".{mod_folder}"
                new_path = os.path.join(os.path.dirname(mod_path), new_folder_name)
                
                try:
                    os.rename(mod_path, new_path)
                    disabled_count += 1
                except Exception as e:
                    messagebox.showerror("错误", f"禁用Mod失败: {str(e)}")
        
        if disabled_count > 0:
            messagebox.showinfo("成功", f"已禁用 {disabled_count} 个Mod")
            self.refresh_mods_list_thread()
    
    def delete_selected_mods(self):
        """删除选中的Mod"""
        selected_items = self.mods_tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请先选择要删除的Mod")
            return
        
        # 确认删除
        if not messagebox.askyesno("确认删除", f"确定要删除选中的 {len(selected_items)} 个Mod吗？此操作不可恢复！"):
            return
        
        deleted_count = 0
        failed_count = 0
        
        for item in selected_items:
            mod_path = self.mods_tree.item(item, "values")[4]
            
            try:
                # 删除文件夹
                if os.path.isdir(mod_path):
                    shutil.rmtree(mod_path)
                    deleted_count += 1
            except Exception as e:
                messagebox.showerror("错误", f"删除Mod失败: {str(e)}")
                failed_count += 1
        
        messagebox.showinfo("结果", f"已删除 {deleted_count} 个Mod，{failed_count} 个删除失败")
        self.refresh_mods_list_thread()

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = StardewModManager(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("程序错误", f"程序发生错误: {str(e)}")
        sys.exit(1)
    