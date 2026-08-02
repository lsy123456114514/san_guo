import os
import json
import threading
import copy
from ASSET.log_system import info, warning, error


class DataAccessLayer:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self):
        self._data = {}
        self._data_lock = threading.RLock()
        self._save_callbacks = []
        self._load_callbacks = []

    def set_data(self, data):
        with self._data_lock:
            self._data = data

    def get_data(self):
        with self._data_lock:
            return self._data

    def get(self, keys, default=None):
        with self._data_lock:
            result = self._data
            for key in keys:
                if isinstance(result, dict) and key in result:
                    result = result[key]
                else:
                    return default
            return result

    def set(self, keys, value):
        with self._data_lock:
            result = self._data
            for key in keys[:-1]:
                if key not in result:
                    result[key] = {}
                result = result[key]
            result[keys[-1]] = value

    def increment(self, keys, amount=1):
        with self._data_lock:
            result = self._data
            for key in keys[:-1]:
                if key not in result:
                    result[key] = {}
                result = result[key]
            key = keys[-1]
            if key not in result:
                result[key] = 0
            result[key] += amount
            return result[key]

    def add_resource(self, resource_name, amount):
        return self.increment(['resources', resource_name], amount)

    def get_resource(self, resource_name):
        return self.get(['resources', resource_name], 0)

    def ensure_keys(self, keys, default_value=None):
        with self._data_lock:
            result = self._data
            for key in keys[:-1]:
                if key not in result:
                    result[key] = {}
                result = result[key]
            final_key = keys[-1]
            if final_key not in result:
                result[final_key] = default_value if default_value is not None else {}
            return result[final_key]

    def deep_copy(self):
        with self._data_lock:
            return copy.deepcopy(self._data)

    def register_save_callback(self, callback):
        with self._data_lock:
            if callback not in self._save_callbacks:
                self._save_callbacks.append(callback)

    def register_load_callback(self, callback):
        with self._data_lock:
            if callback not in self._load_callbacks:
                self._load_callbacks.append(callback)

    def notify_save(self):
        with self._data_lock:
            callbacks = list(self._save_callbacks)
        for callback in callbacks:
            try:
                callback()
            except Exception as e:
                error(f"保存回调执行失败: {e}")

    def notify_load(self):
        with self._data_lock:
            callbacks = list(self._load_callbacks)
        for callback in callbacks:
            try:
                callback()
            except Exception as e:
                error(f"加载回调执行失败: {e}")


class SaveManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self):
        self._save_lock = threading.Lock()
        self._auto_save_interval = 300
        self._last_save_time = 0
        self._data_access = DataAccessLayer()

    def set_save_path(self, save_path):
        self._save_path = save_path

    def save(self, data=None):
        if data is None:
            data = self._data_access.get_data()

        with self._save_lock:
            try:
                if os.path.exists(self._save_path):
                    backup_path = self._save_path + ".bak"
                    with open(self._save_path, "rb") as f_in:
                        with open(backup_path, "wb") as f_out:
                            f_out.write(f_in.read())
                
                temp_path = self._save_path + ".tmp"
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                if os.path.exists(self._save_path):
                    os.remove(self._save_path)
                os.rename(temp_path, self._save_path)

                self._last_save_time = int(__import__('time').time())
                info("存档保存成功")
                self._data_access.notify_save()
                return True
            except Exception as e:
                error(f"保存存档失败: {e}")
                return False

    def load(self, default_save):
        with self._save_lock:
            if os.path.exists(self._save_path):
                try:
                    with open(self._save_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    self._data_access.set_data(data)
                    info("存档加载成功")
                    self._data_access.notify_load()
                    return data
                except Exception as e:
                    error(f"加载存档失败: {e}")
                    warning("使用默认存档")
            else:
                info("存档文件不存在，使用默认存档")

            self._data_access.set_data(default_save.copy())
            return default_save.copy()

    def auto_save(self, force=False):
        current_time = int(__import__('time').time())
        if force or current_time - self._last_save_time >= self._auto_save_interval:
            return self.save()
        return False


data_access = DataAccessLayer()
save_manager = SaveManager()