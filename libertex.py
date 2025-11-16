#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт libertex.py
Анализ APK-файла и вывод базовой информации:
- имя пакета
- версия
- отображаемое название приложения
- список разрешений
- сохранение иконки приложения
"""

import argparse
import json
import os
import sys
from pathlib import Path

from apkutils import APK
from PIL import Image
import io


# -------------------------------
# Разбор аргументов командной строки
# -------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Анализ APK-файла (имя пакета, версия, разрешения, иконка)."
    )
    parser.add_argument(
        "--apk", "-a",
        type=str,
        default="libertex.apk",
        help="Путь к APK-файлу (по умолчанию libertex.apk)"
    )
    parser.add_argument(
        "--icon-out", "-i",
        type=str,
        default="libertex_icon.png",
        help="Имя файла для сохранения иконки (по умолчанию libertex_icon.png)"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Вывести результат в формате JSON"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Подробный вывод"
    )
    return parser.parse_args()


# -------------------------------
# Извлечение основной информации об APK
# -------------------------------
def analyze_apk(apk_path: str, verbose=False) -> dict:
    if verbose:
        print(f"[INFO] Анализ APK: {apk_path}")

    try:
        apk = APK(apk_path)
    except Exception as e:
        print(f"Ошибка анализа APK: {e}")
        sys.exit(2)

    info = {
        "package_name": apk.package or "N/A",
        "app_label": apk.label or "N/A",
        "version_name": apk.version_name or "N/A",
        "version_code": apk.version_code or "N/A",
        "permissions": apk.permissions or [],
        "apk_obj": apk  # оставляем объект для дальнейшего извлечения иконки
    }

    return info


# -------------------------------
# Извлечение иконки приложения
# -------------------------------
def extract_icon(apk_obj, output_path: str, verbose=False):
    """
    Пытаемся извлечь иконку.
    Возвращаем кортеж:
    (успех: bool, путь или None)
    """

    if verbose:
        print("[INFO] Пытаемся извлечь иконку...")

    try:
        icon_path = apk_obj.icon
        if not icon_path:
            if verbose:
                print("[WARN] Иконка в APK не найдена.")
            return False, None

        # Извлекаем байты иконки
        raw = apk_obj.get_file(icon_path)
        if raw is None:
            if verbose:
                print("[WARN] Не удалось прочитать файл иконки.")
            return False, None

        # Пробуем интерпретировать иконку через Pillow
        try:
            img = Image.open(io.BytesIO(raw))
            img.save(output_path)
        except Exception:
            # Если Pillow не справился, просто запишем как есть
            try:
                with open(output_path, "wb") as f:
                    f.write(raw)
            except Exception as e2:
                if verbose:
                    print(f"[ERROR] Не удалось сохранить иконку: {e2}")
                return False, None

        if verbose:
            print(f"[INFO] Иконка успешно сохранена: {output_path}")

        return True, output_path

    except Exception as e:
        if verbose:
            print(f"[ERROR] Ошибка извлечения иконки: {e}")
        return False, None


# -------------------------------
# Вывод результата в текстовом виде
# -------------------------------
def print_human_readable(info: dict):
    print(f"APK файл: {info.get('apk_path')}")
    print("-" * 40)
    print(f"Имя пакета         : {info.get('package_name')}")
    print(f"Название приложения: {info.get('app_label')}")
    print(f"Версия (name)      : {info.get('version_name')}")
    print(f"Версия (code)      : {info.get('version_code')}")
    print("\nРазрешения:")
    if info.get("permissions"):
        for p in info["permissions"]:
            print(f"  - {p}")
    else:
        print("  Нет разрешений")

    print("\nИконка:")
    icon = info.get("icon", {})
    if icon.get("saved"):
        print(f"  Сохранена в файл: {icon.get('path')}")
    else:
        print("  Не удалось извлечь иконку")


# -------------------------------
# Вывод результата в формате JSON
# -------------------------------
def print_json(info: dict):
    print(json.dumps(info, ensure_ascii=False, indent=2))


# -------------------------------
# Основная точка входа
# -------------------------------
def main():
    args = parse_args()

    apk_path = Path(args.apk)
    if not apk_path.is_file():
        print(f"Ошибка: файл '{apk_path}' не найден. Укажите путь с помощью параметра --apk")
        sys.exit(1)

    # Анализ APK
    info = analyze_apk(str(apk_path), verbose=args.verbose)

    # Извлечение иконки
    saved, saved_path = extract_icon(
        info["apk_obj"],
        output_path=args.icon_out,
        verbose=args.verbose
    )

    # Формируем итоговую структуру для вывода
    result = {
        "apk_path": str(apk_path),
        "package_name": info["package_name"],
        "app_label": info["app_label"],
        "version_name": info["version_name"],
        "version_code": info["version_code"],
        "permissions": info["permissions"],
        "icon": {
            "saved": saved,
            "path": saved_path
        }
    }

    # Удаляем служебный объект
    result_clean = result

    # Вывод результата
    if args.json:
        print_json(result_clean)
    else:
        print_human_readable(result_clean)

    sys.exit(0)


# -------------------------------
# Запуск
# -------------------------------
if __name__ == "__main__":
    main()