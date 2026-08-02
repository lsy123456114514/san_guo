import os
import threading
import time
from ASSET.game_data import (
    data, save, auto_save, default_save, RESOURCES,
    HERO_DATABASE, EQUIPMENT_DATABASE, HERO_BONDS,
    safe_get, ensure_keys, type_safe
)
from ASSET.log_system import info, warning, error


class GameStateManager:
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
        self._state_lock = threading.RLock()
        self._listeners = {}

    def subscribe(self, event_type, callback):
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        if callback not in self._listeners[event_type]:
            self._listeners[event_type].append(callback)

    def unsubscribe(self, event_type, callback):
        if event_type in self._listeners and callback in self._listeners[event_type]:
            self._listeners[event_type].remove(callback)

    def _notify(self, event_type, **kwargs):
        callbacks = self._listeners.get(event_type, [])
        for callback in callbacks:
            try:
                callback(**kwargs)
            except Exception as e:
                error(f"事件回调执行失败 ({event_type}): {e}")

    def get_resources(self):
        with self._state_lock:
            return safe_get(data, ['resources'], {}).copy()

    def add_resource(self, resource_name, amount):
        with self._state_lock:
            if resource_name not in RESOURCES:
                warning(f"未知资源类型: {resource_name}")
                return False
            
            if 'resources' not in data:
                data['resources'] = {r: 0 for r in RESOURCES}
            
            data['resources'][resource_name] = data['resources'].get(resource_name, 0) + amount
            auto_save()
            self._notify('resource_changed', resource=resource_name, amount=amount)
            return True

    def consume_resource(self, resource_name, amount):
        with self._state_lock:
            current = safe_get(data, ['resources', resource_name], 0)
            if current < amount:
                warning(f"资源不足: {resource_name} 需要 {amount}，当前 {current}")
                return False
            
            data['resources'][resource_name] -= amount
            auto_save()
            self._notify('resource_changed', resource=resource_name, amount=-amount)
            return True

    def has_resource(self, resource_name, amount=1):
        return safe_get(data, ['resources', resource_name], 0) >= amount

    def get_heroes(self):
        with self._state_lock:
            return safe_get(data, ['heroes'], {}).copy()

    def add_hero(self, hero_name):
        with self._state_lock:
            if hero_name not in HERO_DATABASE:
                error(f"未知武将: {hero_name}")
                return False
            
            if 'heroes' not in data:
                data['heroes'] = {}
            
            if hero_name in data['heroes']:
                warning(f"武将已存在: {hero_name}")
                return False
            
            hero_info = HERO_DATABASE[hero_name]
            data['heroes'][hero_name] = {
                'name': hero_name,
                'level': 1,
                'experience': 0,
                'hp': hero_info.get('base_attributes', {}).get('hp', 100),
                'attack': hero_info.get('base_attributes', {}).get('attack', 10),
                'defense': hero_info.get('base_attributes', {}).get('defense', 5),
                'speed': hero_info.get('base_attributes', {}).get('speed', 5),
                'element': hero_info.get('element', '土'),
                'quality': hero_info.get('quality', 'common'),
                'faction': hero_info.get('faction', 'qun'),
                'skills': [],
                'equipment': {'weapon': None, 'armor': None, 'horse': None, 'book': None},
                'bond_bonuses': self._calculate_bond_bonuses(hero_name),
                'awakened': False,
                'rebirth_count': 0
            }
            
            auto_save()
            self._notify('hero_added', hero_name=hero_name)
            info(f"添加武将: {hero_name}")
            return True

    def remove_hero(self, hero_name):
        with self._state_lock:
            if 'heroes' in data and hero_name in data['heroes']:
                del data['heroes'][hero_name]
                auto_save()
                self._notify('hero_removed', hero_name=hero_name)
                info(f"移除武将: {hero_name}")
                return True
            return False

    def _calculate_bond_bonuses(self, hero_name):
        bonuses = {}
        for bond_key, bond_info in HERO_BONDS.items():
            if hero_name in bond_info.get('heroes', []):
                effect = bond_info.get('effect', {})
                bonuses[bond_key] = {
                    'name': bond_info.get('name', ''),
                    'type': effect.get('type', ''),
                    'value': effect.get('value', 0),
                    'description': effect.get('description', '')
                }
        return bonuses

    def get_equipment(self, equip_type):
        with self._state_lock:
            return type_safe.get_list(data, ['equips', equip_type], [])

    def add_equipment(self, equip_name):
        with self._state_lock:
            if equip_name not in EQUIPMENT_DATABASE:
                error(f"未知装备: {equip_name}")
                return False
            
            equip_info = EQUIPMENT_DATABASE[equip_name]
            equip_type = equip_info.get('type', 'weapon')
            
            if 'equips' not in data:
                data['equips'] = {}
            
            if equip_type not in data['equips']:
                data['equips'][equip_type] = []
            
            data['equips'][equip_type].append(equip_name)
            auto_save()
            self._notify('equipment_added', equip_name=equip_name, equip_type=equip_type)
            info(f"添加装备: {equip_name}")
            return True

    def remove_equipment(self, equip_type, index):
        with self._state_lock:
            equips = type_safe.get_list(data, ['equips', equip_type], [])
            if 0 <= index < len(equips):
                removed = equips.pop(index)
                data['equips'][equip_type] = equips
                auto_save()
                self._notify('equipment_removed', equip_name=removed, equip_type=equip_type)
                info(f"移除装备: {removed}")
                return True, removed
            return False, None

    def get_player_stats(self):
        with self._state_lock:
            return {
                'total_play_time': type_safe.get_int(data, ['total_play_time'], 0),
                'prestige_level': type_safe.get_int(data, ['prestige_level'], 0),
                'hero_count': len(safe_get(data, ['heroes'], {})),
                'achievement_count': len(type_safe.get_list(data, ['achievements', 'unlocked'], [])),
                'battle_wins': type_safe.get_int(data, ['battle_stats', 'victories'], 0),
                'battle_losses': type_safe.get_int(data, ['battle_stats', 'defeats'], 0)
            }

    def update_player_stats(self, stat_name, value):
        with self._state_lock:
            if stat_name == 'total_play_time':
                data['total_play_time'] = type_safe.get_int(data, ['total_play_time'], 0) + value
            elif stat_name == 'prestige_level':
                data['prestige_level'] = value
            auto_save()

    def get_battle_stats(self):
        with self._state_lock:
            return safe_get(data, ['battle_stats'], {}).copy()

    def update_battle_stats(self, win=True):
        with self._state_lock:
            ensure_keys(data, ['battle_stats'], {})
            ensure_keys(data, ['battle_stats', 'total_battles'], 0)
            ensure_keys(data, ['battle_stats', 'victories'], 0)
            ensure_keys(data, ['battle_stats', 'defeats'], 0)
            
            data['battle_stats']['total_battles'] += 1
            if win:
                data['battle_stats']['victories'] += 1
            else:
                data['battle_stats']['defeats'] += 1
            
            auto_save()
            self._notify('battle_ended', win=win)

    def get_vip_level(self):
        with self._state_lock:
            return type_safe.get_int(data, ['vip', 'level'], 0)

    def set_vip_level(self, level):
        with self._state_lock:
            ensure_keys(data, ['vip'], {})
            data['vip']['level'] = max(0, level)
            auto_save()
            self._notify('vip_changed', level=level)

    def reset_game(self):
        with self._state_lock:
            global data
            data = default_save.copy()
            save()
            self._notify('game_reset')
            info("游戏数据已重置")

    def get_save_data(self):
        with self._state_lock:
            import copy
            return copy.deepcopy(data)

    def validate_save_data(self):
        from ASSET.data_validator import data_validator
        return data_validator.validate_data(data)


game_state = GameStateManager()