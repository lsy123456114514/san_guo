#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""镜像工具：打包源码/dist，上传 0x0.st，检测存活，失效自动重传，优先从镜像下载。

用法：
  py -3 mirror_tool.py pack
  py -3 mirror_tool.py upload
  py -3 mirror_tool.py check
  py -3 mirror_tool.py sync
  py -3 mirror_tool.py status

约定：
  - 源码包以 GitHub(git archive HEAD) 为准，保证与仓库一致
  - 铜镜 URL 记在 mirror_manifest.json；过期后 check/sync 会重传并更新
  - 铜镜可用时优先下载铜镜；不可用则回退 GitHub archive
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACKS = ROOT / "packs"
DOWNLOADS = ROOT / "downloads"
MANIFEST = ROOT / "mirror_manifest.json"

GITHUB_REPO = "https://github.com/lsy123456114514/san_guo"
GITHUB_ZIP = f"{GITHUB_REPO}/archive/refs/heads/main.zip"
UPLOAD_URL = "https://0x0.st"
CATBOX_URL = "https://catbox.moe/user/api.php"
FILEBIN_URL = "https://filebin.net"
PONE_UPLOAD = "https://pone.rs/upload"
LEOPARD_UPLOAD = "https://leopard.hosting.pecon.us/upload.php"
VIKING_GET_SERVER = "https://vikingfile.com/api/get-server"
MAX_UPLOAD_BYTES = 512 * 1024 * 1024 - 1024 * 1024  # 留 1MiB 余量
# pone.rs ≤1GiB；leopard ≤100MiB（偶发验证码）；viking legacy 匿名可用
MAX_PONE_BYTES = 1024 * 1024 * 1024
MAX_LEOPARD_BYTES = 100 * 1024 * 1024
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) san-guo-mirror/1.0"


def log(msg: str) -> None:
    print(msg, flush=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest() -> dict:
    if MANIFEST.exists():
        try:
            raw = MANIFEST.read_text(encoding="utf-8")
            # 修复历史误写入的字面 \n 结尾
            raw = raw.rstrip("\\\n").rstrip()
            if not raw.endswith("}"):
                idx = raw.rfind("}")
                if idx >= 0:
                    raw = raw[: idx + 1]
            return json.loads(raw)
        except Exception as e:
            log(f"[manifest] 解析失败，重置: {e}")
    return {"files": {}}


def save_manifest(man: dict) -> None:
    text = json.dumps(man, ensure_ascii=False, indent=2) + "\n"
    # 防止误写成字面 \n
    text = text.replace('\\n', '\n') if False else text
    tmp = MANIFEST.with_suffix(".json.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(MANIFEST)


def run_git_archive(out_zip: Path) -> None:
    """从当前 HEAD 打源码包（与 GitHub 一致）。"""
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    if out_zip.exists():
        try:
            out_zip.unlink()
        except PermissionError:
            # 被占用则写到临时名再替换
            alt = out_zip.with_suffix(".zip.new")
            if alt.exists():
                try:
                    alt.unlink()
                except PermissionError:
                    pass
            out_zip = alt
    cmd = ["git", "archive", "--format=zip", "-o", str(out_zip), "HEAD"]
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(
            "git archive 失败: " + (r.stderr or b"").decode("utf-8", "replace")
        )
    # 若用了 .new，替换目标
    final = ROOT / "packs" / "san_guo_src.zip"
    if out_zip != final and out_zip.exists():
        try:
            out_zip.replace(final)
        except PermissionError:
            shutil.copy2(out_zip, final)


def zip_dir_into(src_dir: Path, dest_zip: Path, arc_prefix: str = "") -> None:
    dest_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(src_dir.rglob("*")):
            if p.is_file():
                arc = arc_prefix + p.relative_to(src_dir).as_posix()
                zf.write(p, arcname=arc)


def split_file(src: Path, part_size: int) -> list[Path]:
    """超过 part_size 则切分成 .part001/.part002…，返回分卷列表（未超限则返回 [src]）。"""
    size = src.stat().st_size
    if size <= part_size:
        return [src]
    parts: list[Path] = []
    remain = size
    index = 1
    with src.open("rb") as f:
        while remain > 0:
            n = min(part_size, remain)
            part_path = Path(f"{src}.part{index:03d}")
            with part_path.open("wb") as out:
                out.write(f.read(n))
            parts.append(part_path)
            remain -= n
            index += 1
    return parts


def cmd_pack(_args: argparse.Namespace) -> int:
    PACKS.mkdir(parents=True, exist_ok=True)

    src_zip = PACKS / "san_guo_src.zip"
    log(f"[pack] 源码 git archive -> {src_zip.name}")
    run_git_archive(src_zip)
    log(
        f"[pack]   {src_zip.stat().st_size / 1024 / 1024:.2f} MiB  "
        f"sha256={sha256_file(src_zip)[:16]}…"
    )

    dist = ROOT / "dist"
    dist_items: list[tuple[str, Path]] = []
    if dist.is_dir():
        for child in sorted(dist.iterdir()):
            if child.is_file() and child.suffix.lower() in {".exe", ".zip"}:
                dist_items.append((child.name, child))
            elif child.is_dir():
                safe = child.name.replace("\\", "_").replace("/", "_")
                dist_items.append((f"dist_{safe}.zip", child))

    man = load_manifest()
    man.setdefault("files", {})
    # 源码包固定条目
    man["files"]["san_guo_src.zip"] = {
        "kind": "source",
        "local": str(src_zip.name),
        "sha256": sha256_file(src_zip),
        "size": src_zip.stat().st_size,
        "url": man["files"].get("san_guo_src.zip", {}).get("url"),
        "github_fallback": GITHUB_ZIP,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    part_size = MAX_UPLOAD_BYTES
    for name, path in dist_items:
        # .exe 统一先压成 .zip（filebin 等站常拒收裸 exe）
        if path.is_file() and path.suffix.lower() == ".exe":
            key = path.name + ".zip"
            zip_path = PACKS / key
            log(f"[pack] exe -> {key}")
            zip_dir_into(path.parent, zip_path, arc_prefix="") if False else None
            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                zf.write(path, arcname=path.name)
            parts = split_file(zip_path, part_size)
        elif path.is_file():
            key = name
            zip_path = PACKS / name
            if not zip_path.exists() or zip_path.stat().st_size != path.stat().st_size:
                shutil.copy2(path, zip_path)
            parts = split_file(zip_path, part_size)
        else:
            key = name
            zip_path = PACKS / name
            log(f"[pack] dist 目录 -> {name}")
            zip_dir_into(path, zip_path, arc_prefix=path.name + "/")
            parts = split_file(zip_path, part_size)

        if len(parts) == 1:
            log(
                f"[pack]   {name}: {zip_path.stat().st_size / 1024 / 1024:.2f} MiB"
            )
            man["files"][key] = {
                "kind": "dist",
                "local": zip_path.name,
                "sha256": sha256_file(zip_path),
                "size": zip_path.stat().st_size,
                "url": man["files"].get(key, {}).get("url"),
                "parts": None,
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
        else:
            part_meta = []
            for i, part in enumerate(parts, 1):
                log(
                    f"[pack]   {name} 分卷 {i}/{len(parts)}: "
                    f"{part.name} ({part.stat().st_size / 1024 / 1024:.2f} MiB)"
                )
                part_meta.append(
                    {
                        "local": part.name,
                        "sha256": sha256_file(part),
                        "size": part.stat().st_size,
                        "url": None,
                    }
                )
            man["files"][key] = {
                "kind": "dist",
                "local": zip_path.name if zip_path.exists() else None,
                "sha256": sha256_file(zip_path) if zip_path.exists() else None,
                "size": zip_path.stat().st_size if zip_path.exists() else None,
                "url": None,
                "parts": part_meta,
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }

    save_manifest(man)
    log(f"[pack] 完成 -> {PACKS}  manifest={MANIFEST.name}")
    return 0


def _http_status(url: str, timeout: float = 20.0) -> int:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return int(resp.status)
    except urllib.error.HTTPError as e:
        # 302 跟随后常见 200；若 HEAD 不被允许再试 GET
        if e.code in (301, 302, 303, 307, 308):
            return e.code
        return int(e.code)
    except Exception:
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": USER_AGENT, "Range": "bytes=0-0"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return int(resp.status)
        except urllib.error.HTTPError as e:
            return int(e.code)
        except Exception:
            return 0


def url_alive(url: str) -> bool:
    if not url:
        return False
    # Windows schannel 吊销列表离线时 urllib/curl 均可能失败，优先 curl + --ssl-no-revoke
    curl = shutil.which("curl") or r"C:\Windows\System32\curl.exe"
    if curl:
        r = subprocess.run(
            [
                curl,
                "-sS",
                "-m",
                "25",
                "-A",
                USER_AGENT,
                "--http1.1",
                "-L",
                "--ssl-no-revoke",
                "-o",
                "NUL",
                "-w",
                "%{http_code}",
                url,
            ],
            capture_output=True,
        )
        code = (r.stdout or b"").decode("ascii", "replace").strip()
        if r.returncode == 0 and code in {"200", "206"}:
            return True
    # filebin 等可能 302 到 CDN，GET 跟随更准
    code = _http_status(url)
    if code in (200, 206):
        return True
    if code in (301, 302, 303, 307, 308):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=20) as resp:
                return int(resp.status) in (200, 206)
        except urllib.error.HTTPError as e:
            return int(e.code) in (200, 206, 301, 302, 307, 308)
        except Exception:
            return False
    # 再试一次 GET（部分站禁 HEAD）
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Range": "bytes=0-0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            return int(resp.status) in (200, 206)
    except urllib.error.HTTPError as e:
        return int(e.code) in (200, 206)
    except Exception:
        return False


def _curl_upload(url: str, path: Path, form_args: list[str], timeout: int = 180, extra: list[str] | None = None) -> str:
    """用系统 curl 上传（比 urllib 更稳，支持超时/重试）。"""
    if not shutil.which("curl") and not Path(r"C:\Windows\System32\curl.exe").exists():
        raise RuntimeError("未找到 curl")
    curl = shutil.which("curl") or r"C:\Windows\System32\curl.exe"
    cmd = [
        curl,
        "-sS",
        "--fail-with-body",
        "-m",
        str(timeout),
        "-A",
        USER_AGENT,
        "--http1.1",
        "-L",
    ]
    if extra:
        cmd.extend(extra)
    for a in form_args:
        cmd.extend(["-F", a])
    cmd.append(url)
    r = subprocess.run(cmd, capture_output=True)
    out = (r.stdout or b"").decode("utf-8", "replace").strip()
    err = (r.stderr or b"").decode("utf-8", "replace").strip()
    if r.returncode != 0:
        raise RuntimeError(f"curl exit {r.returncode}: {err or out[:200]}")
    return out


def _curl_put(url: str, path: Path, timeout: int = 420, content_type: str = "application/octet-stream") -> str:
    curl = shutil.which("curl") or r"C:\Windows\System32\curl.exe"
    cmd = [
        curl,
        "-sS",
        "--fail-with-body",
        "-m",
        str(timeout),
        "-A",
        USER_AGENT,
        "--http1.1",
        "-L",
        "--retry",
        "2",
        "--retry-delay",
        "2",
        "-T",
        str(path),
        "-H",
        f"Content-Type: {content_type}",
        "-w",
        "\n__HTTP__:%{http_code}",
        url,
    ]
    r = subprocess.run(cmd, capture_output=True)
    out = (r.stdout or b"").decode("utf-8", "replace").strip()
    err = (r.stderr or b"").decode("utf-8", "replace").strip()
    if r.returncode != 0:
        raise RuntimeError(f"curl exit {r.returncode}: {err or out[:200]}")
    return out


def upload_file_filebin(path: Path) -> str:
    """filebin.net：PUT 直传，返回 https://filebin.net/{bin}/{filename}（约 7 天）。"""
    bin_id = f"sg{uuid.uuid4().hex[:8]}"
    suffix = path.suffix.lower() or ".bin"
    if suffix in {".exe", ".bin"}:
        suffix = ".zip"
    fname = f"{bin_id}{suffix}"
    url = f"{FILEBIN_URL}/{bin_id}/{fname}"
    ct = "application/zip" if suffix == ".zip" else "application/octet-stream"
    out = _curl_put(url, path, content_type=ct)
    if '"filename"' not in out and '"bytes"' not in out:
        raise RuntimeError(f"filebin 返回异常: {out[:200]}")
    return url


def upload_file_pone(path: Path) -> str:
    """pone.rs 长期站（≤1GiB），POST files[]=@file，返回 u.pone.rs 直链。"""
    if path.stat().st_size > MAX_PONE_BYTES:
        raise RuntimeError(f"超过 pone 1GiB: {path.name}")
    out = _curl_upload(
        PONE_UPLOAD,
        path,
        [f"files[]=@{path}", "type=application/zip"],
        timeout=300,
    )
    j = json.loads(out)
    if not (j.get("success") and j.get("files")):
        raise RuntimeError(f"pone 返回异常: {out[:200]}")
    return j["files"][0]["url"].replace("\\/", "/")


def upload_file_leopard(path: Path) -> str:
    """leopard.hosting（≤100MiB，长期），表单 uploadContent，json=true。"""
    if path.stat().st_size > MAX_LEOPARD_BYTES:
        raise RuntimeError(f"超过 leopard 100MiB: {path.name}")
    out = _curl_upload(
        LEOPARD_UPLOAD,
        path,
        [
            f"uploadContent=@{path}",
            "type=application/zip",
            "json=true",
            "showname=yes",
            "public=yes",
        ],
        timeout=300,
    )
    j = json.loads(out)
    url = (j.get("upload") or {}).get("downloadURL") or ""
    if not url:
        raise RuntimeError(f"leopard 返回异常: {out[:200]}")
    return url.replace("\\/", "/")


def upload_file_viking(path: Path) -> str:
    """vikingfile legacy：get-server 后 POST file 匿名上传，返回 /f/{hash}。"""
    curl = shutil.which("curl") or r"C:\Windows\System32\curl.exe"
    r = subprocess.run(
        [
            curl,
            "-sS",
            "--fail-with-body",
            "-m",
            "30",
            "-A",
            USER_AGENT,
            "--http1.1",
            "-L",
            VIKING_GET_SERVER,
        ],
        capture_output=True,
    )
    gs = (r.stdout or b"").decode("utf-8", "replace").strip()
    if r.returncode != 0:
        raise RuntimeError(
            "viking get-server 失败: "
            + (r.stderr or b"").decode("utf-8", "replace")[:180]
        )
    try:
        server = json.loads(gs).get("server") or "https://fn.vikingfile.com/index2.php"
    except Exception:
        server = "https://fn.vikingfile.com/index2.php"
    server = server.replace("\\/", "/")
    out = _curl_upload(
        server,
        path,
        [f"file=@{path}", "user="],
        timeout=300,
    )
    j = json.loads(out)
    url = j.get("url") or ""
    if not url:
        raise RuntimeError(f"viking 返回异常: {out[:200]}")
    return url.replace("\\/", "/")


def upload_file_0x0(path: Path) -> str:
    """上传到 0x0.st，返回直链。"""
    out = _curl_upload(UPLOAD_URL, path, [f"file=@{path}"])
    if not out.startswith("http"):
        raise RuntimeError(f"0x0.st 返回异常: {out[:200]}")
    return out.split()[0]


def upload_file_catbox(path: Path) -> str:
    out = _curl_upload(
        CATBOX_URL,
        path,
        ["reqtype=fileupload", f"fileToUpload=@{path}"],
    )
    if not out.startswith("http"):
        raise RuntimeError(f"catbox 返回异常: {out[:200]}")
    return out.split()[0]


def upload_file_litterbox(path: Path, hours: str = "72") -> str:
    """litterbox 临时 72h，作兜底。hours: 1h/12h/24h/72h"""
    if not hours.endswith("h"):
        hours = f"{hours}h"
    url = "https://litterbox.catbox.moe/resources/internals/api.php"
    out = _curl_upload(
        url,
        path,
        ["reqtype=fileupload", f"time={hours}", f"fileToUpload=@{path}"],
    )
    if not out.startswith("http"):
        raise RuntimeError(f"litterbox 返回异常: {out[:200]}")
    return out.split()[0]


def upload_file_uguu(path: Path) -> str:
    out = _curl_upload("https://uguu.se/upload.php", path, [f"files[]=@{path}"])
    try:
        j = json.loads(out)
        if j.get("success") and j.get("files"):
            return j["files"][0].get("url") or ""
    except Exception:
        pass
    raise RuntimeError(f"uguu 返回异常: {out[:200]}")


def upload_file_catbox_retry(path: Path, retries: int = 3) -> str:
    last = None
    for i in range(retries):
        try:
            return upload_file_catbox(path)
        except Exception as e:
            last = e
            log(f"[upload] catbox 第{i+1}次失败: {e}")
            time.sleep(1.5 * (i + 1))
    raise last or RuntimeError("catbox failed")


def upload_file_tmpfiles(path: Path) -> str:
    """tmpfiles.org 返回 JSON，解析 download 字段。"""
    out = _curl_upload("https://tmpfiles.org/api/v1/upload", path, [f"file=@{path}"])
    try:
        j = json.loads(out)
        url = (j.get("data") or {}).get("url") or ""
        if "tmpfiles.org/" in url and "/dl/" not in url:
            url = url.replace("tmpfiles.org/", "tmpfiles.org/dl/", 1)
        if url:
            return url
    except Exception:
        pass
    raise RuntimeError(f"tmpfiles 返回异常: {out[:200]}")


def upload_mirrors(path: Path, want: int = 1) -> list[dict]:
    """上传并返回 [{host,url},…]。
    长期可用且能直链下载的只有 pone.rs（≤1GiB）。
    viking 下载是 Turnstile 页；leopard 常验证码；filebin 约 7 天且当前 GET 回 HTML。
    """
    mirrors: list[dict] = []
    errors: list[str] = []
    try:
        url = upload_file_pone(path)
        if not _url_is_binary(url):
            raise RuntimeError("pone 下载非二进制")
        mirrors.append({"host": "pone.rs", "url": url})
        log(f"[upload] pone.rs -> {path.name} => {url}")
    except Exception as e:
        errors.append(f"pone.rs: {e}")
        log(f"[upload] pone.rs 失败: {e}")
    # 可选后备：仅当 want>1 且文件不大时试 filebin（快失败）
    if len(mirrors) < want and path.stat().st_size <= MAX_UPLOAD_BYTES:
        try:
            url = upload_file_filebin(path)
            if _url_is_binary(url):
                mirrors.append({"host": "filebin", "url": url})
                log(f"[upload] filebin -> {path.name} => {url}")
            else:
                log("[upload] filebin 下载非二进制，丢弃")
        except Exception as e:
            errors.append(f"filebin: {e}")
            log(f"[upload] filebin 失败: {e}")
    if not mirrors:
        raise RuntimeError("全部上传源失败: " + " | ".join(errors))
    return mirrors


def _url_is_binary(url: str) -> bool:
    """HEAD/GET 前几字节：HTML/验证码页不算可用镜像。"""
    curl = shutil.which("curl") or r"C:\Windows\System32\curl.exe"
    if not curl:
        return url_alive(url)
    tmp = Path(__file__).resolve().parent / "downloads" / ".probe.bin"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    try:
        r = subprocess.run(
            [
                curl,
                "-sS",
                "-m",
                "30",
                "-A",
                USER_AGENT,
                "--http1.1",
                "-L",
                "--ssl-no-revoke",
                "-r",
                "0-3",
                "-o",
                str(tmp),
                "-w",
                "%{http_code}|%{content_type}",
                url,
            ],
            capture_output=True,
        )
        meta = (r.stdout or b"").decode("utf-8", "replace").strip()
        if r.returncode != 0 or not meta.startswith(("200", "206")):
            return False
        ctype = meta.split("|", 1)[-1].lower()
        if "text/html" in ctype:
            return False
        if tmp.exists():
            head = tmp.read_bytes()[:64]
            if head.lstrip().lower().startswith(b"<!doctype") or head.lstrip().lower().startswith(b"<html"):
                return False
            return tmp.stat().st_size >= 4 or True
        return False
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass


def upload_with_fallback(path: Path) -> str:
    if path.stat().st_size > MAX_UPLOAD_BYTES:
        raise RuntimeError(f"文件超过 512MiB: {path.name}")
    # 长期站优先（pone/viking）；filebin 约 7 天作后备；已知坏站短超时快速失败
    attempts = [
        ("pone.rs", lambda: upload_file_pone(path), 300),
        ("viking", lambda: upload_file_viking(path), 300),
        ("leopard", lambda: upload_file_leopard(path), 300),
        ("filebin", lambda: upload_file_filebin(path), 420),
        ("0x0.st", lambda: upload_file_0x0(path), 15),
        ("catbox", lambda: upload_file_catbox_retry(path, 1), 15),
        ("uguu", lambda: upload_file_uguu(path), 20),
        ("tmpfiles", lambda: upload_file_tmpfiles(path), 15),
        ("litterbox72h", lambda: upload_file_litterbox(path, "72h"), 15),
    ]
    errors: list[str] = []
    for name, fn, _t in attempts:
        try:
            # 部分函数内部已带 timeout 参数，这里只包一层日志
            if name in {"pone.rs", "viking", "leopard"}:
                url = fn()
            elif name == "0x0.st":
                url = _curl_upload(UPLOAD_URL, path, [f"file=@{path}"], timeout=15).split()[0]
                if not url.startswith("http"):
                    raise RuntimeError(url[:120])
            elif name == "catbox":
                url = _curl_upload(
                    CATBOX_URL,
                    path,
                    ["reqtype=fileupload", f"fileToUpload=@{path}"],
                    timeout=15,
                ).split()[0]
                if not url.startswith("http"):
                    raise RuntimeError(url[:120])
            elif name == "uguu":
                out = _curl_upload(
                    "https://uguu.se/upload.php",
                    path,
                    [f"files[]=@{path}"],
                    timeout=20,
                )
                j = json.loads(out)
                if not (j.get("success") and j.get("files")):
                    raise RuntimeError(str(j.get("description") or out)[:120])
                url = j["files"][0]["url"]
            elif name == "tmpfiles":
                out = _curl_upload(
                    "https://tmpfiles.org/api/v1/upload",
                    path,
                    [f"file=@{path}"],
                    timeout=15,
                )
                j = json.loads(out)
                url = (j.get("data") or {}).get("url") or ""
                if "tmpfiles.org/" in url and "/dl/" not in url:
                    url = url.replace("tmpfiles.org/", "tmpfiles.org/dl/", 1)
                if not url:
                    raise RuntimeError(out[:120])
            elif name == "litterbox72h":
                url = _curl_upload(
                    "https://litterbox.catbox.moe/resources/internals/api.php",
                    path,
                    ["reqtype=fileupload", "time=72h", f"fileToUpload=@{path}"],
                    timeout=15,
                ).split()[0]
                if not url.startswith("http"):
                    raise RuntimeError(url[:120])
            else:
                url = fn()
            log(f"[upload] {name} -> {path.name} => {url}")
            return url
        except Exception as e:
            msg = str(e).replace("\n", " ")[:180]
            errors.append(f"{name}: {msg}")
            log(f"[upload] {name} 失败: {msg}")
    raise RuntimeError("全部上传源失败: " + " | ".join(errors))


def _iter_upload_targets(man: dict) -> list[tuple[str, str, Path | None]]:
    """返回 (key, part_label, path)；path 为 None 表示缺失本地文件。"""
    targets: list[tuple[str, str, Path | None]] = []
    for key, meta in man.get("files", {}).items():
        parts = meta.get("parts")
        if parts:
            for i, p in enumerate(parts, 1):
                path = PACKS / p["local"]
                targets.append((key, f"{i}", path if path.exists() else None))
        else:
            local = meta.get("local")
            path = PACKS / local if local else None
            targets.append((key, "", path if path and path.exists() else None))
    return targets


def _store_mirrors(meta: dict, path: Path) -> str:
    mirrors = upload_mirrors(path, want=1)
    primary = mirrors[0]["url"]
    meta["url"] = primary
    meta["mirrors"] = mirrors
    meta["uploaded_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    return primary


def cmd_upload(_args: argparse.Namespace) -> int:
    if not MANIFEST.exists():
        log("[upload] 无 manifest，请先 pack")
        return 1
    man = load_manifest()
    rc = 0
    for key, label, path in _iter_upload_targets(man):
        meta = man["files"][key]
        parts = meta.get("parts")
        try:
            if parts:
                idx = int(label) - 1
                if path is None:
                    log(f"[upload] 缺少分卷 {key}#{label}，请先 pack")
                    rc = 1
                    continue
                _store_mirrors(parts[idx], path)
            else:
                if path is None:
                    log(f"[upload] 缺少 {key}，请先 pack")
                    rc = 1
                    continue
                _store_mirrors(meta, path)
        except Exception as e:
            log(f"[upload] {key} 失败: {e}")
            rc = 1
            continue
        save_manifest(man)
    return rc


def _entry_alive(meta: dict) -> bool:
    if _url_is_binary(meta.get("url") or ""):
        return True
    for m in meta.get("mirrors") or []:
        if _url_is_binary(m.get("url") or ""):
            # 救活：把存活镜像提升为 primary
            meta["url"] = m["url"]
            return True
    return False


def cmd_status(_args: argparse.Namespace) -> int:
    man = load_manifest()
    if not man.get("files"):
        log("[status] 空 manifest，请先 pack/upload")
        return 0
    for key, meta in man["files"].items():
        parts = meta.get("parts")
        if parts:
            for i, p in enumerate(parts, 1):
                st = "OK" if _entry_alive(p) else "DEAD/EMPTY"
                mirrors = ",".join(m.get("host", "?") for m in p.get("mirrors") or [])
                log(f"[status] {key}#{i}  {st}  [{mirrors}]  {p.get('url') or '-'}")
        else:
            st = "OK" if _entry_alive(meta) else "DEAD/EMPTY"
            mirrors = ",".join(m.get("host", "?") for m in meta.get("mirrors") or [])
            log(f"[status] {key}  {st}  [{mirrors}]  {meta.get('url') or '-'}")
    return 0


def _ensure_pack_for_key(man: dict, key: str) -> bool:
    """确保本地包在；没有则重新 git archive / 从 dist 补。"""
    meta = man["files"][key]
    parts = meta.get("parts")
    if parts:
        for p in parts:
            if (PACKS / p["local"]).exists():
                continue
            log(f"[check] 本地缺分卷 {p['local']}，尝试 pack 补齐…")
            return False
        return True
    local = meta.get("local")
    if not local:
        return False
    path = PACKS / local
    if path.exists():
        return True
    if meta.get("kind") == "source":
        log(f"[check] 本地缺 {local}，从 git HEAD 重打包…")
        try:
            run_git_archive(path)
            return True
        except Exception as e:
            log(f"[check] 重打包失败: {e}")
            return False
    log(f"[check] 本地缺 {local}，请手动 pack")
    return False


def cmd_check(_args: argparse.Namespace) -> int:
    if not MANIFEST.exists():
        log("[check] 无 manifest")
        return 1
    man = load_manifest()
    need_upload = False
    for key, meta in man.get("files", {}).items():
        parts = meta.get("parts")
        if parts:
            for i, p in enumerate(parts, 1):
                if _entry_alive(p):
                    log(f"[check] {key}#{i} 存活")
                    continue
                log(f"[check] {key}#{i} 失效，准备重传")
                need_upload = True
            if not _ensure_pack_for_key(man, key):
                continue
            path = PACKS / p["local"]
            if path.exists():
                try:
                    _store_mirrors(p, path)
                    save_manifest(man)
                except Exception as e:
                    log(f"[check] {key}#{i} 重传失败: {e}")
        else:
            if _entry_alive(meta):
                log(f"[check] {key} 存活")
                continue
            log(f"[check] {key} 失效，准备重传")
            need_upload = True
            if not _ensure_pack_for_key(man, key):
                continue
            local = meta.get("local")
            path = PACKS / local if local else None
            if path and path.exists():
                try:
                    _store_mirrors(meta, path)
                    save_manifest(man)
                except Exception as e:
                    log(f"[check] {key} 重传失败: {e}")
    if not need_upload:
        log("[check] 全部存活")
    return 0


def _download(url: str, dest: Path, timeout: float = 120.0) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    curl = shutil.which("curl") or r"C:\Windows\System32\curl.exe"
    if curl:
        r = subprocess.run(
            [
                curl,
                "-sS",
                "--fail-with-body",
                "-m",
                str(int(timeout)),
                "-A",
                USER_AGENT,
                "--http1.1",
                "-L",
                "--ssl-no-revoke",
                "--retry",
                "2",
                "-o",
                str(dest),
                url,
            ],
            capture_output=True,
        )
        if r.returncode == 0 and dest.exists() and dest.stat().st_size > 0:
            return
        err = (r.stderr or b"").decode("utf-8", "replace").strip()
        if dest.exists() and dest.stat().st_size == 0:
            dest.unlink(missing_ok=True)
        # 继续尝试 urllib
        if err:
            log(f"[download] curl 失败，改用 urllib: {err[:160]}")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp, dest.open("wb") as out:
        shutil.copyfileobj(resp, out)


def cmd_sync(args: argparse.Namespace) -> int:
    """检测铜镜；失效则重传；存活则下载到 downloads/。"""
    if not MANIFEST.exists():
        log("[sync] 无 manifest，请先 pack/upload")
        return 1
    # 先 check（自动重传失效项）
    cmd_check(args)
    man = load_manifest()
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    for key, meta in man.get("files", {}).items():
        parts = meta.get("parts")
        if parts:
            for i, p in enumerate(parts, 1):
                url = p.get("url") or ""
                dest = DOWNLOADS / p["local"]
                if url_alive(url):
                    log(f"[sync] 下载铜镜 {key}#{i} -> {dest.name}")
                    try:
                        _download(url, dest)
                        continue
                    except Exception as e:
                        log(f"[sync] 铜镜下载失败: {e}")
                log(f"[sync] 铜镜不可用 {key}#{i}（本地已有包则跳过网络回退）")
                local = PACKS / p["local"]
                if local.exists():
                    shutil.copy2(local, dest)
                    log(f"[sync]   使用本地分卷 {local.name}")
        else:
            url = meta.get("url") or ""
            dest = DOWNLOADS / meta.get("local") or key
            dest = DOWNLOADS / (meta.get("local") or key)
            if url_alive(url):
                log(f"[sync] 下载铜镜 {key} -> {dest.name}")
                try:
                    _download(url, dest)
                    continue
                except Exception as e:
                    log(f"[sync] 铜镜下载失败: {e}")
            if meta.get("kind") == "source":
                log(f"[sync] 回退 GitHub -> {dest.name}")
                try:
                    _download(GITHUB_ZIP, dest)
                    log(f"[sync]   GitHub 下载完成 {dest.stat().st_size / 1024 / 1024:.2f} MiB")
                    continue
                except Exception as e:
                    log(f"[sync] GitHub 也失败: {e}")
            local = PACKS / (meta.get("local") or "")
            if local.exists():
                shutil.copy2(local, dest)
                log(f"[sync]   使用本地包 {local.name}")
    log(f"[sync] 完成，输出目录: {DOWNLOADS}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="三国游戏铜镜（pone/viking/leopard/filebin）打包/上传/检测/同步")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("pack", help="打源码包 + dist 分段包")
    sub.add_parser("upload", help="上传全部本地包")
    sub.add_parser("check", help="检测 URL，失效自动重传")
    sub.add_parser("sync", help="检测 + 重传 + 下载")
    sub.add_parser("status", help="打印各文件存活状态")
    args = ap.parse_args()
    handlers = {
        "pack": cmd_pack,
        "upload": cmd_upload,
        "check": cmd_check,
        "sync": cmd_sync,
        "status": cmd_status,
    }
    try:
        return handlers[args.cmd](args)
    except KeyboardInterrupt:
        log("已取消")
        return 130


if __name__ == "__main__":
    sys.exit(main())
