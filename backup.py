"""ПР1. Резервное копирование с ротацией и проверкой целостности.
Вариант 5: Университет, хранится 5 последних копий.

Запуск:
    python backup.py            - создать копию, удалить старые, проверить восстановление
    python backup.py verify     - проверить последнюю копию (задание 3)
    python backup.py restore    - восстановить company_data из последней копии (задание 4)
"""

import hashlib
import json
import shutil
import sys
import tarfile
import time
from datetime import datetime
from pathlib import Path

SOURCE = Path("company_data")  # что копируем
BACKUP_DIR = Path("backups")  # куда складываем архивы
KEEP_LAST = 5  # сколько последних копий хранить (вариант 5)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def make_manifest(folder):
    """Контрольная сумма каждого файла: {относительный_путь: sha256}."""
    return {str(p.relative_to(folder)): sha256(p)
            for p in sorted(folder.rglob("*")) if p.is_file()}


def create_backup():
    BACKUP_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive = BACKUP_DIR / f"backup_{stamp}.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(SOURCE, arcname=SOURCE.name)
    manifest = {"created": stamp, "archive_sha256": sha256(archive),
                "files": make_manifest(SOURCE)}
    archive.with_suffix("").with_suffix(".json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Создан {archive.name}, файлов: {len(manifest['files'])}, "
          f"размер: {archive.stat().st_size / 1024:.1f} КБ")
    return archive


def rotate():
    archives = sorted(BACKUP_DIR.glob("backup_*.tar.gz"))
    for old in archives[:-KEEP_LAST]:
        old.unlink()
        old.with_suffix("").with_suffix(".json").unlink(missing_ok=True)
        print(f"[ROTATE] Удалена старая копия {old.name}")


def verify_restore(archive):
    """Восстанавливает архив во временную папку и сравнивает контрольные суммы."""
    manifest = json.loads(archive.with_suffix("").with_suffix(".json").read_text(encoding="utf-8"))
    if sha256(archive) != manifest["archive_sha256"]:
        print("[FAIL] Архив повреждён: контрольная сумма не совпадает")
        return False
    tmp = Path("restore_test")
    shutil.rmtree(tmp, ignore_errors=True)
    with tarfile.open(archive) as tar:
        tar.extractall(tmp, filter="data")
    restored = make_manifest(tmp / SOURCE.name)
    shutil.rmtree(tmp)
    if restored == manifest["files"]:
        print(f"[OK] Восстановление проверено: {len(restored)} файлов совпадают")
        return True
    # Задание 3: подробный отчёт о различиях
    expected = manifest["files"]
    missing = sorted(set(expected) - set(restored))   # есть в манифесте, нет в архиве
    extra = sorted(set(restored) - set(expected))     # есть в архиве, нет в манифесте
    changed = sorted(f for f in set(expected) & set(restored)
                     if expected[f] != restored[f])   # хеш не совпадает
    print("[FAIL] Восстановленные данные не совпадают с оригиналом")
    for f in missing:
        print(f"  отсутствует: {f}")
    for f in extra:
        print(f"  лишний:      {f}")
    for f in changed:
        print(f"  изменён:     {f}")
    print(f"  Итого: отсутствует {len(missing)}, лишних {len(extra)}, изменено {len(changed)}")
    return False


def latest_archive():
    """Последний по времени архив в папке backups/."""
    archives = sorted(BACKUP_DIR.glob("backup_*.tar.gz"))
    if not archives:
        sys.exit("[FAIL] В папке backups/ нет ни одной копии")
    return archives[-1]


def restore(archive):
    """Задание 4. Восстанавливает company_data из архива и выводит время восстановления."""
    start = time.perf_counter()
    print(f"[RESTORE] Восстановление из {archive.name}")
    shutil.rmtree(SOURCE, ignore_errors=True)        # удаляем повреждённые данные
    with tarfile.open(archive) as tar:
        tar.extractall(".", filter="data")           # архив содержит папку company_data/
    files = make_manifest(SOURCE)
    print(f"[OK] Восстановлено файлов: {len(files)}; отделы: "
          + ", ".join(sorted(p.name for p in SOURCE.iterdir() if p.is_dir())))
    print(f"[TIME] Время восстановления: {time.perf_counter() - start:.3f} с")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "backup"
    if command == "verify":
        verify_restore(latest_archive())
    elif command == "restore":
        restore(latest_archive())
    else:
        archive = create_backup()
        rotate()
        verify_restore(archive)
