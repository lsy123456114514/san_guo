#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动更新模块 - 支持多种更新源
"""

import os
import sys
import subprocess
import tempfile
import zipfile
import shutil
import time
import urllib.request
import urllib.error
import hashlib

from ASSET.game_data import logger, draw_gradient_bg, cull_dead, get_font

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# FTP 支持
try:
    import ftplib
    HAS_FTP = True
except ImportError:
    HAS_FTP = False

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (50, 200, 50)
RED = (220, 50, 50)
BLUE = (50, 100, 255)
GRAY = (128, 128, 128)

class AutoUpdater:
    def __init__(self, screen=None):
        self.screen = screen
        self.clock = None
        self.font = None
        self.font_small = None
        self.running = True
        self.download_progress = 0
        self.status_text = ""
        self.error_message = ""
        self.update_info = None
        self.current_version = "1.0"  # 当前版本，需要和游戏版本同步
        self.init_pygame()
    
    def init_pygame(self):
        """初始化 pygame"""
        if self.screen is None:
            pygame.init()
            self.screen = pygame.display.set_mode((600, 400))
            pygame.display.set_caption("自动更新")
            self.clock = pygame.time.Clock()
        
        try:
            self.font = pygame.font.SysFont("Microsoft YaHei", 24)
            self.font_small = pygame.font.SysFont("Microsoft YaHei", 16)
        except Exception as _e:
            self.font = pygame.font.Font(None, 24)
            self.font_small = pygame.font.Font(None, 16)
    
    def draw_progress_bar(self, progress, width=500, height=30):
        """绘制进度条"""
        x = (self.screen.get_width() - width) // 2
        y = 200
        
        # 背景
        pygame.draw.rect(self.screen, GRAY, (x, y, width, height), border_radius=5)
        # 进度
        pygame.draw.rect(self.screen, BLUE, (x, y, int(width * progress), height), border_radius=5)
        # 边框
        pygame.draw.rect(self.screen, BLACK, (x, y, width, height), 2, border_radius=5)
        
        # 文字
        text = self.font.render(f"下载进度: {int(progress * 100)}%", True, BLACK)
        text_rect = text.get_rect(center=(x + width // 2, y + height // 2))
        self.screen.blit(text, text_rect)
    
    def draw_status(self):
        """绘制状态信息"""
        y = 100
        for i, line in enumerate(self.status_text.split('\n')):
            text = self.font_small.render(line, True, BLACK)
            self.screen.blit(text, (50, y + i * 25))
        
        if self.error_message:
            text = self.font.render(self.error_message, True, RED)
            text_rect = text.get_rect(center=(self.screen.get_width() // 2, 300))
            self.screen.blit(text, text_rect)
    
    def download_file(self, url, local_path, show_progress=True):
        """下载文件"""
        try:
            if HAS_REQUESTS:
                t0 = time.perf_counter()
                logger.info("[更新] 开始下载 requests.get stream %s (timeout=30s)", url)
                response = requests.get(url, stream=True, timeout=30)
                total_size = int(response.headers.get('content-length', 0))
                logger.info("[更新] 响应头状态=%s total_size=%d 已连接耗时 %.3fs",
                            response.status_code, total_size, time.perf_counter() - t0)

                with open(local_path, 'wb') as f:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0 and show_progress:
                                self.download_progress = downloaded / total_size
                logger.info("[更新] 下载完成 %.3fs, 写入 %d 字节 -> %s",
                            time.perf_counter() - t0, downloaded, local_path)
            else:
                t0 = time.perf_counter()
                logger.info("[更新] 开始下载 urllib.urlretrieve %s", url)
                urllib.request.urlretrieve(url, local_path)
                logger.info("[更新] urlretrieve 完成 %.3fs -> %s",
                            time.perf_counter() - t0, local_path)
                self.download_progress = 1.0

            return True
        except Exception as e:
            duration = time.perf_counter() - locals().get('t0', time.perf_counter())
            logger.error("[更新] 下载失败 耗时约%.3fs url=%s err=%s", duration, url, e, exc_info=True)
            self.error_message = f"下载失败: {str(e)}"
            return False
    
    def check_ftp_updates(self, host, port, user, password, path="/"):
        """检查 FTP 更新"""
        if not HAS_FTP:
            self.error_message = "FTP 模块不可用"
            logger.warning("[更新] check_ftp_updates: ftplib 模块不可用")
            return None

        t0 = time.perf_counter()
        phase = "connect"
        try:
            logger.info("[更新] FTP 检查更新 host=%s port=%s user=%s path=%s", host, port, user, path)
            ftp = ftplib.FTP()
            phase = "connect"
            ftp.connect(host, port)
            dt_conn = time.perf_counter() - t0
            logger.info("[更新] FTP connect 成功 耗时 %.3fs", dt_conn)
            phase = "login"
            ftp.login(user, password)
            dt_login = time.perf_counter() - t0
            logger.info("[更新] FTP login 成功 累计耗时 %.3fs", dt_login)

            if path != "/":
                phase = f"cwd({path})"
                ftp.cwd(path)

            # 获取文件列表
            phase = "LIST"
            files = []
            t_list = time.perf_counter()
            ftp.retrlines('LIST', lambda x: files.append(x))
            logger.info("[更新] FTP LIST 完成 条目数=%d 单独耗时 %.3fs",
                        len(files), time.perf_counter() - t_list)

            # 解析文件名和修改时间
            exe_files = []
            for line in files:
                parts = line.split()
                if len(parts) >= 9:
                    filename = ' '.join(parts[8:])
                    if filename.endswith('.exe'):
                        exe_files.append(filename)

            phase = "quit"
            ftp.quit()

            if not exe_files:
                logger.info("[更新] FTP 目录中无 EXE 文件 总耗时 %.3fs", time.perf_counter() - t0)
                return None

            # 获取版本号（文件名格式: Game_v2.0.exe）
            versions = []
            for filename in exe_files:
                try:
                    version = filename.replace('.exe', '').split('_v')[-1]
                    versions.append((version, filename))
                except Exception as _e:
                    logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)

            if not versions:
                logger.info("[更新] FTP EXE 文件名解析未匹配版本号模式 总耗时 %.3fs", time.perf_counter() - t0)
                return None

            # 找到最新版本
            latest_version, latest_file = max(versions, key=lambda x: x[0])
            logger.info("[更新] FTP 检查完成 最新版本=%s 文件=%s 总耗时 %.3fs",
                        latest_version, latest_file, time.perf_counter() - t0)

            return {
                'version': latest_version,
                'download_url': f"ftp://{user}:{password}@{host}:{port}{path}/{latest_file}",
                'file_name': latest_file,
                'ftp_host': host,
                'ftp_port': port,
                'ftp_user': user,
                'ftp_pass': password,
                'ftp_path': path
            }
        except Exception as e:
            duration = time.perf_counter() - t0
            logger.error(
                "[更新] FTP 检查失败 阶段=%s 类型=%s 耗时≈%.3fs host=%s err=%s",
                phase, type(e).__name__, duration, host, e, exc_info=True,
            )
            self.error_message = f"FTP 连接失败 ({phase}): {str(e)}"
            return None

    def download_from_ftp(self, host, port, user, password, remote_path, local_path):
        """从 FTP 下载文件"""
        if not HAS_FTP:
            logger.warning("[更新] download_from_ftp: ftplib 模块不可用")
            return False

        t0 = time.perf_counter()
        phase = "connect"
        try:
            logger.info("[更新] FTP 开始下载 host=%s port=%s remote=%s -> local=%s",
                        host, port, remote_path, local_path)
            ftp = ftplib.FTP()
            phase = "connect"
            ftp.connect(host, port)
            phase = "login"
            ftp.login(user, password)

            # 获取文件大小
            phase = "SIZE"
            try:
                file_size = ftp.size(remote_path)
            except Exception as _e:
                file_size = 0
            logger.info("[更新] FTP 登录成功 remote_size=%d 累计耗时 %.3fs",
                        file_size, time.perf_counter() - t0)

            # 下载文件
            phase = f"RETR {remote_path}"
            t_dl = time.perf_counter()
            with open(local_path, 'wb') as f:
                downloaded = 0
                def callback(data):
                    nonlocal downloaded
                    f.write(data)
                    downloaded += len(data)
                    if file_size > 0:
                        self.download_progress = downloaded / file_size

                ftp.retrbinary(f"RETR {remote_path}", callback)

            dt_dl = time.perf_counter() - t_dl
            dt_total = time.perf_counter() - t0
            speed_kb = (downloaded / 1024.0 / dt_dl) if dt_dl > 0 else 0
            logger.info(
                "[更新] FTP 下载完成 写入=%d字节 下载耗时=%.3fs 平均=%.1f KB/s 总耗时=%.3fs",
                downloaded, dt_dl, speed_kb, dt_total,
            )

            phase = "quit"
            ftp.quit()
            return True
        except Exception as e:
            duration = time.perf_counter() - t0
            logger.error(
                "[更新] FTP 下载失败 阶段=%s 类型=%s 耗时≈%.3fs remote=%s err=%s",
                phase, type(e).__name__, duration, remote_path, e, exc_info=True,
            )
            self.error_message = f"FTP 下载失败 ({phase}): {str(e)}"
            return False
    
    def check_pcloud_updates(self, token, folder_id, current_version):
        """检查 pCloud 更新"""
        try:
            # 获取文件夹内容
            url = f"https://api.pcloud.com/listfolder?auth={token}&folderid={folder_id}"
            t0 = time.perf_counter()
            display_url = url.split('?auth=')[0] + '?auth=***'
            logger.info("[更新] pCloud 检查更新 GET %s (timeout=10s)", display_url)
            response = requests.get(url, timeout=10)
            dt = time.perf_counter() - t0
            logger.info("[更新] pCloud 返回 状态=%s 耗时 %.3fs", response.status_code, dt)
            try:
                data = response.json()
            except ValueError as jerr:
                snippet = ""
                try:
                    snippet = response.text[:300].replace("\r", " ").replace("\n", "\\n")
                except Exception as _e:
                    snippet = "<无法读取 body>"
                logger.error(
                    "[更新] pCloud 返回非 JSON！HTTP=%s 耗时=%.3fs Content-Type=%s snippet=%s",
                    response.status_code, dt,
                    response.headers.get('Content-Type', '?'), snippet,
                )
                self.error_message = f"pCloud 返回格式错误（可能是网关超时页/反爬拦截）"
                return None

            if data.get('result') != 0:
                logger.warning("[更新] pCloud result=%s", data.get('result'))
                return None

            files = data.get('files', [])
            exe_files = [f for f in files if f['name'].endswith('.exe')]

            if not exe_files:
                logger.info("[更新] pCloud 文件夹中没有 EXE")
                return None

            # 获取最新的 EXE 文件
            latest = max(exe_files, key=lambda x: x.get('modified', ''))

            return {
                'version': latest.get('name', 'unknown').replace('.exe', '').split('_v')[-1] or current_version,
                'download_url': f"https://api.pcloud.com/getfilepublink?auth={token}&fileid={latest['fileid']}",
                'file_size': latest.get('size', 0),
                'file_name': latest['name']
            }
        except Exception as e:
            duration = time.perf_counter() - locals().get('t0', time.perf_counter())
            logger.error("[更新] pCloud 检查失败 类型=%s 耗时≈%.3fs: %s",
                         type(e).__name__, duration, e, exc_info=True)
            self.error_message = f"检查更新失败: {str(e)}"
            return None

    def check_github_releases(self, repo, current_version):
        """检查 GitHub Releases 更新"""
        try:
            url = f"https://api.github.com/repos/{repo}/releases/latest"
            t0 = time.perf_counter()
            logger.info("[更新] GitHub 检查最新版本 GET %s (timeout=10s)", url)
            response = requests.get(url, timeout=10)
            dt = time.perf_counter() - t0
            logger.info("[更新] GitHub 返回 状态=%s 耗时 %.3fs", response.status_code, dt)

            if response.status_code != 200:
                return None

            try:
                data = response.json()
            except ValueError as jerr:
                snippet = ""
                try:
                    snippet = response.text[:300].replace("\r", " ").replace("\n", "\\n")
                except Exception as _e:
                    snippet = "<无法读取 body>"
                logger.error(
                    "[更新] GitHub 返回非 JSON！HTTP=%s 耗时=%.3fs Content-Type=%s snippet=%s",
                    response.status_code, dt,
                    response.headers.get('Content-Type', '?'), snippet,
                )
                self.error_message = "GitHub 返回格式错误（可能被云提供商/CDN 拦截或网络超时页）"
                return None

            latest_version = data.get('tag_name', '').lstrip('v')

            if latest_version <= current_version:
                logger.info("[更新] GitHub 当前版本已是最新 current=%s latest=%s",
                            current_version, latest_version)
                return None

            # 获取 EXE 文件
            assets = data.get('assets', [])
            exe_asset = next((a for a in assets if a['name'].endswith('.exe')), None)

            if not exe_asset:
                logger.info("[更新] GitHub 最新版本无 EXE 资产")
                return None

            return {
                'version': latest_version,
                'download_url': exe_asset['browser_download_url'],
                'file_size': exe_asset['size'],
                'file_name': exe_asset['name'],
                'changelog': data.get('body', '')
            }
        except Exception as e:
            duration = time.perf_counter() - locals().get('t0', time.perf_counter())
            logger.error("[更新] GitHub 检查失败 类型=%s 耗时≈%.3fs: %s",
                         type(e).__name__, duration, e, exc_info=True)
            self.error_message = f"检查更新失败: {str(e)}"
            return None

    def check_direct_url(self, version_url, download_url_template, current_version):
        """检查直接 URL 更新（用户自定义）"""
        try:
            t0 = time.perf_counter()
            logger.info("[更新] 自定义源 检查版本 GET %s (timeout=10s)", version_url)
            response = requests.get(version_url, timeout=10)
            dt = time.perf_counter() - t0
            logger.info("[更新] 自定义源 返回 状态=%s 耗时 %.3fs", response.status_code, dt)
            try:
                data = response.json()
            except ValueError as jerr:
                snippet = ""
                try:
                    snippet = response.text[:300].replace("\r", " ").replace("\n", "\\n")
                except Exception as _e:
                    snippet = "<无法读取 body>"
                logger.error(
                    "[更新] 自定义源 返回非 JSON！HTTP=%s 耗时=%.3fs Content-Type=%s snippet=%s",
                    response.status_code, dt,
                    response.headers.get('Content-Type', '?'), snippet,
                )
                self.error_message = "自定义版本源返回格式错误（可能是网关超时页或认证被拒）"
                return None
            
            latest_version = data.get('version', '0')

            if latest_version <= current_version:
                logger.info("[更新] 自定义源 当前版本已是最新 current=%s latest=%s",
                            current_version, latest_version)
                return None

            return {
                'version': latest_version,
                'download_url': download_url_template.format(version=latest_version),
                'changelog': data.get('changelog', '')
            }
        except Exception as e:
            duration = time.perf_counter() - locals().get('t0', time.perf_counter())
            logger.error("[更新] 自定义源 检查失败 耗时约%.3fs: %s", duration, e, exc_info=True)
            self.error_message = f"检查更新失败: {str(e)}"
            return None
    
    def download_and_install(self, update_info):
        """下载并安装更新"""
        if not update_info:
            self.status_text = "已是最新版本！"
            return False
        
        self.status_text = f"发现新版本: {update_info['version']}"
        self.status_text += f"\n正在下载: {update_info.get('file_name', 'update.exe')}"
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, update_info.get('file_name', 'update.exe'))
        
        # 下载文件（支持 FTP 和 HTTP）
        success = False
        if update_info.get('ftp_host'):
            # FTP 下载
            remote_path = update_info.get('ftp_path', '/') + '/' + update_info.get('file_name', '')
            if remote_path.startswith('//'):
                remote_path = remote_path[1:]
            success = self.download_from_ftp(
                update_info['ftp_host'],
                update_info['ftp_port'],
                update_info['ftp_user'],
                update_info['ftp_pass'],
                remote_path,
                temp_file
            )
        else:
            # HTTP 下载
            success = self.download_file(update_info['download_url'], temp_file)
        
        if not success:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return False
        
        self.status_text += "\n下载完成！正在安装..."
        
        # 等待一小段时间让用户看到状态
        pygame.time.wait(1000)
        
        # 获取当前 EXE 路径
        current_exe = sys.executable
        if not current_exe.endswith('.exe'):
            current_exe = sys.argv[0]
        
        backup_exe = current_exe + '.bak'
        
        try:
            # 备份旧版本
            if os.path.exists(current_exe):
                if os.path.exists(backup_exe):
                    os.remove(backup_exe)
                shutil.copy2(current_exe, backup_exe)
            
            # 替换为新版本
            shutil.copy2(temp_file, current_exe)
            
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            self.status_text += "\n安装完成！正在重启..."
            pygame.time.wait(1000)
            
            # 重启程序
            subprocess.Popen([current_exe])
            pygame.quit()
            sys.exit(0)
            
        except Exception as e:
            self.error_message = f"安装失败: {str(e)}"
            # 尝试恢复备份
            if os.path.exists(backup_exe):
                shutil.copy2(backup_exe, current_exe)
            return False
    
    def run_update_check(self, source='github', **kwargs):
        """运行更新检查"""
        self.status_text = "正在检查更新..."
        self.error_message = ""
        
        # 根据来源检查更新
        if source == 'ftp':
            host = kwargs.get('host', '')
            port = kwargs.get('port', 21)
            user = kwargs.get('user', '')
            password = kwargs.get('password', '')
            path = kwargs.get('path', '/')
            self.update_info = self.check_ftp_updates(host, port, user, password, path)
        elif source == 'pcloud':
            token = kwargs.get('token', '')
            folder_id = kwargs.get('folder_id', 0)
            self.update_info = self.check_pcloud_updates(token, folder_id, self.current_version)
        elif source == 'github':
            repo = kwargs.get('repo', '')
            self.update_info = self.check_github_releases(repo, self.current_version)
        elif source == 'direct':
            version_url = kwargs.get('version_url', '')
            download_url = kwargs.get('download_url', '')
            self.update_info = self.check_direct_url(version_url, download_url, self.current_version)
        else:
            self.update_info = None
        
        # 如果有可用更新，下载并安装
        if self.update_info:
            self.download_and_install(self.update_info)
        else:
            self.status_text = "已是最新版本，无需更新！"
    
    def run(self):
        """运行更新界面"""
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_RETURN:
                        # 开始检查更新
                        self.run_update_check()
            
            # 绘制界面
            self.screen.fill(WHITE)
            
            title = self.font.render("自动更新", True, BLACK)
            title_rect = title.get_rect(center=(self.screen.get_width() // 2, 50))
            self.screen.blit(title, title_rect)
            
            self.draw_status()
            self.draw_progress_bar(self.download_progress)
            
            hint = self.font_small.render("按 ESC 返回 | 按 Enter 检查更新", True, GRAY)
            hint_rect = hint.get_rect(center=(self.screen.get_width() // 2, 370))
            self.screen.blit(hint, hint_rect)
            
            pygame.display.flip()
            self.clock.tick(60)
        
        return False

def check_for_updates(source='github', **kwargs):
    """简单的更新检查（无界面）"""
    updater = AutoUpdater()
    
    if source == 'ftp':
        host = kwargs.get('host', '')
        port = kwargs.get('port', 21)
        user = kwargs.get('user', '')
        password = kwargs.get('password', '')
        path = kwargs.get('path', '/')
        result = updater.check_ftp_updates(host, port, user, password, path)
    elif source == 'github':
        repo = kwargs.get('repo', '')
        current = kwargs.get('current_version', '1.0')
        result = updater.check_github_releases(repo, current)
    elif source == 'pcloud':
        token = kwargs.get('token', '')
        folder_id = kwargs.get('folder_id', 0)
        current = kwargs.get('current_version', '1.0')
        result = updater.check_pcloud_updates(token, folder_id, current)
    else:
        result = None
    
    return result

if __name__ == '__main__':
    updater = AutoUpdater()
    updater.run()
