import os
import sys
import time
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

class ColorfulProgressBar:
    """彩色进度条类"""
    
    COLORS = {
        'black': '\033[30m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'magenta': '\033[35m',
        'cyan': '\033[36m',
        'white': '\033[37m',
        'reset': '\033[0m',
        'bold': '\033[1m',
    }
    
    @staticmethod
    def color_text(text, color):
        """给文本添加颜色"""
        return f"{ColorfulProgressBar.COLORS.get(color, '')}{text}{ColorfulProgressBar.COLORS['reset']}"
    
    @staticmethod
    def create_progress_bar(progress, total, width=50, color='green'):
        """创建进度条"""
        if total == 0:
            return f"[{'░' * width}]   0.00% (0/0)"
        percent = progress / total * 100
        filled_width = int(width * progress / total)
        bar = '█' * filled_width + '░' * (width - filled_width)
        
        colored_bar = ColorfulProgressBar.color_text(bar[:filled_width], color) + bar[filled_width:]
        return f"[{colored_bar}] {percent:6.2f}% ({progress}/{total})"
    
    @staticmethod
    def display_progress(desc, progress, total, color='green'):
        """显示进度条"""
        bar = ColorfulProgressBar.create_progress_bar(progress, total, color=color)
        sys.stdout.write(f"\r{ColorfulProgressBar.color_text(desc, 'cyan')}: {bar}")
        sys.stdout.flush()
    
    @staticmethod
    def complete_progress(desc, total, color='green'):
        """完成进度条"""
        bar = ColorfulProgressBar.create_progress_bar(total, total, color=color)
        sys.stdout.write(f"\r{ColorfulProgressBar.color_text(desc, 'cyan')}: {bar} {ColorfulProgressBar.color_text('✓ 完成', 'green')}\n")
        sys.stdout.flush()

class SystemSearcher:
    def __init__(self, target_path):
        self.target_path = Path(target_path)
        self.folders = []
        self.files = []
        self.results = {
            'folders_found': [],
            'folders_not_found': [],
            'files_found': [],
            'files_not_found': []
        }
        
        # 进度计数器
        self.progress_folders = 0
        self.progress_files = 0
        
        # 用于显示当前搜索的信息
        self.current_search_items = {
            'folders': {},
            'files': {}
        }
        
        # 显示控制
        self.show_search_paths = True  # 是否显示搜索路径
        self.show_search_items = True  # 是否显示正在搜索的项目
        
        # Windows常见的搜索根目录
        self.search_roots = [
            "C:\\",
            "D:\\",
            "E:\\",
            "F:\\",
            "G:\\",
            os.path.expanduser("~"),  # 用户目录
            "C:\\Program Files",
            "C:\\Program Files (x86)",
            "C:\\Windows",
            "C:\\Users"
        ]
    
    def display_directory_contents(self):
        """彩色显示目录内容"""
        print(ColorfulProgressBar.color_text("\n" + "="*70, 'cyan'))
        print(ColorfulProgressBar.color_text("📂 目录内容: ", 'yellow') + ColorfulProgressBar.color_text(str(self.target_path), 'cyan'))
        print(ColorfulProgressBar.color_text("="*70, 'cyan'))
        
        # 显示文件夹
        if self.folders:
            print(ColorfulProgressBar.color_text(f"\n📁 文件夹 ({len(self.folders)}个):", 'green'))
            for i, folder in enumerate(self.folders, 1):
                print(f"  {ColorfulProgressBar.color_text(f'{i:3}.', 'white')} {ColorfulProgressBar.color_text(folder, 'cyan')}")
        else:
            print(ColorfulProgressBar.color_text(f"\n📁 文件夹 (0个):", 'green'))
            print(ColorfulProgressBar.color_text("  没有文件夹", 'white'))
        
        # 显示文件
        if self.files:
            print(ColorfulProgressBar.color_text(f"\n📄 文件 ({len(self.files)}个):", 'green'))
            for i, file in enumerate(self.files, 1):
                print(f"  {ColorfulProgressBar.color_text(f'{i:3}.', 'white')} {ColorfulProgressBar.color_text(file, 'yellow')}")
        else:
            print(ColorfulProgressBar.color_text(f"\n📄 文件 (0个):", 'green'))
            print(ColorfulProgressBar.color_text("  没有文件", 'white'))
        
        print(ColorfulProgressBar.color_text("\n" + "="*70, 'cyan'))
    
    def collect_target_items(self):
        """收集目标目录下的所有文件夹和文件"""
        if not self.target_path.exists():
            raise FileNotFoundError(ColorfulProgressBar.color_text(f"错误: 路径 '{self.target_path}' 不存在", 'red'))
            
        if not self.target_path.is_dir():
            raise NotADirectoryError(ColorfulProgressBar.color_text(f"错误: '{self.target_path}' 不是文件夹", 'red'))
        
        print(ColorfulProgressBar.color_text(f"📂 正在读取目录: ", 'green') + ColorfulProgressBar.color_text(str(self.target_path), 'cyan'))
        
        items = list(self.target_path.iterdir())
        total = len(items)
        
        if total == 0:
            print(ColorfulProgressBar.color_text("目标目录为空", 'yellow'))
            return
        
        for i, item in enumerate(items, 1):
            if item.is_dir():
                self.folders.append(item.name)
            elif item.is_file():
                self.files.append(item.name)
            
            # 显示进度
            ColorfulProgressBar.display_progress("扫描目录", i, total, 'green')
        
        ColorfulProgressBar.complete_progress("扫描目录", total, 'green')
        print(ColorfulProgressBar.color_text(f"✅ 找到 ", 'green') + 
              ColorfulProgressBar.color_text(f"{len(self.folders)}", 'cyan') + 
              ColorfulProgressBar.color_text(f" 个文件夹, ", 'green') + 
              ColorfulProgressBar.color_text(f"{len(self.files)}", 'cyan') + 
              ColorfulProgressBar.color_text(f" 个文件", 'green'))
        
        # 显示目录内容
        self.display_directory_contents()
    
    def search_folder_in_system(self, folder_name, thread_id=0):
        """在整个Windows系统中搜索文件夹"""
        for root in self.search_roots:
            root_path = Path(root)
            if not root_path.exists():
                continue
                
            # 显示当前搜索路径
            if self.show_search_paths:
                print(f"\r{ColorfulProgressBar.color_text(f'线程{thread_id}:', 'magenta')} "
                      f"{ColorfulProgressBar.color_text('正在搜索', 'cyan')} "
                      f"{ColorfulProgressBar.color_text(f'📁 {folder_name}', 'yellow')} "
                      f"{ColorfulProgressBar.color_text('在路径', 'cyan')} "
                      f"{ColorfulProgressBar.color_text(str(root_path), 'blue')}",
                      end='', flush=True)
            
            try:
                for dirpath, dirnames, _ in os.walk(root_path):
                    if folder_name in dirnames:
                        # 找到时显示
                        if self.show_search_items:
                            print(f"\r{ColorfulProgressBar.color_text(f'线程{thread_id}:', 'magenta')} "
                                  f"{ColorfulProgressBar.color_text('✅ 找到', 'green')} "
                                  f"{ColorfulProgressBar.color_text(f'📁 {folder_name}', 'yellow')} "
                                  f"{ColorfulProgressBar.color_text('在', 'green')} "
                                  f"{ColorfulProgressBar.color_text(str(Path(dirpath) / folder_name), 'cyan')}")
                        return True, str(Path(dirpath) / folder_name)
            except (PermissionError, OSError):
                continue  # 跳过没有权限的目录
            except Exception:
                continue
        
        # 未找到时显示
        if self.show_search_items:
            print(f"\r{ColorfulProgressBar.color_text(f'线程{thread_id}:', 'magenta')} "
                  f"{ColorfulProgressBar.color_text('❌ 未找到', 'red')} "
                  f"{ColorfulProgressBar.color_text(f'📁 {folder_name}', 'yellow')}")
        
        return False, None
    
    def search_file_in_system(self, file_name, thread_id=0):
        """在整个Windows系统中搜索文件"""
        for root in self.search_roots:
            root_path = Path(root)
            if not root_path.exists():
                continue
            
            # 显示当前搜索路径
            if self.show_search_paths:
                print(f"\r{ColorfulProgressBar.color_text(f'线程{thread_id}:', 'magenta')} "
                      f"{ColorfulProgressBar.color_text('正在搜索', 'cyan')} "
                      f"{ColorfulProgressBar.color_text(f'📄 {file_name}', 'yellow')} "
                      f"{ColorfulProgressBar.color_text('在路径', 'cyan')} "
                      f"{ColorfulProgressBar.color_text(str(root_path), 'blue')}",
                      end='', flush=True)
            
            try:
                for dirpath, _, filenames in os.walk(root_path):
                    if file_name in filenames:
                        # 找到时显示
                        if self.show_search_items:
                            print(f"\r{ColorfulProgressBar.color_text(f'线程{thread_id}:', 'magenta')} "
                                  f"{ColorfulProgressBar.color_text('✅ 找到', 'green')} "
                                  f"{ColorfulProgressBar.color_text(f'📄 {file_name}', 'yellow')} "
                                  f"{ColorfulProgressBar.color_text('在', 'green')} "
                                  f"{ColorfulProgressBar.color_text(str(Path(dirpath) / file_name), 'cyan')}")
                        return True, str(Path(dirpath) / file_name)
            except (PermissionError, OSError):
                continue  # 跳过没有权限的目录
            except Exception:
                continue
        
        # 未找到时显示
        if self.show_search_items:
            print(f"\r{ColorfulProgressBar.color_text(f'线程{thread_id}:', 'magenta')} "
                  f"{ColorfulProgressBar.color_text('❌ 未找到', 'red')} "
                  f"{ColorfulProgressBar.color_text(f'📄 {file_name}', 'yellow')}")
        
        return False, None
    
    def update_folder_progress(self):
        """更新文件夹搜索进度"""
        while self.progress_folders < len(self.folders):
            ColorfulProgressBar.display_progress("文件夹搜索进度", self.progress_folders, len(self.folders), 'cyan')
            time.sleep(0.1)
    
    def update_file_progress(self):
        """更新文件搜索进度"""
        while self.progress_files < len(self.files):
            ColorfulProgressBar.display_progress("文件搜索进度", self.progress_files, len(self.files), 'yellow')
            time.sleep(0.1)
    
    def display_search_status(self):
        """显示当前搜索状态"""
        print(ColorfulProgressBar.color_text("\n" + "="*70, 'cyan'))
        print(ColorfulProgressBar.color_text("🔍 实时搜索状态", 'yellow'))
        print(ColorfulProgressBar.color_text("="*70, 'cyan'))
        
        print(f"\n{ColorfulProgressBar.color_text('正在搜索文件夹:', 'green')} {ColorfulProgressBar.color_text(str(len(self.folders)), 'cyan')}")
        print(f"{ColorfulProgressBar.color_text('正在搜索文件:', 'green')} {ColorfulProgressBar.color_text(str(len(self.files)), 'cyan')}")
        print(f"{ColorfulProgressBar.color_text('搜索根目录:', 'green')} {ColorfulProgressBar.color_text(str(len(self.search_roots)), 'cyan')}")
        print(f"{ColorfulProgressBar.color_text('显示搜索路径:', 'green')} {ColorfulProgressBar.color_text('是' if self.show_search_paths else '否', 'cyan')}")
        print(f"{ColorfulProgressBar.color_text('显示搜索项目:', 'green')} {ColorfulProgressBar.color_text('是' if self.show_search_items else '否', 'cyan')}")
        
        if self.search_roots:
            print(f"\n{ColorfulProgressBar.color_text('搜索路径列表:', 'green')}")
            for i, root in enumerate(self.search_roots[:5], 1):
                print(f"  {ColorfulProgressBar.color_text(f'{i}.', 'white')} {ColorfulProgressBar.color_text(root, 'blue')}")
            if len(self.search_roots) > 5:
                print(f"  {ColorfulProgressBar.color_text(f'... 还有 {len(self.search_roots) - 5} 个路径', 'white')}")
        
        print(ColorfulProgressBar.color_text("\n" + "="*70, 'cyan'))
        print(ColorfulProgressBar.color_text("开始搜索... 按 Ctrl+C 可中断搜索", 'yellow'))
    
    def search_items_parallel(self, max_workers=4):
        """并行搜索文件夹和文件，使用彩色进度条"""
        total_items = len(self.folders) + len(self.files)
        
        # 如果没有项目需要搜索，直接返回
        if total_items == 0:
            print(ColorfulProgressBar.color_text("没有项目需要搜索", 'yellow'))
            return
        
        # 显示搜索状态
        self.display_search_status()
        
        start_time = time.time()
        
        # 重置进度计数器
        self.progress_folders = 0
        self.progress_files = 0
        
        # 线程ID分配器
        thread_counter = 0
        
        # 搜索文件夹
        if self.folders:
            print(ColorfulProgressBar.color_text(f"\n📁 开始搜索文件夹 ({len(self.folders)}个)...", 'magenta'))
            
            # 启动进度条线程
            progress_thread = threading.Thread(target=self.update_folder_progress)
            progress_thread.daemon = True
            progress_thread.start()
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_folder = {}
                for folder in self.folders:
                    thread_counter += 1
                    thread_id = thread_counter % max_workers if max_workers > 0 else thread_counter
                    future = executor.submit(self.search_folder_in_system, folder, thread_id)
                    future_to_folder[future] = folder
                
                for future in as_completed(future_to_folder):
                    folder = future_to_folder[future]
                    try:
                        found, path = future.result()
                        if found:
                            self.results['folders_found'].append((folder, path))
                        else:
                            self.results['folders_not_found'].append(folder)
                    except Exception as e:
                        print(ColorfulProgressBar.color_text(f"搜索文件夹 '{folder}' 时出错: {e}", 'red'))
                    finally:
                        self.progress_folders += 1
            
            ColorfulProgressBar.complete_progress("文件夹搜索", len(self.folders), 'cyan')
        
        # 搜索文件
        if self.files:
            print(ColorfulProgressBar.color_text(f"\n📄 开始搜索文件 ({len(self.files)}个)...", 'magenta'))
            
            # 启动进度条线程
            progress_thread = threading.Thread(target=self.update_file_progress)
            progress_thread.daemon = True
            progress_thread.start()
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {}
                for file in self.files:
                    thread_counter += 1
                    thread_id = thread_counter % max_workers if max_workers > 0 else thread_counter
                    future = executor.submit(self.search_file_in_system, file, thread_id)
                    future_to_file[future] = file
                
                for future in as_completed(future_to_file):
                    file = future_to_file[future]
                    try:
                        found, path = future.result()
                        if found:
                            self.results['files_found'].append((file, path))
                        else:
                            self.results['files_not_found'].append(file)
                    except Exception as e:
                        print(ColorfulProgressBar.color_text(f"搜索文件 '{file}' 时出错: {e}", 'red'))
                    finally:
                        self.progress_files += 1
            
            ColorfulProgressBar.complete_progress("文件搜索", len(self.files), 'yellow')
        
        end_time = time.time()
        
        # 清除最后一行的搜索状态显示
        if self.show_search_paths:
            print("\r" + " " * 150 + "\r", end='', flush=True)
        
        # 显示搜索统计信息
        self.display_search_statistics(start_time, end_time)
    
    def display_search_statistics(self, start_time, end_time):
        """显示搜索统计信息"""
        print(ColorfulProgressBar.color_text("\n" + "="*70, 'cyan'))
        print(ColorfulProgressBar.color_text("📊 搜索完成 - 统计信息", 'yellow'))
        print(ColorfulProgressBar.color_text("="*70, 'cyan'))
        
        # 计算耗时
        search_time = end_time - start_time
        
        # 文件夹统计
        folders_found = len(self.results['folders_found'])
        folders_not_found = len(self.results['folders_not_found'])
        folders_total = len(self.folders)
        
        # 文件统计
        files_found = len(self.results['files_found'])
        files_not_found = len(self.results['files_not_found'])
        files_total = len(self.files)
        
        # 总体统计
        total_found = folders_found + files_found
        total_not_found = folders_not_found + files_not_found
        total_items = folders_total + files_total
        
        print(f"\n{ColorfulProgressBar.color_text('⏱️  搜索耗时:', 'green')} {ColorfulProgressBar.color_text(f'{search_time:.2f} 秒', 'cyan')}")
        
        # 文件夹统计
        print(ColorfulProgressBar.color_text("\n📁 文件夹统计:", 'green'))
        print(f"  {ColorfulProgressBar.color_text('总数:', 'white')} {ColorfulProgressBar.color_text(f'{folders_total}', 'cyan')}")
        if folders_total > 0:
            print(f"  {ColorfulProgressBar.color_text('✅ 存在的:', 'green')} {ColorfulProgressBar.color_text(f'{folders_found}', 'cyan')} "
                  f"({ColorfulProgressBar.color_text(f'{folders_found/folders_total*100:.1f}%', 'green')})")
            print(f"  {ColorfulProgressBar.color_text('❌ 不存在的:', 'red')} {ColorfulProgressBar.color_text(f'{folders_not_found}', 'cyan')} "
                  f"({ColorfulProgressBar.color_text(f'{folders_not_found/folders_total*100:.1f}%', 'red')})")
        else:
            print(f"  {ColorfulProgressBar.color_text('✅ 存在的:', 'green')} {ColorfulProgressBar.color_text('0', 'cyan')} (0%)")
            print(f"  {ColorfulProgressBar.color_text('❌ 不存在的:', 'red')} {ColorfulProgressBar.color_text('0', 'cyan')} (0%)")
        
        # 文件统计
        print(ColorfulProgressBar.color_text("\n📄 文件统计:", 'green'))
        print(f"  {ColorfulProgressBar.color_text('总数:', 'white')} {ColorfulProgressBar.color_text(f'{files_total}', 'cyan')}")
        if files_total > 0:
            print(f"  {ColorfulProgressBar.color_text('✅ 存在的:', 'green')} {ColorfulProgressBar.color_text(f'{files_found}', 'cyan')} "
                  f"({ColorfulProgressBar.color_text(f'{files_found/files_total*100:.1f}%', 'green')})")
            print(f"  {ColorfulProgressBar.color_text('❌ 不存在的:', 'red')} {ColorfulProgressBar.color_text(f'{files_not_found}', 'cyan')} "
                  f"({ColorfulProgressBar.color_text(f'{files_not_found/files_total*100:.1f}%', 'red')})")
        else:
            print(f"  {ColorfulProgressBar.color_text('✅ 存在的:', 'green')} {ColorfulProgressBar.color_text('0', 'cyan')} (0%)")
            print(f"  {ColorfulProgressBar.color_text('❌ 不存在的:', 'red')} {ColorfulProgressBar.color_text('0', 'cyan')} (0%)")
        
        # 总体统计
        print(ColorfulProgressBar.color_text("\n📈 总体统计:", 'green'))
        print(f"  {ColorfulProgressBar.color_text('总数:', 'white')} {ColorfulProgressBar.color_text(f'{total_items}', 'cyan')}")
        if total_items > 0:
            print(f"  {ColorfulProgressBar.color_text('✅ 存在的:', 'green')} {ColorfulProgressBar.color_text(f'{total_found}', 'cyan')} "
                  f"({ColorfulProgressBar.color_text(f'{total_found/total_items*100:.1f}%', 'green')})")
            print(f"  {ColorfulProgressBar.color_text('❌ 不存在的:', 'red')} {ColorfulProgressBar.color_text(f'{total_not_found}', 'cyan')} "
                  f"({ColorfulProgressBar.color_text(f'{total_not_found/total_items*100:.1f}%', 'red')})")
        else:
            print(f"  {ColorfulProgressBar.color_text('✅ 存在的:', 'green')} {ColorfulProgressBar.color_text('0', 'cyan')} (0%)")
            print(f"  {ColorfulProgressBar.color_text('❌ 不存在的:', 'red')} {ColorfulProgressBar.color_text('0', 'cyan')} (0%)")
        
        # 显示搜索效率
        if search_time > 0 and total_items > 0:
            items_per_second = total_items / search_time
            print(f"\n{ColorfulProgressBar.color_text('⚡ 搜索效率:', 'green')} "
                  f"{ColorfulProgressBar.color_text(f'{items_per_second:.1f} 个项目/秒', 'cyan')}")
        
        print(ColorfulProgressBar.color_text("\n" + "="*70, 'cyan'))
    
    def display_detailed_results(self):
        """显示详细结果（不存在的项目列表）"""
        # 显示不存在的文件夹
        if self.results['folders_not_found']:
            print(ColorfulProgressBar.color_text(f"\n📁 不存在的文件夹 ({len(self.results['folders_not_found'])}个):", 'red'))
            for i, folder in enumerate(self.results['folders_not_found'], 1):
                print(f"  {ColorfulProgressBar.color_text(f'{i:3}.', 'white')} {ColorfulProgressBar.color_text(folder, 'red')}")
        else:
            print(ColorfulProgressBar.color_text(f"\n📁 不存在的文件夹 (0个)", 'red'))
        
        # 显示不存在的文件
        if self.results['files_not_found']:
            print(ColorfulProgressBar.color_text(f"\n📄 不存在的文件 ({len(self.results['files_not_found'])}个):", 'red'))
            for i, file in enumerate(self.results['files_not_found'], 1):
                print(f"  {ColorfulProgressBar.color_text(f'{i:3}.', 'white')} {ColorfulProgressBar.color_text(file, 'red')}")
        else:
            print(ColorfulProgressBar.color_text(f"\n📄 不存在的文件 (0个)", 'red'))
        
        # 询问是否显示存在的项目
        show_found = input(ColorfulProgressBar.color_text(f"\n是否显示在系统中存在的项目？(y/n, 回车默认n): ", 'yellow')).strip().lower()
        if show_found == 'y':
            # 显示存在的文件夹
            if self.results['folders_found']:
                print(ColorfulProgressBar.color_text(f"\n📁 存在的文件夹 ({len(self.results['folders_found'])}个):", 'green'))
                for i, (folder, path) in enumerate(self.results['folders_found'][:10], 1):
                    print(f"  {ColorfulProgressBar.color_text(f'{i:2}.', 'white')} "
                          f"{ColorfulProgressBar.color_text(f'{folder}', 'cyan')} "
                          f"{ColorfulProgressBar.color_text('→', 'white')} "
                          f"{ColorfulProgressBar.color_text(f'{path}', 'yellow')}")
                if len(self.results['folders_found']) > 10:
                    print(f"  {ColorfulProgressBar.color_text(f'... 还有 {len(self.results["folders_found"]) - 10} 个文件夹', 'white')}")
            else:
                print(ColorfulProgressBar.color_text(f"\n📁 存在的文件夹 (0个)", 'green'))
            
            # 显示存在的文件
            if self.results['files_found']:
                print(ColorfulProgressBar.color_text(f"\n📄 存在的文件 ({len(self.results['files_found'])}个):", 'green'))
                for i, (file, path) in enumerate(self.results['files_found'][:10], 1):
                    print(f"  {ColorfulProgressBar.color_text(f'{i:2}.', 'white')} "
                          f"{ColorfulProgressBar.color_text(f'{file}', 'cyan')} "
                          f"{ColorfulProgressBar.color_text('→', 'white')} "
                          f"{ColorfulProgressBar.color_text(f'{path}', 'yellow')}")
                if len(self.results['files_found']) > 10:
                    print(f"  {ColorfulProgressBar.color_text(f'... 还有 {len(self.results["files_found"]) - 10} 个文件', 'white')}")
            else:
                print(ColorfulProgressBar.color_text(f"\n📄 存在的文件 (0个)", 'green'))
    
    def display_results(self):
        """显示所有结果"""
        # 显示不存在的项目
        if self.results['folders_not_found'] or self.results['files_not_found']:
            show_not_found = input(ColorfulProgressBar.color_text(f"\n是否显示不存在的项目列表？(y/n, 回车默认y): ", 'yellow')).strip().lower()
            if show_not_found != 'n':
                self.display_detailed_results()
        else:
            print(ColorfulProgressBar.color_text(f"\n🎉 恭喜！所有项目在系统中都存在！", 'green'))
    
    def save_results(self):
        """保存结果到文件 - 修复中文编码和除零错误"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = f"search_results_{timestamp}.txt"
        
        try:
            # 使用utf-8编码保存文件，处理中文字符
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("文件系统搜索报告\n")
                f.write("="*70 + "\n")
                f.write(f"搜索目录: {self.target_path}\n")
                f.write(f"搜索时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("\n")
                
                # 写入目录内容
                f.write("目录内容:\n")
                f.write(f"  文件夹: {len(self.folders)} 个\n")
                for folder in self.folders:
                    # 确保文件夹名是字符串
                    folder_str = str(folder)
                    f.write(f"    - {folder_str}\n")
                
                f.write(f"\n  文件: {len(self.files)} 个\n")
                for file in self.files:
                    # 确保文件名是字符串
                    file_str = str(file)
                    f.write(f"    - {file_str}\n")
                
                f.write("\n" + "="*70 + "\n")
                
                # 写入统计信息
                f.write("搜索结果统计:\n\n")
                
                # 文件夹统计
                folders_found = len(self.results['folders_found'])
                folders_not_found = len(self.results['folders_not_found'])
                folders_total = len(self.folders)
                
                f.write("文件夹统计:\n")
                f.write(f"  总数: {folders_total}\n")
                # 修复除零错误
                if folders_total > 0:
                    f.write(f"  存在的: {folders_found} ({folders_found/folders_total*100:.1f}%)\n")
                    f.write(f"  不存在的: {folders_not_found} ({folders_not_found/folders_total*100:.1f}%)\n\n")
                else:
                    f.write(f"  存在的: {folders_found} (0%)\n")
                    f.write(f"  不存在的: {folders_not_found} (0%)\n\n")
                
                # 文件统计
                files_found = len(self.results['files_found'])
                files_not_found = len(self.results['files_not_found'])
                files_total = len(self.files)
                
                f.write("文件统计:\n")
                f.write(f"  总数: {files_total}\n")
                # 修复除零错误
                if files_total > 0:
                    f.write(f"  存在的: {files_found} ({files_found/files_total*100:.1f}%)\n")
                    f.write(f"  不存在的: {files_not_found} ({files_not_found/files_total*100:.1f}%)\n\n")
                else:
                    f.write(f"  存在的: {files_found} (0%)\n")
                    f.write(f"  不存在的: {files_not_found} (0%)\n\n")
                
                # 总体统计
                total_found = folders_found + files_found
                total_not_found = folders_not_found + files_not_found
                total_items = folders_total + files_total
                
                f.write("总体统计:\n")
                f.write(f"  总数: {total_items}\n")
                # 修复除零错误
                if total_items > 0:
                    f.write(f"  存在的: {total_found} ({total_found/total_items*100:.1f}%)\n")
                    f.write(f"  不存在的: {total_not_found} ({total_not_found/total_items*100:.1f}%)\n\n")
                else:
                    f.write(f"  存在的: {total_found} (0%)\n")
                    f.write(f"  不存在的: {total_not_found} (0%)\n\n")
                
                # 写入不存在的文件夹
                if self.results['folders_not_found']:
                    f.write("不存在的文件夹:\n")
                    for folder in self.results['folders_not_found']:
                        folder_str = str(folder)
                        f.write(f"  - {folder_str}\n")
                    f.write("\n")
                
                # 写入不存在的文件
                if self.results['files_not_found']:
                    f.write("不存在的文件:\n")
                    for file in self.results['files_not_found']:
                        file_str = str(file)
                        f.write(f"  - {file_str}\n")
                    f.write("\n")
                
                # 写入存在的文件夹
                if self.results['folders_found']:
                    f.write("存在的文件夹:\n")
                    for folder, path in self.results['folders_found']:
                        folder_str = str(folder)
                        path_str = str(path)
                        f.write(f"  - {folder_str} (位置: {path_str})\n")
                    f.write("\n")
                
                # 写入存在的文件
                if self.results['files_found']:
                    f.write("存在的文件:\n")
                    for file, path in self.results['files_found']:
                        file_str = str(file)
                        path_str = str(path)
                        f.write(f"  - {file_str} (位置: {path_str})\n")
            
            print(ColorfulProgressBar.color_text(f"\n✅ 结果已保存到: ", 'green') + 
                  ColorfulProgressBar.color_text(f"{os.path.abspath(output_file)}", 'cyan'))
            return True
        except UnicodeEncodeError as e:
            print(ColorfulProgressBar.color_text(f"保存文件时编码错误，尝试使用另一种编码...", 'red'))
            try:
                # 尝试使用另一种编码
                with open(output_file, 'w', encoding='gbk') as f:
                    f.write("文件系统搜索报告\n")
                    f.write("="*70 + "\n")
                    f.write(f"搜索目录: {self.target_path}\n")
                    f.write(f"搜索时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    # 简化内容避免编码问题
                    f.write(f"\n文件夹总数: {len(self.folders)}\n")
                    f.write(f"文件总数: {len(self.files)}\n")
                print(ColorfulProgressBar.color_text(f"\n✅ 结果已保存到 (使用GBK编码): ", 'green') + 
                      ColorfulProgressBar.color_text(f"{os.path.abspath(output_file)}", 'cyan'))
                return True
            except Exception as e2:
                print(ColorfulProgressBar.color_text(f"保存文件时出错: {e2}", 'red'))
                return False
        except Exception as e:
            print(ColorfulProgressBar.color_text(f"保存文件时出错: {e}", 'red'))
            return False

def configure_search():
    """配置搜索选项"""
    print(ColorfulProgressBar.color_text("\n" + "="*70, 'cyan'))
    print(ColorfulProgressBar.color_text("🔧 配置搜索选项", 'yellow'))
    print(ColorfulProgressBar.color_text("="*70, 'cyan'))
    
    print(ColorfulProgressBar.color_text(f"\n搜索范围:", 'green'))
    print(f"  {ColorfulProgressBar.color_text('1.', 'cyan')} {ColorfulProgressBar.color_text('整个系统', 'white')} {ColorfulProgressBar.color_text('(推荐)', 'yellow')}")
    print(f"  {ColorfulProgressBar.color_text('2.', 'cyan')} {ColorfulProgressBar.color_text('仅当前驱动器', 'white')}")
    print(f"  {ColorfulProgressBar.color_text('3.', 'cyan')} {ColorfulProgressBar.color_text('自定义搜索路径', 'white')}")
    
    choice = input(ColorfulProgressBar.color_text(f"\n请选择搜索范围 (1-3, 回车默认1): ", 'yellow')).strip()
    
    search_roots = []
    if choice == '2':
        # 仅当前驱动器
        current_drive = Path.cwd().drive
        search_roots = [current_drive + "\\"]
        print(ColorfulProgressBar.color_text(f"将仅在 ", 'green') + 
              ColorfulProgressBar.color_text(f"{current_drive}", 'cyan') + 
              ColorfulProgressBar.color_text(f" 驱动器中搜索", 'green'))
    elif choice == '3':
        # 自定义路径
        custom_paths = input(ColorfulProgressBar.color_text(f"请输入要搜索的路径 (多个路径用分号分隔): ", 'yellow')).strip()
        search_roots = [p.strip() for p in custom_paths.split(';') if p.strip()]
        print(ColorfulProgressBar.color_text(f"将在 ", 'green') + 
              ColorfulProgressBar.color_text(f"{len(search_roots)}", 'cyan') + 
              ColorfulProgressBar.color_text(f" 个自定义路径中搜索", 'green'))
    else:
        # 整个系统
        search_roots = [
            "C:\\", "D:\\", "E:\\", "F:\\", "G:\\",
            os.path.expanduser("~"),
            "C:\\Program Files", "C:\\Program Files (x86)",
            "C:\\Windows", "C:\\Users"
        ]
        print(ColorfulProgressBar.color_text(f"将在整个系统中搜索", 'green'))
    
    return search_roots

def configure_display_options():
    """配置显示选项"""
    print(ColorfulProgressBar.color_text(f"\n显示选项:", 'green'))
    
    show_search_paths = input(ColorfulProgressBar.color_text(f"  是否显示搜索路径？(y/n, 回车默认y): ", 'yellow')).strip().lower()
    show_search_items = input(ColorfulProgressBar.color_text(f"  是否显示正在搜索的项目？(y/n, 回车默认y): ", 'yellow')).strip().lower()
    
    return show_search_paths != 'n', show_search_items != 'n'

def main():
    print(ColorfulProgressBar.color_text("="*70, 'cyan'))
    print(ColorfulProgressBar.color_text("🚀 Windows系统文件搜索工具", 'yellow'))
    print(ColorfulProgressBar.color_text("="*70, 'cyan'))
    
    # 设置要读取的目录路径
    target_directory = input(ColorfulProgressBar.color_text(f"\n请输入要读取的目录路径 (直接回车使用当前目录): ", 'yellow')).strip()
    
    if not target_directory:
        target_directory = os.getcwd()
        print(ColorfulProgressBar.color_text(f"使用当前目录: ", 'green') + 
              ColorfulProgressBar.color_text(f"{target_directory}", 'cyan'))
    
    try:
        # 创建搜索器
        searcher = SystemSearcher(target_directory)
        
        # 配置搜索选项
        search_roots = configure_search()
        if search_roots:
            searcher.search_roots = search_roots
        
        # 配置显示选项
        show_search_paths, show_search_items = configure_display_options()
        searcher.show_search_paths = show_search_paths
        searcher.show_search_items = show_search_items
        
        # 收集目标项目
        searcher.collect_target_items()
        
        if not searcher.folders and not searcher.files:
            print(ColorfulProgressBar.color_text(f"目标目录中没有文件夹或文件", 'yellow'))
            return
        
        # 确认是否开始搜索
        print(ColorfulProgressBar.color_text(f"\n" + "="*70, 'cyan'))
        confirm = input(ColorfulProgressBar.color_text(f"是否开始在整个系统中搜索这些项目？(y/n, 回车默认n): ", 'yellow')).strip().lower()
        
        if confirm != 'y':
            print(ColorfulProgressBar.color_text(f"搜索已取消", 'yellow'))
            return
        
        # 执行搜索
        searcher.search_items_parallel()
        
        # 显示详细结果
        searcher.display_results()
        
        # 询问是否保存结果
        save_choice = input(ColorfulProgressBar.color_text(f"\n是否将结果保存到文件？(y/n, 回车默认y): ", 'yellow')).strip().lower()
        if save_choice != 'n':
            searcher.save_results()
        
    except (FileNotFoundError, NotADirectoryError) as e:
        print(ColorfulProgressBar.color_text(f"{e}", 'red'))
    except KeyboardInterrupt:
        print(ColorfulProgressBar.color_text(f"\n\n程序被用户中断", 'yellow'))
    except Exception as e:
        print(ColorfulProgressBar.color_text(f"程序出错: {e}", 'red'))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        main()
        input(ColorfulProgressBar.color_text(f"\n按回车键退出...", 'yellow'))
    except KeyboardInterrupt:
        print(ColorfulProgressBar.color_text(f"\n程序被用户中断", 'yellow'))
        sys.exit(0)