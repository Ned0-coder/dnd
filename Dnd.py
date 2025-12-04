import streamlit as st
from typing import List, Dict, Optional
from datetime import datetime
import time

# ========== КОНФИГУРАЦИЯ ==========
HOST_PASSWORD = "IamDM"
ELEMENTS = ["Огонь", "Вода", "Земля", "Воздух", "Свет", "Тьма", "Жизнь", "Смерть"]
ELEMENT_COLORS = {
    "Огонь": "#FF6B6B",
    "Вода": "#4ECDC4",
    "Воздух": "#A0D2FF",
    "Земля": "#D4A76A",
    "Свет": "#FFD166",
    "Тьма": "#5A189A",
    "Жизнь": "#06D6A0",
    "Смерть": "#6A0572"
}
ELEMENT_SYMBOLS = {
    "Огонь": "🔥",
    "Вода": "💧",
    "Воздух": "💨",
    "Земля": "🌍",
    "Свет": "✨",
    "Тьма": "🌙",
    "Жизнь": "🌿",
    "Смерть": "💀"
}

# ========== БАЗА ДАННЫХ ЗАКЛИНАНИЙ ==========
SPELLS_DB = [
    {"id": 1, "name": "Огненный шар", "level": 3},
    {"id": 2, "name": "Лечение ран", "level": 1},
    {"id": 3, "name": "Магическая защита", "level": 2},
    {"id": 4, "name": "Молния", "level": 3},
    {"id": 5, "name": "Невидимость", "level": 2},
    {"id": 6, "name": "Телепортация", "level": 4},
    {"id": 7, "name": "Воскрешение", "level": 5},
    {"id": 8, "name": "Метеоритный дождь", "level": 5},
    {"id": 9, "name": "Шаровая молния", "level": 3},
    {"id": 10, "name": "Щит мага", "level": 2},
    {"id": 11, "name": "Призыв элементаля", "level": 4},
    {"id": 12, "name": "Рассеивание магии", "level": 3},
    {"id": 13, "name": "Магический снаряд", "level": 1},
    {"id": 14, "name": "Огненная стена", "level": 4},
    {"id": 15, "name": "Ледяная буря", "level": 4},
    {"id": 16, "name": "Полёт", "level": 3},
    {"id": 17, "name": "Каменная кожа", "level": 3},
    {"id": 18, "name": "Планарные врата", "level": 5},
    {"id": 19, "name": "Слово силы", "level": 5},
    {"id": 20, "name": "Пожирающая туча", "level": 4},
]


# ========== ИНИЦИАЛИЗАЦИЯ СЕССИИ ==========
def init_session_state():
    """Инициализация всех переменных сессии"""
    if "spell_combinations" not in st.session_state:
        st.session_state.spell_combinations = {}

    if "client_requests" not in st.session_state:
        st.session_state.client_requests = []

    if "game_blocks" not in st.session_state:
        st.session_state.game_blocks = []

    if "current_user" not in st.session_state:
        st.session_state.current_user = "Игрок"

    if "user_type" not in st.session_state:
        st.session_state.user_type = "client"

    if "show_client_table" not in st.session_state:
        st.session_state.show_client_table = False

    if "last_request_id" not in st.session_state:
        st.session_state.last_request_id = 0

    if "last_block_id" not in st.session_state:
        st.session_state.last_block_id = 0

    if "current_game" not in st.session_state:
        st.session_state.current_game = None

    if "selected_spell" not in st.session_state:
        st.session_state.selected_spell = None

    # Для онлайн-работы обновляем данные каждые 2 секунды
    if "last_update" not in st.session_state:
        st.session_state.last_update = time.time()


# ========== ОБНОВЛЕНИЕ ДАННЫХ ==========
def update_data_periodically():
    """Периодическое обновление данных для онлайн-работы"""
    current_time = time.time()
    if current_time - st.session_state.last_update > 2:  # Обновление каждые 2 секунды
        st.session_state.last_update = current_time
        st.rerun()


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def get_or_create_game_block(spell_name: str, level: int, client_name: str = "Система") -> Optional[Dict]:
    """Получает существующий игровой блок или создает новый"""
    # Ищем существующий блок
    existing_block = next((b for b in st.session_state.game_blocks
                           if b['spell_name'] == spell_name), None)

    if existing_block:
        return existing_block

    # Проверяем, есть ли комбинация для этого заклинания
    spell_combo = st.session_state.spell_combinations.get(spell_name)

    if spell_combo:
        # Создаем новый блок с существующей комбинацией
        new_block = {
            "id": st.session_state.last_block_id + 1,
            "spell_name": spell_name,
            "level": level,
            "combination": spell_combo['combination'],
            "elements": spell_combo['elements'],
            "guessed": [],
            "attempts": 0,
            "max_attempts": 1,
            "is_active": True,
            "created_by": client_name,
            "created_at": datetime.now().strftime("%H:%M:%S"),
            "last_played": None
        }
        st.session_state.last_block_id += 1
        st.session_state.game_blocks.append(new_block)
        return new_block

    return None


def create_repeat_request(spell_name: str, level: int, client_name: str):
    """Создает запрос на повторную попытку"""
    new_request = {
        "id": st.session_state.last_request_id + 1,
        "client_name": client_name,
        "spell_name": spell_name,
        "level": level,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "status": "ожидает",
        "type": "повтор",
        "original_client": client_name
    }
    st.session_state.last_request_id += 1
    st.session_state.client_requests.append(new_request)
    return new_request


def create_new_request(spell_name: str, level: int, client_name: str):
    """Создает новый запрос на заклинание"""
    new_request = {
        "id": st.session_state.last_request_id + 1,
        "client_name": client_name,
        "spell_name": spell_name,
        "level": level,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "status": "ожидает",
        "type": "новый",
        "original_client": client_name
    }
    st.session_state.last_request_id += 1
    st.session_state.client_requests.append(new_request)
    return new_request


# ========== ФУНКЦИИ ДЛЯ ХОСТА ==========
def host_interface():
    """Интерфейс хоста"""
    # Обновление данных для онлайн-работы
    update_data_periodically()

    st.title("👑 Панель Мастера")

    # Переключение режимов
    col_view1, col_view2 = st.columns(2)
    with col_view1:
        if st.button("📋 Панель мастера", use_container_width=True,
                     type="primary" if not st.session_state.show_client_table else "secondary"):
            st.session_state.show_client_table = False
            st.rerun()
    with col_view2:
        if st.button("🎮 Стол клиентов", use_container_width=True,
                     type="primary" if st.session_state.show_client_table else "secondary"):
            st.session_state.show_client_table = True
            st.rerun()

    if st.session_state.show_client_table:
        display_client_table_for_host()
        return

    # Основная панель мастера
    st.header("🔮 Управление комбинациями")

    # Онлайн-статус
    with st.expander("📡 Статус системы", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("👥 Активных игроков",
                      len(set(
                          r['original_client'] for r in st.session_state.client_requests if r['status'] == 'ожидает')))
        with col2:
            st.metric("🕒 Последнее обновление", datetime.now().strftime("%H:%M:%S"))
        with col3:
            if st.button("🔄 Принудительное обновление"):
                st.rerun()

    # Статистика
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📦 Игровых блоков", len(st.session_state.game_blocks))
    with col2:
        active_requests = len([r for r in st.session_state.client_requests if r['status'] == 'ожидает'])
        st.metric("📨 Ожидают", active_requests)
    with col3:
        st.metric("🧩 Комбинаций", len(st.session_state.spell_combinations))

    # Разделение на две колонки
    requests_col, combos_col = st.columns(2)

    with requests_col:
        st.subheader("📨 Запросы игроков")

        pending_requests = [r for r in st.session_state.client_requests if r['status'] == 'ожидает']

        if not pending_requests:
            st.info("Нет ожидающих запросов")
        else:
            for req in pending_requests[:]:
                with st.expander(f"{'🔄' if req['type'] == 'повтор' else '🔔'} {req['spell_name']} (Ур. {req['level']})",
                                 expanded=True):

                    if req['type'] == 'повтор':
                        st.warning(f"**ПОВТОРНЫЙ ЗАПРОС** от {req['client_name']}")
                    else:
                        st.write(f"**Игрок:** {req['client_name']}")

                    st.write(f"**Тип:** {'Повторная попытка' if req['type'] == 'повтор' else 'Новый запрос'}")
                    st.write(f"**Время:** {req['timestamp']}")

                    # Проверяем, есть ли уже комбинация
                    existing_combo = st.session_state.spell_combinations.get(req['spell_name'])

                    if existing_combo:
                        st.success(f"✅ Комбинация существует: {existing_combo['combination']}")

                        # Находим игровой блок
                        existing_block = next((b for b in st.session_state.game_blocks
                                               if b['spell_name'] == req['spell_name']), None)

                        if existing_block:
                            st.info(f"🎮 Игровой блок уже создан")

                            if req['type'] == 'повтор':
                                # Для повторного запроса - сбрасываем попытки
                                if st.button("✅ Разрешить повторную попытку", key=f"allow_repeat_{req['id']}",
                                             use_container_width=True):
                                    existing_block['attempts'] = 0
                                    req['status'] = 'обработан'
                                    st.success(f"Повторная попытка разрешена для {req['spell_name']}")
                                    st.rerun()
                            else:
                                # Для нового запроса - создаем/обновляем блок
                                if st.button("🎮 Создать/обновить игру", key=f"create_game_{req['id']}",
                                             use_container_width=True):
                                    if not existing_block:
                                        get_or_create_game_block(req['spell_name'], req['level'], req['client_name'])
                                    req['status'] = 'обработан'
                                    st.rerun()
                        else:
                            # Создаем новый блок
                            if st.button("🎮 Создать игру", key=f"create_new_{req['id']}", use_container_width=True):
                                get_or_create_game_block(req['spell_name'], req['level'], req['client_name'])
                                req['status'] = 'обработан'
                                st.rerun()
                    else:
                        st.warning("❌ Комбинация не найдена")

                        # Создание новой комбинации
                        st.write("**Создать комбинацию:**")

                        num_elements = req['level']
                        combo_cols = st.columns(min(4, num_elements))
                        new_combo = []

                        for i in range(num_elements):
                            with combo_cols[i % 4]:
                                element = st.selectbox(
                                    f"Элемент {i + 1}",
                                    ELEMENTS,
                                    key=f"host_new_{req['id']}_{i}"
                                )
                                new_combo.append(element)

                        if st.button("💾 Сохранить и создать игру", key=f"save_{req['id']}", use_container_width=True,
                                     type="primary"):
                            # Сохраняем комбинацию
                            combo_symbols = "".join([ELEMENT_SYMBOLS[e] for e in new_combo])
                            st.session_state.spell_combinations[req['spell_name']] = {
                                "combination": combo_symbols,
                                "elements": new_combo
                            }

                            # Создаем игровой блок
                            get_or_create_game_block(req['spell_name'], req['level'], req['client_name'])

                            # Помечаем запрос как обработанный
                            req['status'] = 'обработан'
                            st.rerun()

                        if st.button("❌ Отклонить", key=f"reject_{req['id']}", use_container_width=True):
                            req['status'] = 'отклонен'
                            st.rerun()

    with combos_col:
        st.subheader("🧩 Существующие комбинации")

        if not st.session_state.spell_combinations:
            st.info("Нет созданных комбинаций")
        else:
            # Поиск комбинаций
            search_combo = st.text_input("🔍 Поиск комбинации", placeholder="Введите название заклинания...")

            filtered_combos = list(st.session_state.spell_combinations.items())
            if search_combo:
                filtered_combos = [(k, v) for k, v in filtered_combos if search_combo.lower() in k.lower()]

            for spell_name, combo_data in filtered_combos:
                with st.expander(f"🔮 {spell_name} - {combo_data['combination']}", expanded=False):
                    # Информация о блоке
                    block = next((b for b in st.session_state.game_blocks
                                  if b['spell_name'] == spell_name), None)

                    if block:
                        st.write(
                            f"**Статус:** {'🎮 Активна' if block['attempts'] < block['max_attempts'] else '⏳ Ожидает повторного запроса'}")
                        st.write(f"**Угадано:** {len(block['guessed'])}/{block['level']} элементов")

                    # Редактирование
                    st.write("**Редактировать комбинацию:**")

                    num_elements = len(combo_data['elements'])
                    edit_cols = st.columns(min(4, num_elements))
                    edited_combo = []

                    for i in range(num_elements):
                        with edit_cols[i % 4]:
                            current_element = combo_data['elements'][i]
                            element = st.selectbox(
                                f"Эл. {i + 1}",
                                ELEMENTS,
                                index=ELEMENTS.index(current_element) if current_element in ELEMENTS else 0,
                                key=f"edit_combo_{spell_name}_{i}"
                            )
                            edited_combo.append(element)

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("💾 Обновить", key=f"update_{spell_name}", use_container_width=True):
                            combo_symbols = "".join([ELEMENT_SYMBOLS[e] for e in edited_combo])
                            st.session_state.spell_combinations[spell_name] = {
                                "combination": combo_symbols,
                                "elements": edited_combo
                            }

                            # Обновляем блок
                            if block:
                                block['combination'] = combo_symbols
                                block['elements'] = edited_combo
                                # Не сбрасываем угаданные элементы!

                            st.rerun()

                    with col2:
                        if st.button("🔄 Сбросить попытки", key=f"reset_attempts_{spell_name}",
                                     use_container_width=True):
                            if block:
                                block['attempts'] = 0
                            st.rerun()

                    with col3:
                        if st.button("🗑️ Удалить", key=f"delete_{spell_name}", use_container_width=True):
                            del st.session_state.spell_combinations[spell_name]
                            st.session_state.game_blocks = [b for b in st.session_state.game_blocks
                                                            if b['spell_name'] != spell_name]
                            st.rerun()


def display_client_table_for_host():
    """Отображение стола клиентов для хоста"""
    # Обновление данных
    update_data_periodically()

    st.title("🎮 Стол клиентов (режим просмотра)")

    if not st.session_state.game_blocks:
        st.info("Нет активных игр")
        return

    # Поиск по играм
    search_game = st.text_input("🔍 Поиск игры", placeholder="Введите название заклинания...")

    filtered_games = st.session_state.game_blocks
    if search_game:
        filtered_games = [b for b in filtered_games if search_game.lower() in b['spell_name'].lower()]

    for block in filtered_games:
        with st.container():
            st.markdown("---")

            col_title, col_status = st.columns([3, 1])
            with col_title:
                status_icon = "✅" if len(block['guessed']) == block['level'] else "🎮" if block['attempts'] < block[
                    'max_attempts'] else "⏳"
                st.write(f"**{status_icon} {block['spell_name']}** (Ур. {block['level']})")
                st.caption(f"Создал: {block['created_by']} | Попыток использовано: {block['attempts']}")

            with col_status:
                progress = len(block['guessed']) / block['level']
                st.progress(progress)
                st.caption(f"{len(block['guessed'])}/{block['level']}")

            # Отображение элементов
            st.write("**Прогресс игроков:**")

            element_cols = st.columns(block['level'])
            for i in range(block['level']):
                with element_cols[i]:
                    if i < len(block['guessed']):
                        element = block['guessed'][i]
                        color = ELEMENT_COLORS.get(element, "#CCCCCC")
                        symbol = ELEMENT_SYMBOLS.get(element, "?")

                        st.markdown(
                            f'<div style="background-color: {color}; padding: 10px; border-radius: 50%; '
                            f'width: 50px; height: 50px; display: flex; align-items: center; '
                            f'justify-content: center; margin: 0 auto; border: 3px solid #06D6A0;">'
                            f'<span style="font-size: 1.2em;">{symbol}</span></div>',
                            unsafe_allow_html=True
                        )
                        st.caption(f"✓ {element}")
                    else:
                        actual_element = block['elements'][i]
                        color = ELEMENT_COLORS.get(actual_element, "#CCCCCC")
                        symbol = ELEMENT_SYMBOLS.get(actual_element, "?")

                        st.markdown(
                            f'<div style="background-color: {color}; padding: 10px; border-radius: 50%; '
                            f'width: 50px; height: 50px; display: flex; align-items: center; '
                            f'justify-content: center; margin: 0 auto; border: 2px dashed #666; opacity: 0.6;">'
                            f'<span style="font-size: 1.2em;">{symbol}</span></div>',
                            unsafe_allow_html=True
                        )
                        st.caption(f"? {actual_element}")


# ========== ФУНКЦИИ ДЛЯ КЛИЕНТА ==========
def client_interface():
    """Общий интерфейс для всех клиентов"""
    # Обновление данных для онлайн-работы
    update_data_periodically()

    st.title("🧙‍♂️ Общий игровой стол")

    # Информация о пользователе
    with st.sidebar:
        st.write(f"**Игрок:** {st.session_state.current_user}")

        # Изменение имени
        new_name = st.text_input("Сменить имя", value=st.session_state.current_user)
        if new_name != st.session_state.current_user:
            st.session_state.current_user = new_name
            st.rerun()

        if st.button("🔄 Обновить стол", use_container_width=True, type="primary"):
            st.rerun()

        # Статистика
        st.subheader("📊 Статистика стола")
        active_games = len(st.session_state.game_blocks)
        total_guessed = sum(len(b['guessed']) for b in st.session_state.game_blocks)
        total_elements = sum(b['level'] for b in st.session_state.game_blocks)

        st.write(f"**Активных игр:** {active_games}")
        if total_elements > 0:
            progress_pct = (total_guessed / total_elements) * 100
            st.write(f"**Общий прогресс:** {progress_pct:.1f}%")

        # Активные запросы
        pending_requests = [r for r in st.session_state.client_requests
                            if r['status'] == 'ожидает' and r['original_client'] == st.session_state.current_user]
        if pending_requests:
            st.subheader("📨 Мои запросы")
            for req in pending_requests:
                st.write(f"• {req['spell_name']} ({'повтор' if req['type'] == 'повтор' else 'новый'})")

        st.markdown("---")
        if st.button("👑 Войти как Мастер", use_container_width=True):
            st.session_state.user_type = "host_login"
            st.rerun()

    # Если выбрана игра
    if st.session_state.current_game:
        game_block = next((b for b in st.session_state.game_blocks
                           if b['spell_name'] == st.session_state.current_game), None)
        if game_block:
            play_spell_game(game_block)
            return

    # Основной интерфейс
    col_search, col_games = st.columns([1, 2])

    with col_search:
        st.header("🔍 Поиск заклинаний")

        # Автокомплит с выпадающим списком
        spell_names = [spell["name"] for spell in SPELLS_DB]

        # Поле выбора заклинания
        selected_spell_name = st.selectbox(
            "Выберите заклинание",
            options=[""] + spell_names,
            format_func=lambda x: "🔍 Выберите заклинание..." if x == "" else x,
            key="spell_search_select",
            index=0
        )

        # Кнопка выбора
        if selected_spell_name:
            # Находим заклинание
            spell = next((s for s in SPELLS_DB if s["name"] == selected_spell_name), None)

            if spell:
                # Показываем информацию о заклинании
                st.markdown("---")
                st.write(f"### {spell['name']}")
                st.write(f"**Уровень:** {spell['level']}")

                # Проверяем статус
                existing_block = next((b for b in st.session_state.game_blocks
                                       if b['spell_name'] == spell['name']), None)

                existing_request = next((r for r in st.session_state.client_requests
                                         if r['spell_name'] == spell['name'] and
                                         r['status'] == 'ожидает' and
                                         r['original_client'] == st.session_state.current_user), None)

                # Показываем текущий статус
                if existing_block:
                    if existing_block['attempts'] < existing_block['max_attempts']:
                        st.success("✅ Игра доступна!")
                        st.write(f"**Угадано:** {len(existing_block['guessed'])}/{existing_block['level']} элементов")
                    else:
                        st.warning("⏳ Попытка использована")
                        st.write(f"**Угадано:** {len(existing_block['guessed'])}/{existing_block['level']} элементов")
                elif existing_request:
                    st.info("📨 Запрос ожидает ответа мастера")
                else:
                    st.info("📤 Можно отправить запрос на игру")

                # Кнопки действий
                st.markdown("---")

                if existing_block:
                    if existing_block['attempts'] < existing_block['max_attempts']:
                        # Кнопка Играть
                        if st.button("🎮 **Играть**",
                                     use_container_width=True,
                                     type="primary",
                                     key=f"play_selected_{spell['id']}"):
                            st.session_state.current_game = spell['name']
                            st.rerun()
                    else:
                        # Кнопка Запросить повтор
                        if st.button("🔄 **Запросить повторную попытку**",
                                     use_container_width=True,
                                     type="secondary",
                                     key=f"repeat_selected_{spell['id']}"):
                            create_repeat_request(spell['name'], spell['level'], st.session_state.current_user)
                            st.success(f"📨 Запрос на повторную попытку отправлен!")
                            st.rerun()

                        # Кнопка Посмотреть прогресс
                        if st.button("👁️ **Посмотреть прогресс**",
                                     use_container_width=True,
                                     key=f"view_selected_{spell['id']}"):
                            st.session_state.current_game = spell['name']
                            st.rerun()
                else:
                    if not existing_request:
                        # Кнопка Запросить игру
                        if st.button("📤 **Запросить игру у мастера**",
                                     use_container_width=True,
                                     type="primary",
                                     key=f"request_selected_{spell['id']}"):
                            create_new_request(spell['name'], spell['level'], st.session_state.current_user)
                            st.success(f"📨 Запрос на игру отправлен мастеру!")
                            st.rerun()
                    else:
                        st.button("⏳ **Ожидает ответа мастера**",
                                  disabled=True,
                                  use_container_width=True,
                                  key=f"waiting_selected_{spell['id']}")

    with col_games:
        st.header("🎮 Активные игры")

        if not st.session_state.game_blocks:
            st.info("""
            ### 🎯 Как начать игру:
            1. Выберите заклинание из списка слева
            2. Нажмите "📤 Запросить игру"
            3. Мастер создаст комбинацию
            4. Игра появится здесь автоматически
            """)
        else:
            # Поиск по играм
            game_search = st.text_input("🔍 Поиск по играм", placeholder="Введите название...", key="game_search")

            filtered_games = st.session_state.game_blocks
            if game_search:
                filtered_games = [b for b in filtered_games if game_search.lower() in b['spell_name'].lower()]

            if not filtered_games:
                st.info("Игры не найдены")

            for block in filtered_games:
                display_client_game_block(block)


def display_client_game_block(block: Dict):
    """Отображение игрового блока для клиента"""
    with st.container():
        st.markdown("---")

        # Заголовок и статус
        col_title, col_status = st.columns([3, 1])

        with col_title:
            status_icon = "✅" if len(block['guessed']) == block['level'] else "🎮" if block['attempts'] < block[
                'max_attempts'] else "⏳"
            st.write(f"**{status_icon} {block['spell_name']}** (Ур. {block['level']})")
            if block['guessed']:
                st.caption(f"Угадано: {len(block['guessed'])}/{block['level']}")

        with col_status:
            progress = len(block['guessed']) / block['level']
            st.progress(progress)
            if block['attempts'] >= block['max_attempts']:
                st.caption("🔄 Нужен запрос")
            else:
                st.caption(f"Попыток: {block['max_attempts'] - block['attempts']}")

        # Отображение элементов
        element_cols = st.columns(min(8, block['level']))
        for i in range(block['level']):
            with element_cols[i % 8]:
                if i < len(block['guessed']):
                    # Угаданный элемент
                    element = block['guessed'][i]
                    color = ELEMENT_COLORS.get(element, "#CCCCCC")
                    symbol = ELEMENT_SYMBOLS.get(element, "?")

                    st.markdown(
                        f'<div style="background-color: {color}; padding: 12px; border-radius: 50%; '
                        f'width: 50px; height: 50px; display: flex; align-items: center; '
                        f'justify-content: center; margin: 0 auto; border: 3px solid #06D6A0;">'
                        f'<span style="font-size: 1.3em;">{symbol}</span></div>',
                        unsafe_allow_html=True
                    )
                else:
                    # Неугаданный элемент
                    st.markdown(
                        f'<div style="background-color: #333; padding: 12px; border-radius: 50%; '
                        f'width: 50px; height: 50px; display: flex; align-items: center; '
                        f'justify-content: center; margin: 0 auto; border: 2px solid #666;">'
                        f'<span style="font-size: 1.3em; color: white;">?</span></div>',
                        unsafe_allow_html=True
                    )

        # Кнопки действий
        col_play, col_repeat = st.columns(2)

        with col_play:
            if block['attempts'] < block['max_attempts']:
                if st.button("🎮 **Играть**", key=f"play_btn_{block['id']}",
                             use_container_width=True, type="primary"):
                    st.session_state.current_game = block['spell_name']
                    st.rerun()
            else:
                st.button("❌ **Попытка использована**", disabled=True,
                          use_container_width=True, key=f"used_{block['id']}")

        with col_repeat:
            if block['attempts'] >= block['max_attempts']:
                if st.button("🔄 **Запросить повтор**", key=f"repeat_btn_{block['id']}",
                             use_container_width=True, type="secondary",
                             help="Запросить новую попытку у мастера"):
                    create_repeat_request(block['spell_name'], block['level'], st.session_state.current_user)
                    st.success(f"📨 Запрос на повторную попытку отправлен!")
                    st.rerun()
            else:
                if len(block['guessed']) < block['level']:
                    if st.button("👁️ **Посмотреть**", key=f"view_btn_{block['id']}",
                                 use_container_width=True):
                        st.session_state.current_game = block['spell_name']
                        st.rerun()


def play_spell_game(block: Dict):
    """Игровой интерфейс угадывания"""
    st.title(f"🎮 Угадайте: {block['spell_name']}")

    # Проверяем, можно ли играть
    if block['attempts'] >= block['max_attempts']:
        st.error("❌ Попытка уже использована!")
        st.info("Нажмите '🔄 Запросить повтор' для получения новой попытки.")

        if st.button("← Назад к играм", use_container_width=True):
            st.session_state.current_game = None
            st.rerun()
        return

    # Показываем прогресс
    if block['guessed']:
        st.success(f"✅ Уже угаданы: {', '.join(block['guessed'])}")

    # Определяем сколько элементов угадывать
    elements_to_guess = block['level'] - len(block['guessed'])

    if elements_to_guess == 0:
        st.balloons()
        st.success(f"🎉 Поздравляем! Вы полностью разгадали '{block['spell_name']}'!")
        st.write(f"**Полная комбинация:** {block['combination']}")

        # Помечаем попытку как использованную
        block['attempts'] += 1
        block['last_played'] = datetime.now().strftime("%H:%M:%S")

        if st.button("← Назад к играм", use_container_width=True):
            st.session_state.current_game = None
            st.rerun()
        return

    # Игровой интерфейс
    st.subheader(f"Угадайте {elements_to_guess} элементов:")

    # Выбор элементов
    selected_elements = []
    guess_cols = st.columns(min(4, elements_to_guess))

    for i in range(elements_to_guess):
        with guess_cols[i % 4]:
            element = st.selectbox(
                f"Элемент {i + 1}",
                ELEMENTS,
                key=f"game_{block['id']}_{i}"
            )
            selected_elements.append(element)

    if st.button("🔍 **Проверить**", type="primary", use_container_width=True):
        # Используем попытку
        block['attempts'] += 1
        block['last_played'] = datetime.now().strftime("%H:%M:%S")

        # Проверяем угаданные элементы
        actual_elements = block['elements'][len(block['guessed']):]
        new_guessed = []

        for selected, actual in zip(selected_elements, actual_elements):
            if selected == actual:
                new_guessed.append(actual)

        if new_guessed:
            # Сохраняем угаданные элементы
            block['guessed'].extend(new_guessed)
            st.success(f"✅ Угадано {len(new_guessed)} элементов!")

            # Проверяем полное угадывание
            if len(block['guessed']) == block['level']:
                st.balloons()
                st.success(f"🎉 Вы полностью разгадали заклинание!")
                st.write(f"**Полная комбинация:** {block['combination']}")

            st.rerun()
        else:
            st.error("❌ Элементы не угаданы!")
            st.info("Попытка использована. Для новой попытки нажмите '🔄 Запросить повтор' в игровом блоке.")
            st.rerun()

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Назад к играм", use_container_width=True):
            st.session_state.current_game = None
            st.rerun()
    with col2:
        if st.button("🏠 На главную", use_container_width=True):
            st.session_state.current_game = None
            st.rerun()


# ========== ГЛАВНЫЙ ИНТЕРФЕЙС ==========
def main():
    init_session_state()

    # Сайдбар
    st.sidebar.title("⚔️ D&D Spell Caster")
    st.sidebar.caption("🟢 Онлайн-режим активен")

    if st.session_state.user_type == "client":
        client_interface()

    elif st.session_state.user_type == "host_login":
        with st.sidebar:
            st.header("Вход для Мастера")
            password = st.text_input("Пароль", type="password")

            if st.button("Войти", type="primary", use_container_width=True):
                if password == HOST_PASSWORD:
                    st.session_state.user_type = "host"
                    st.session_state.current_user = "Мастер"
                    st.rerun()
                else:
                    st.error("Неверный пароль!")

            if st.button("← Назад", use_container_width=True):
                st.session_state.user_type = "client"
                st.rerun()

        st.info("Войдите как Мастер для управления комбинациями")

    elif st.session_state.user_type == "host":
        with st.sidebar:
            st.success(f"👑 Вы вошли как Мастер")
            if st.button("🚪 Выйти", use_container_width=True):
                st.session_state.user_type = "client"
                st.session_state.current_user = "Игрок"
                st.rerun()

        host_interface()


if __name__ == "__main__":
    main()