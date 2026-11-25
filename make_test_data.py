"""ПР1. Создаёт тестовые «данные компании» для резервного копирования.
Вариант 5: Университет, отделы dekanat и kafedra, по 7 файлов на отдел."""

import random
from pathlib import Path

root = Path("company_data")
for dept in ["dekanat", "kafedra"]:
    (root / dept).mkdir(parents=True, exist_ok=True)
    for i in range(1, 8):
        lines = [f"{dept};doc{i};{random.randint(1000, 99999)}" for _ in range(200)]
        (root / dept / f"report_{i}.csv").write_text("\n".join(lines), encoding="utf-8")
print("Тестовые данные созданы в папке company_data/")
