# МЕЛЛДЖАМП 🟢

*Doodle Jump × Меллстрой*

Фанатская мобильная игра в стиле **Doodle Jump** — с фото Меллстроя в роли персонажа.
Чистый Java + Android Canvas, **без внешних зависимостей**, собирается в APK одной командой.

<p align="center">
  <img src="assets/icon_512.png" width="150" alt="Иконка">
</p>

## Возможности

**Геймплей**
- Бесконечные прыжки по платформам вверх, растущая сложность
- 🟩 обычные · 🟦 движущиеся · 🟫 ломающиеся под весом
- 🌀 пружины, подбрасывающие выше
- Персонаж проскакивает через край экрана

**Настройки (шестерёнка в меню и в игре)**
- 🎮 **Управление**: палец по экрану · наклон телефона · экранные кнопки ◀ ▶
- 🎚 **Чувствительность** 50–160 % (слайдер + кнопки − / +)
- ⏩ **Скорость игры** 50–150 %
- 📳 Вибрация вкл/выкл
- 🔊 Звук вкл/выкл
- 🗑 Сброс рекорда
- 🖼 **Фон игры**: тетрадный лист · ночной город · космос · закат
  (все фоны нарисованы генератором и прокручиваются бесшовно)

**Техника**
- Фиксированный шаг физики 120 Гц + vsync-рендер (без мерцания и рванья)
- Рекорд и настройки сохраняются в SharedPreferences
- Все кнопки/иконки/фоны сгенерированы Python-скриптом (`assets/make_assets2.py`)

## Скачать

- APK (603 КБ, Android 5.0+): [`dist/Melljump.apk`](dist/Melljump.apk)
  — прямая ссылка: `https://raw.githubusercontent.com/liquidghosty/doodle-jump-mellstroy/main/dist/Melljump.apk`
- Браузерная демка: [`dist/dudle_jump_demo.html`](dist/dudle_jump_demo.html)

> Подпись — debug-ключ. Play Protect может предупредить, это нормально.

## Сборка

Нужны JDK 11+ и Android SDK (build-tools 34, platform 33).

```bash
export ANDROID_HOME=/путь/к/android-sdk
bash scripts/build.sh
# результат: dist/Melljump.apk
```

Пересоздать ассеты:

```bash
pip install pillow
python3 assets/make_assets2.py   # фоны, кнопки, иконки
python3 assets/make_assets.py    # аватар, музыка, звуки
python3 assets/make_demo.py      # браузерная демка
```

## Структура

```
app/src/com/arena/dudlejump/GameActivity.java   # игра: физика, рендер, UI, настройки
app/res/drawable-nodpi/                         # фоны, кнопки, иконки
app/res/raw/                                    # музыка и звуки
assets/                                          # генераторы ассетов (Python)
dist/                                            # APK и демка
scripts/build.sh                                 # сборка одной командой
ci/build.yml                                     # CI-сборка APK (см. ниже)
```

## Лицензия

Код — **MIT** (см. [LICENSE](LICENSE)).
⚠️ Фото Меллстроя — фанатский мем-ассет из открытых источников, **не** под MIT.
Для публикации/коммерческого использования нужны права на изображение и образ.


---

## CI (автосборка APK)

Файл для GitHub Actions лежит в `ci/build.yml`, потому что он заливался
токеном без scope `workflow`. Чтобы включить автосборку:

1. Создай файл `.github/workflows/build.yml` в веб-интерфейсе GitHub
   (**Add file → Create new file**, имя `.github/workflows/build.yml`)
2. Скопируй туда содержимое `ci/build.yml`
3. Commit — сборка запустится сама, APK появится в **Actions → артефакты**

Если пушишь локально с токеном, у которого есть галочка `workflow` —
можно просто:

```bash
mkdir -p .github/workflows && cp ci/build.yml .github/workflows/build.yml
git add .github && git commit -m "ci: включить сборку APK" && git push
```
