#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ngrok内网穿透模块
实现公网P2P连接，像"陶瓦联机"一样！
支持TCP和UDP隧道
"""

import subprocess
import requests
import socket
import threading
import time
import json
from typing import Optional, Dict, Any, Callable

from ASSET.game_data import logger, draw_gradient_bg, cull_dead, get_font


class NgrokTunnel:
    """Ngrok隧道管理器"""
    
    def __init__(self):
        self.tunnel_url = None
        self.tunnel_port = None
        self.ngrok_process = None
        self.api_url = "http://127.0.0.1:4040/api/tunnels"
        self.running = False
    
    def check_ngrok_installed(self) -> bool:
        """检查ngrok是否安装"""
        try:
            result = subprocess.run(['ngrok', 'version'], 
                                 capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except Exception as _e:
            return False
    
    def download_ngrok(self) -> bool:
        """提示用户安装ngrok"""
        logger.info("ngrok未安装！")
        logger.info("请访问: https://ngrok.com/download")
        logger.info("下载并安装ngrok后重试")
        return False
    
    def start_tunnel(self, local_port: int, proto: str = 'tcp') -> Optional[str]:
        """启动ngrok隧道"""
        if not self.check_ngrok_installed():
            if not self.download_ngrok():
                return None
        
        try:
            args = ['ngrok', proto, str(local_port)]
            
            logger.info(f"启动ngrok隧道...")
            self.ngrok_process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.running = True
            time.sleep(3)
            
            tunnel_info = self._get_tunnel_info()
            if tunnel_info:
                self.tunnel_url = tunnel_info.get('public_url', '')
                self.tunnel_port = self._parse_port(self.tunnel_url)
                logger.info(f"✅ 隧道已启动: {self.tunnel_url}")
                return self.tunnel_url
            else:
                logger.info("❌ 获取隧道信息失败")
                self.stop_tunnel()
                return None
                
        except Exception as e:
            logger.info(f"❌ 启动ngrok失败: {e}")
            return None
    
    def _get_tunnel_info(self) -> Optional[Dict]:
        """从ngrok API获取隧道信息"""
        try:
            total_t0 = time.perf_counter()
            seen_error_types = {}  # 统计 10 轮里各异常类型出现了几次，方便直接判断根因
            for attempt in range(10):
                try:
                    t0 = time.perf_counter()
                    logger.info("[Ngrok] 轮询隧道信息 第%d次 GET %s (timeout=2s)",
                                attempt + 1, self.api_url)
                    response = requests.get(self.api_url, timeout=2)
                    dt = time.perf_counter() - t0
                    logger.info("[Ngrok] 轮询返回 状态=%s 耗时 %.3fs", response.status_code, dt)
                    if response.status_code == 200:
                        try:
                            data = response.json()
                        except ValueError as jerr:
                            snippet = ""
                            try:
                                snippet = response.text[:200].replace("\n", "\\n")
                            except Exception as _e:
                                snippet = "<无法读取 body>"
                            logger.warning(
                                "[Ngrok] 第%d次轮询 JSON解析失败 HTTP=%s Content-Type=%s snippet=%s err=%s",
                                attempt + 1, response.status_code,
                                response.headers.get('Content-Type', '?'), snippet, jerr,
                            )
                            seen_error_types['JSON解析失败'] = seen_error_types.get('JSON解析失败', 0) + 1
                            time.sleep(0.5)
                            continue
                        tunnels = data.get('tunnels', [])
                        if tunnels:
                            total_dt = time.perf_counter() - total_t0
                            logger.info("[Ngrok] 获取到隧道信息 总耗时 %.3fs", total_dt)
                            return tunnels[0]
                        else:
                            logger.info("[Ngrok] 第%d次轮询 HTTP=200 但 tunnels 为空", attempt + 1)
                            seen_error_types['空隧道列表'] = seen_error_types.get('空隧道列表', 0) + 1
                except requests.exceptions.Timeout as te:
                    etype = type(te).__name__  # ConnectTimeout / ReadTimeout
                    # 单轮超时直接升为 info：否则默认级别看不到到底是 ngrok 启动慢还是网络真的不通
                    dt_to = time.perf_counter() - t0
                    logger.info(
                        "[Ngrok] 第%d次轮询超时 类型=%s 实际耗时≈%.3fs 配置阈值=2s err=%s",
                        attempt + 1, etype, dt_to, te,
                    )
                    seen_error_types[etype] = seen_error_types.get(etype, 0) + 1
                except requests.exceptions.ConnectionError as ce:
                    etype = type(ce).__name__
                    # ngrok 本地进程还没起来时最常见：ConnectionRefused
                    dt_ce = time.perf_counter() - t0
                    logger.info(
                        "[Ngrok] 第%d次轮询连接失败 类型=%s 耗时≈%.3fs err=%s",
                        attempt + 1, etype, dt_ce, ce,
                    )
                    seen_error_types[etype] = seen_error_types.get(etype, 0) + 1
                except Exception as inner_e:
                    etype = type(inner_e).__name__
                    dt_ie = time.perf_counter() - t0
                    # 之前的 debug 改为 info：默认配置下 game.log 要能看到每轮失败的精确类型
                    logger.info(
                        "[Ngrok] 第%d次轮询未分类异常 类型=%s 耗时≈%.3fs err=%s",
                        attempt + 1, etype, dt_ie, inner_e,
                    )
                    seen_error_types[etype] = seen_error_types.get(etype, 0) + 1
                time.sleep(0.5)
            logger.warning(
                "[Ngrok] 10次轮询未获取到隧道 总耗时 %.3fs 异常分布=%s",
                time.perf_counter() - total_t0, seen_error_types,
            )
            return None
        except Exception as e:
            logger.error("[Ngrok] _get_tunnel_info 异常 类型=%s err=%s",
                         type(e).__name__, e, exc_info=True)
            logger.info(f"获取隧道API错误: {e}")
            return None
    
    def _parse_port(self, url: str) -> Optional[int]:
        """从ngrok URL解析端口"""
        try:
            if url.startswith('tcp://'):
                parts = url.split(':')
                return int(parts[-1])
        except Exception as _e:
            logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)
        return None
    
    def get_public_address(self) -> Optional[tuple]:
        """获取公网地址 (host, port)"""
        if not self.tunnel_url:
            return None
        
        try:
            if self.tunnel_url.startswith('tcp://'):
                parts = self.tunnel_url.replace('tcp://', '')
                host, port_str = parts.split(':')
                return (host, int(port_str))
        except Exception as _e:
            logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)
        return None
    
    def stop_tunnel(self):
        """停止ngrok隧道"""
        self.running = False
        if self.ngrok_process:
            try:
                self.ngrok_process.terminate()
                self.ngrok_process.wait(timeout=2)
            except Exception as _e:
                try:
                    self.ngrok_process.kill()
                except Exception as _e:
                    logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)
            self.ngrok_process = None
        self.tunnel_url = None
        self.tunnel_port = None
        logger.info("🛑 隧道已关闭")


class P2PNgrok:
    """集成ngrok的P2P网络"""
    
    def __init__(self, player_name: str = "玩家"):
        self.player_name = player_name
        self.local_port = 4000
        self.local_socket = None
        self.ngrok = NgrokTunnel()
        self.message_handler = None
        self.running = False
        self.thread = None
        self.players = {}
        self.player_id = str(int(time.time()))
    
    def start_host(self, port: int = 4000, message_callback: Optional[Callable] = None) -> Optional[str]:
        """启动主机（带ngrok穿透）"""
        try:
            self.local_port = port
            self.message_handler = message_callback
            
            self.local_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.local_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.local_socket.bind(('0.0.0.0', port))
            
            self.running = True
            self.thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.thread.start()
            
            logger.info(f"✅ 本地服务器启动: 0.0.0.0:{port}")
            
            public_url = self.ngrok.start_tunnel(port, 'tcp')
            
            if public_url:
                return public_url
            else:
                logger.info("⚠️ ngrok启动失败，但本地模式仍可用")
                return f"local:{self._get_local_ip()}:{port}"
                
        except Exception as e:
            logger.info(f"❌ 启动失败: {e}")
            return None
    
    def _get_local_ip(self) -> str:
        """获取本地IP"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as _e:
            return '127.0.0.1'
    
    def _receive_loop(self):
        """接收消息循环"""
        while self.running:
            try:
                if not self.local_socket:
                    break
                
                self.local_socket.settimeout(1.0)
                data, addr = self.local_socket.recvfrom(4096)
                self._handle_message(data, addr)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logger.info(f"接收错误: {e}")
    
    def _handle_message(self, data: bytes, addr: tuple):
        """处理消息"""
        try:
            message = json.loads(data.decode('utf-8'))
            
            if self.message_handler:
                self.message_handler(message, addr)
            else:
                logger.info(f"收到: {message}")
        except Exception as e:
            logger.info(f"解析错误: {e}")
    
    def connect_to(self, host: str, port: int):
        """连接到其他玩家"""
        try:
            self.send_message(host, port, {
                'type': 'connect',
                'player_id': self.player_id,
                'player_name': self.player_name,
                'timestamp': time.time()
            })
            logger.info(f"✅ 已连接到 {host}:{port}")
            return True
        except Exception as e:
            logger.info(f"❌ 连接失败: {e}")
            return False
    
    def send_message(self, host: str, port: int, message: Dict[str, Any]):
        """发送消息"""
        try:
            if not self.local_socket:
                return False
            
            data = json.dumps(message).encode('utf-8')
            self.local_socket.sendto(data, (host, port))
            return True
        except Exception as e:
            logger.info(f"发送失败: {e}")
            return False
    
    def stop(self):
        """停止"""
        self.running = False
        self.ngrok.stop_tunnel()
        
        if self.local_socket:
            try:
                self.local_socket.close()
            except Exception as _e:
                logger.debug("[异常静默] %s: %s", type(_e).__name__, _e)
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)
        
        logger.info("🛑 P2P网络已停止")


def test_ngrok():
    """测试ngrok功能"""
    logger.info("=== Ngrok P2P 测试\n")
    
    p2p = P2PNgrok("测试玩家")
    
    def handle_msg(msg, addr):
        logger.info(f"\n📨 收到: {msg}")
    
    logger.info("启动主机...")
    url = p2p.start_host(4000, handle_msg)
    
    if url:
        logger.info(f"\n公网地址: {url}")
        logger.info("\n按 Ctrl+C 退出...")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("[Ngrok] 手动 Ctrl+C 中断，退出隧道保持循环")
    
    p2p.stop()


if __name__ == "__main__":
    test_ngrok()
