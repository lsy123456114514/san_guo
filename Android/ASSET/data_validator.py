import os
import json
import threading
from ASSET.log_system import info, warning, error


class DataValidator:
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
        self._validators = {}
        self._validation_errors = []

    def register_validator(self, key_path, validator_func, description=""):
        self._validators[key_path] = {
            'func': validator_func,
            'description': description
        }

    def validate_data(self, data, key_path="", parent_key=""):
        self._validation_errors = []
        self._recursive_validate(data, key_path, parent_key)
        
        if self._validation_errors:
            error(f"数据验证发现 {len(self._validation_errors)} 个问题")
            for err in self._validation_errors:
                warning(f"  {err}")
        else:
            info("数据验证通过")
        
        return len(self._validation_errors) == 0, self._validation_errors

    def _recursive_validate(self, data, key_path="", parent_key=""):
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{key_path}.{key}" if key_path else key
                self._validate_value(value, current_path)
                
                if isinstance(value, (dict, list)):
                    self._recursive_validate(value, current_path, key)
                    
                    if current_path in self._validators:
                        validator = self._validators[current_path]
                        try:
                            if not validator['func'](value):
                                self._validation_errors.append(
                                    f"路径 '{current_path}' 验证失败: {validator['description']}"
                                )
                        except Exception as e:
                            self._validation_errors.append(
                                f"路径 '{current_path}' 验证异常: {e}"
                            )
        elif isinstance(data, list):
            for index, item in enumerate(data):
                current_path = f"{key_path}[{index}]"
                self._validate_value(item, current_path)
                if isinstance(item, (dict, list)):
                    self._recursive_validate(item, current_path, str(index))

    def _validate_value(self, value, path):
        if value is None:
            self._validation_errors.append(f"路径 '{path}' 值为 None")
        elif isinstance(value, (int, float)):
            if isinstance(value, float) and (value != value or value == float('inf') or value == float('-inf')):
                self._validation_errors.append(f"路径 '{path}' 值为 NaN 或 Infinity")
            elif isinstance(value, int) and value < -10**18:
                self._validation_errors.append(f"路径 '{path}' 值过大或过小")
        elif isinstance(value, str):
            if len(value) > 10000:
                self._validation_errors.append(f"路径 '{path}' 字符串过长")

    def get_validation_errors(self):
        return self._validation_errors

    def clear_errors(self):
        self._validation_errors = []


class TypeSafeAccessor:
    @staticmethod
    def get_int(data, keys, default=0):
        result = TypeSafeAccessor._safe_get(data, keys)
        if result is None:
            return default
        try:
            return int(result)
        except (ValueError, TypeError):
            warning(f"类型转换失败: {keys} 应为 int，实际为 {type(result).__name__}")
            return default

    @staticmethod
    def get_float(data, keys, default=0.0):
        result = TypeSafeAccessor._safe_get(data, keys)
        if result is None:
            return default
        try:
            return float(result)
        except (ValueError, TypeError):
            warning(f"类型转换失败: {keys} 应为 float，实际为 {type(result).__name__}")
            return default

    @staticmethod
    def get_str(data, keys, default=""):
        result = TypeSafeAccessor._safe_get(data, keys)
        if result is None:
            return default
        try:
            return str(result)
        except (ValueError, TypeError):
            warning(f"类型转换失败: {keys} 应为 str，实际为 {type(result).__name__}")
            return default

    @staticmethod
    def get_list(data, keys, default=None):
        if default is None:
            default = []
        result = TypeSafeAccessor._safe_get(data, keys)
        if result is None:
            return default
        if isinstance(result, list):
            return result
        warning(f"类型转换失败: {keys} 应为 list，实际为 {type(result).__name__}")
        return default

    @staticmethod
    def get_dict(data, keys, default=None):
        if default is None:
            default = {}
        result = TypeSafeAccessor._safe_get(data, keys)
        if result is None:
            return default
        if isinstance(result, dict):
            return result
        warning(f"类型转换失败: {keys} 应为 dict，实际为 {type(result).__name__}")
        return default

    @staticmethod
    def get_bool(data, keys, default=False):
        result = TypeSafeAccessor._safe_get(data, keys)
        if result is None:
            return default
        if isinstance(result, bool):
            return result
        try:
            return bool(result)
        except (ValueError, TypeError):
            warning(f"类型转换失败: {keys} 应为 bool，实际为 {type(result).__name__}")
            return default

    @staticmethod
    def _safe_get(data, keys):
        if not isinstance(data, dict):
            return None
        result = data
        for key in keys:
            if isinstance(result, dict) and key in result:
                result = result[key]
            elif isinstance(result, list) and isinstance(key, int) and 0 <= key < len(result):
                result = result[key]
            else:
                return None
        return result

    @staticmethod
    def set_int(data, keys, value):
        try:
            TypeSafeAccessor._safe_set(data, keys, int(value))
            return True
        except (ValueError, TypeError):
            error(f"设置失败: {keys} 应为 int，实际为 {type(value).__name__}")
            return False

    @staticmethod
    def set_float(data, keys, value):
        try:
            TypeSafeAccessor._safe_set(data, keys, float(value))
            return True
        except (ValueError, TypeError):
            error(f"设置失败: {keys} 应为 float，实际为 {type(value).__name__}")
            return False

    @staticmethod
    def _safe_set(data, keys, value):
        if not isinstance(data, dict):
            return
        result = data
        for key in keys[:-1]:
            if key not in result:
                result[key] = {}
            result = result[key]
        result[keys[-1]] = value


data_validator = DataValidator()
type_safe = TypeSafeAccessor()