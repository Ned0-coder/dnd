import streamlit as st
from typing import List, Dict, Optional
from datetime import datetime
import time

# ========== КОНФИГУРАЦИЯ ==========
HOST_PASSWORD = "IamDM"  # Секретный пароль для ДМа
ELEMENTS = ["Огонь", "Вода", "Земля", "Молния", "Лед", "Жизнь", "Смерть", "Щит"]
ELEMENT_SYMBOLS = {
    "Огонь": "🔥",
    "Вода": "💧", 
    "Земля": "🌍",
    "Молния": "⚡",
    "Лед": "❄️",
    "Жизнь": "🌿",
    "Смерть": "💀",
    "Щит": "🛡️"
}
ELEMENT_COLORS = {
    "Огонь": "#FF6B6B",
    "Вода": "#4ECDC4", 
    "Земля": "#D4A76A",
    "Молния": "#FFD166",
    "Лед": "#A0D2FF",
    "Жизнь": "#06D6A0",
    "Смерть": "#6A0572",
    "Щит": "#118AB2"
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

# ========== ГЛОБАЛЬНЫЕ ДАННЫЕ ДЛЯ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ ==========
@st.cache_resource(ttl=60)
def get_shared_data():
    """Создает общие данные для ВСЕХ пользователей"""
    return {
        "spell_combinations": {},
        "client_requests": [],
        "game_blocks": [],
        "last_request_id": 0,
        "last_block_id": 0,
        "users": {},
        "last_global_update": time.time()
    }

shared_data = get_shared_data()

# ========== ИНИЦИАЛИЗАЦИЯ СЕССИИ ПОЛЬЗОВАТЕЛЯ ==========
def init_user_session():
    """Инициализация сессии для текущего пользователя"""
    if "user_id" not in st.session_state:
        st.session_state.user_id = str(time.time()) + str(hash(str(time.time())))
    
    if "user_name" not in st.session_state:
        st.session_state.user_name = f"Игрок_{int(time.time()) % 10000}"
    
    if "user_type" not in st.session_state:
        st.session_state.user_type = "guest"
    
    if "current_game" not in st.session_state:
        st.session_state.current_game = None
    
    if "selected_spell" not in st.session_state:
        st.session_state.selected_spell = None
    
    if st.session_state.user_id not in shared_data["users"]:
        shared_data["users"][st.session_state.user_id] = {
            "name": st.session_state.user_name,
            "type": st.session_state.user_type,
            "last_active": time.time()
        }

def update_user_activity():
    """Обновляет время активности пользователя"""
    if st.session_state.user_id in shared_data["users"]:
        shared_data["users"][st.session_state.user_id]["last_active"] = time.time()

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def format_element_option(element: str) -> str:
    """Форматирует элемент для отображения в выпадающем списке"""
    symbol = ELEMENT_SYMBOLS.get(element, "❓")
    return f"{symbol} {element}"

def parse_element_option(option: str) -> str:
    """Парсит элемент из форматированной строки"""
    if " " in option:
        return option.split(" ", 1)[1]
    return option

def create_element_display(elements: List[str]) -> str:
    """Создает строку для отображения комбинации элементов"""
    return " + ".join([ELEMENT_SYMBOLS.get(e, "❓") for e in elements])

def check_guessed_elements(player_guesses: List[str], actual_elements: List[str]) -> List[str]:
    """
    Проверяет угаданные элементы с правильной логикой:
    - Каждый элемент проверяется отдельно
    - Порядок не важен для проверки
    - Одинаковые элементы считаются отдельно
    """
    guessed = []
    actual_copy = actual_elements.copy()
    
    for guess in player_guesses:
        if guess in actual_copy:
            guessed.append(guess)
            actual_copy.remove(guess)  # Удаляем угаданный элемент
    
    return guessed

def get_or_create_game_block(spell_name: str, level: int, user_name: str = "Система") -> Optional[Dict]:
    """Получает существующий игровой блок или создает новый"""
    existing_block = next((b for b in shared_data["game_blocks"] 
                         if b['spell_name'] == spell_name), None)
    
    if existing_block:
        return existing_block
    
    spell_combo = shared_data["spell_combinations"].get(spell_name)
    
    if spell_combo:
        new_block = {
            "id": shared_data["last_block_id"] + 1,
            "spell_name": spell_name,
            "level": level,
            "combination": create_element_display(spell_combo['elements']),
            "elements": spell_combo['elements'],
            "guessed": [],
            "attempts": 0,
            "max_attempts": 1,
            "is_active": True,
            "created_by": user_name,
            "created_at": datetime.now().strftime("%H:%M:%S"),
            "last_played": None
        }
        shared_data["last_block_id"] += 1
        shared_data["game_blocks"].append(new_block)
        return new_block
    
    return None

def create_repeat_request(spell_name: str, level: int, user_name: str, user_id: str):
    """Создает запрос на повторную попытку"""
    new_request = {
        "id": shared_data["last_request_id"] + 1,
        "user_name": user_name,
        "user_id": user_id,
        "spell_name": spell_name,
        "level": level,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "status": "ожидает",
        "type": "повтор"
    }
    shared_data["last_request_id"] += 1
    shared_data["client_requests"].append(new_request)
    return new_request

def create_new_request(spell_name: str, level: int, user_name: str, user_id: str):
    """Создает новый запрос на заклинание"""
    new_request = {
        "id": shared_data["last_request_id"] + 1,
        "user_name": user_name,
        "user_id": user_id,
        "spell_name": spell_name,
        "level": level,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "status": "ожидает",
        "type": "новый"
    }
    shared_data["last_request_id"] += 1
    shared_data["client_requests"].append(new_request)
    return new_request

# ========== РЕГИСТРАЦИЯ И ВХОД ==========
def registration_interface():
    """Интерфейс регистрации и входа"""
    st.title("⚔️ D&D Spell Caster - Выберите роль")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎮 Стать Игроком")
        player_name = st.text_input("Введите имя персонажа", key="reg_player_name")
        
        if st.button("🎮 **Войти как Игрок**", 
                    use_container_width=True, 
                    type="primary",
                    help="Начать игру в роли игрока"):
            if player_name:
                st.session_state.user_name = player_name
                st.session_state.user_type = "player"
                shared_data["users"][st.session_state.user_id] = {
                    "name": player_name,
                    "type": "player",
                    "last_active": time.time()
                }
                st.rerun()
    
    with col2:
        st.markdown("### 👑 Стать Мастером")
        host_name = st.text_input("Введите имя Мастера", key="reg_host_name")
        host_password = st.text_input("Пароль", type="password", key="reg_host_pass")
        
        if st.button("👑 **Войти как Мастер**", 
                    use_container_width=True,
                    help="Войти в режим мастера (требуется пароль)"):
            if host_name and host_password == HOST_PASSWORD:
                st.session_state.user_name = host_name
                st.session_state.user_type = "host"
                shared_data["users"][st.session_state.user_id] = {
                    "name": host_name,
                    "type": "host",
                    "last_active": time.time()
                }
                st.rerun()
            elif host_password and host_password != HOST_PASSWORD:
                st.error("❌ Неверный пароль!")
    
    st.markdown("---")
    st.markdown("""
    ### 📖 Как это работает:
    
    **🎮 Для Игроков:**
    1. Введите имя персонажа
    2. Выберите заклинание
    3. Отправьте запрос Мастеру
    4. Угадывайте комбинации элементов
    5. Запрашивайте новые попытки
    
    **👑 Для Мастера:**
    1. Введите пароль
    2. Создавайте комбинации для заклинаний
    3. Отвечайте на запросы игроков
    4. Следите за прогрессом
    """)

# ========== ФУНКЦИИ ДЛЯ ХОСТА ==========
def host_interface():
    """Интерфейс хоста"""
    update_user_activity()
    
    st.title(f"👑 Панель Мастера: {st.session_state.user_name}")
    
    # Онлайн-статистика
    with st.expander("📡 Онлайн-статистика", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            active_users = [u for u in shared_data["users"].values() 
                          if time.time() - u["last_active"] < 300]
            st.metric("👥 Онлайн", len(active_users))
        with col2:
            st.metric("🎮 Игроков", len([u for u in active_users if u["type"] == "player"]))
        with col3:
            st.metric("🕒 Обновление", datetime.now().strftime("%H:%M:%S"))
    
    # Переключение режимов
    col_view1, col_view2 = st.columns(2)
    with col_view1:
        if st.button("📋 Панель мастера", use_container_width=True, 
                    type="primary" if not st.session_state.get("show_client_table", False) else "secondary"):
            st.session_state.show_client_table = False
            st.rerun()
    with col_view2:
        if st.button("🎮 Стол игроков", use_container_width=True,
                    type="primary" if st.session_state.get("show_client_table", False) else "secondary"):
            st.session_state.show_client_table = True
            st.rerun()
    
    if st.session_state.get("show_client_table", False):
        display_client_table_for_host()
        return
    
    # Основная панель мастера
    st.header("🔮 Управление комбинациями")
    
    # Общая статистика
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📦 Игровых блоков", len(shared_data["game_blocks"]))
    with col2:
        active_requests = len([r for r in shared_data["client_requests"] if r['status'] == 'ожидает'])
        st.metric("📨 Ожидают", active_requests)
    with col3:
        st.metric("🧩 Комбинаций", len(shared_data["spell_combinations"]))
    
    # Разделение на две колонки
    requests_col, combos_col = st.columns(2)
    
    with requests_col:
        st.subheader("📨 Запросы игроков")
        
        pending_requests = [r for r in shared_data["client_requests"] if r['status'] == 'ожидает']
        
        if not pending_requests:
            st.info("Нет ожидающих запросов")
        else:
            for req in pending_requests[:]:
                with st.expander(f"{'🔄' if req['type'] == 'повтор' else '🔔'} {req['spell_name']} (Ур. {req['level']})", expanded=True):
                    
                    if req['type'] == 'повтор':
                        st.warning(f"**ПОВТОРНЫЙ ЗАПРОС** от {req['user_name']}")
                    else:
                        st.write(f"**Игрок:** {req['user_name']}")
                    
                    st.write(f"**Тип:** {'Повторная попытка' if req['type'] == 'повтор' else 'Новый запрос'}")
                    st.write(f"**Время:** {req['timestamp']}")
                    
                    existing_combo = shared_data["spell_combinations"].get(req['spell_name'])
                    
                    if existing_combo:
                        st.success(f"✅ Комбинация существует: {create_element_display(existing_combo['elements'])}")
                        
                        existing_block = next((b for b in shared_data["game_blocks"] 
                                             if b['spell_name'] == req['spell_name']), None)
                        
                        if existing_block:
                            st.info(f"🎮 Игровой блок уже создан")
                            
                            if req['type'] == 'повтор':
                                if st.button("✅ Разрешить повторную попытку", key=f"allow_repeat_{req['id']}", use_container_width=True):
                                    existing_block['attempts'] = 0
                                    req['status'] = 'обработан'
                                    st.success(f"Повторная попытка разрешена для {req['spell_name']}")
                                    st.rerun()
                            else:
                                if st.button("🎮 Создать/обновить игру", key=f"create_game_{req['id']}", use_container_width=True):
                                    if not existing_block:
                                        get_or_create_game_block(req['spell_name'], req['level'], req['user_name'])
                                    req['status'] = 'обработан'
                                    st.rerun()
                        else:
                            if st.button("🎮 Создать игру", key=f"create_new_{req['id']}", use_container_width=True):
                                get_or_create_game_block(req['spell_name'], req['level'], req['user_name'])
                                req['status'] = 'обработан'
                                st.rerun()
                    else:
                        st.warning("❌ Комбинация не найдена")
                        
                        st.write("**Создать комбинацию:**")
                        
                        num_elements = req['level']
                        combo_cols = st.columns(min(4, num_elements))
                        new_combo = []
                        
                        for i in range(num_elements):
                            with combo_cols[i % 4]:
                                # Используем форматированные элементы со смайликами
                                formatted_elements = [format_element_option(e) for e in ELEMENTS]
                                element_option = st.selectbox(
                                    f"Элемент {i+1}",
                                    formatted_elements,
                                    key=f"host_new_{req['id']}_{i}"
                                )
                                element = parse_element_option(element_option)
                                new_combo.append(element)
                        
                        col_save, col_reject = st.columns(2)
                        with col_save:
                            if st.button("💾 Сохранить и создать игру", key=f"save_{req['id']}", use_container_width=True, type="primary"):
                                shared_data["spell_combinations"][req['spell_name']] = {
                                    "combination": create_element_display(new_combo),
                                    "elements": new_combo
                                }
                                
                                get_or_create_game_block(req['spell_name'], req['level'], req['user_name'])
                                
                                req['status'] = 'обработан'
                                st.rerun()
                        
                        with col_reject:
                            if st.button("❌ Отклонить", key=f"reject_{req['id']}", use_container_width=True):
                                req['status'] = 'отклонен'
                                st.rerun()
    
    with combos_col:
        st.subheader("🧩 Существующие комбинации")
        
        if not shared_data["spell_combinations"]:
            st.info("Нет созданных комбинаций")
        else:
            search_combo = st.text_input("🔍 Поиск комбинации", placeholder="Введите название заклинания...", key="host_combo_search")
            
            filtered_combos = list(shared_data["spell_combinations"].items())
            if search_combo:
                filtered_combos = [(k, v) for k, v in filtered_combos if search_combo.lower() in k.lower()]
            
            for spell_name, combo_data in filtered_combos:
                with st.expander(f"🔮 {spell_name} - {combo_data['combination']}", expanded=False):
                    block = next((b for b in shared_data["game_blocks"] 
                                if b['spell_name'] == spell_name), None)
                    
                    if block:
                        st.write(f"**Статус:** {'🎮 Активна' if block['attempts'] < block['max_attempts'] else '⏳ Ожидает повторного запроса'}")
                        st.write(f"**Угадано:** {len(block['guessed'])}/{block['level']} элементов")
                        st.write(f"**Создал:** {block['created_by']}")
                    
                    st.write("**Редактировать комбинацию:**")
                    
                    num_elements = len(combo_data['elements'])
                    edit_cols = st.columns(min(4, num_elements))
                    edited_combo = []
                    
                    for i in range(num_elements):
                        with edit_cols[i % 4]:
                            current_element = combo_data['elements'][i]
                            formatted_elements = [format_element_option(e) for e in ELEMENTS]
                            element_option = st.selectbox(
                                f"Эл. {i+1}",
                                formatted_elements,
                                index=ELEMENTS.index(current_element) if current_element in ELEMENTS else 0,
                                key=f"edit_combo_{spell_name}_{i}"
                            )
                            element = parse_element_option(element_option)
                            edited_combo.append(element)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("💾 Обновить", key=f"update_{spell_name}", use_container_width=True):
                            shared_data["spell_combinations"][spell_name] = {
                                "combination": create_element_display(edited_combo),
                                "elements": edited_combo
                            }
                            
                            if block:
                                block['combination'] = create_element_display(edited_combo)
                                block['elements'] = edited_combo
                            
                            st.rerun()
                    
                    with col2:
                        if st.button("🔄 Сбросить попытки", key=f"reset_attempts_{spell_name}", use_container_width=True):
                            if block:
                                block['attempts'] = 0
                            st.rerun()
                    
                    with col3:
                        if st.button("🗑️ Удалить", key=f"delete_{spell_name}", use_container_width=True):
                            del shared_data["spell_combinations"][spell_name]
                            shared_data["game_blocks"] = [b for b in shared_data["game_blocks"] 
                                                          if b['spell_name'] != spell_name]
                            st.rerun()

def display_client_table_for_host():
    """Отображение стола клиентов для хоста"""
    st.title("🎮 Стол игроков (режим просмотра)")
    
    if not shared_data["game_blocks"]:
        st.info("Нет активных игр")
        return
    
    search_game = st.text_input("🔍 Поиск игры", placeholder="Введите название заклинания...", key="host_game_search")
    
    filtered_games = shared_data["game_blocks"]
    if search_game:
        filtered_games = [b for b in filtered_games if search_game.lower() in b['spell_name'].lower()]
    
    for block in filtered_games:
        with st.container():
            st.markdown("---")
            
            col_title, col_status = st.columns([3, 1])
            with col_title:
                status_icon = "✅" if len(block['guessed']) == block['level'] else "🎮" if block['attempts'] < block['max_attempts'] else "⏳"
                st.write(f"**{status_icon} {block['spell_name']}** (Ур. {block['level']})")
                st.caption(f"Создал: {block['created_by']} | Попыток использовано: {block['attempts']}")
            
            with col_status:
                progress = len(block['guessed']) / block['level']
                st.progress(progress)
                st.caption(f"{len(block['guessed'])}/{block['level']}")
            
            st.write("**Прогресс игроков:**")
            
            element_cols = st.columns(block['level'])
            for i in range(block['level']):
                with element_cols[i]:
                    if i < len(block['guessed']):
                        element = block['guessed'][i]
                        color = ELEMENT_COLORS.get(element, "#CCCCCC")
                        symbol = ELEMENT_SYMBOLS.get(element, "❓")
                        
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
                        symbol = ELEMENT_SYMBOLS.get(actual_element, "❓")
                        
                        st.markdown(
                            f'<div style="background-color: {color}; padding: 10px; border-radius: 50%; '
                            f'width: 50px; height: 50px; display: flex; align-items: center; '
                            f'justify-content: center; margin: 0 auto; border: 2px dashed #666; opacity: 0.6;">'
                            f'<span style="font-size: 1.2em;">{symbol}</span></div>',
                            unsafe_allow_html=True
                        )
                        st.caption(f"? {actual_element}")

# ========== ФУНКЦИИ ДЛЯ ИГРОКА ==========
def player_interface():
    """Интерфейс игрока"""
    update_user_activity()
    
    st.title(f"🎮 Игрок: {st.session_state.user_name}")
    
    if st.session_state.current_game:
        game_block = next((b for b in shared_data["game_blocks"] 
                         if b['spell_name'] == st.session_state.current_game), None)
        if game_block:
            play_spell_game(game_block)
            return
    
    # Основной интерфейс
    col_search, col_games = st.columns([1, 2])
    
    with col_search:
        st.header("🔍 Выбор заклинания")
        
        spell_names = [spell["name"] for spell in SPELLS_DB]
        selected_spell = st.selectbox(
            "Выберите заклинание:",
            options=[""] + spell_names,
            format_func=lambda x: "👇 Выберите из списка" if x == "" else x,
            key="player_spell_select"
        )
        
        st.markdown("---")
        st.write("### Действия:")
        
        if selected_spell:
            spell = next((s for s in SPELLS_DB if s["name"] == selected_spell), None)
            
            if spell:
                existing_block = next((b for b in shared_data["game_blocks"] 
                                     if b['spell_name'] == spell['name']), None)
                
                existing_request = next((r for r in shared_data["client_requests"] 
                                       if r['spell_name'] == spell['name'] and 
                                       r['user_id'] == st.session_state.user_id and
                                       r['status'] == 'ожидает'), None)
                
                # Кнопка 1: Играть
                if existing_block and existing_block['attempts'] < existing_block['max_attempts']:
                    if st.button("🎮 **Играть**", 
                               use_container_width=True, 
                               type="primary",
                               key="btn_play"):
                        st.session_state.current_game = spell['name']
                        st.rerun()
                else:
                    st.button("🎮 Играть", 
                            disabled=True,
                            use_container_width=True,
                            help="Игра недоступна или попытка использована",
                            key="btn_play_disabled")
                
                # Кнопка 2: Запросить игру
                if not existing_block and not existing_request:
                    if st.button("📤 **Запросить игру у мастера**", 
                               use_container_width=True,
                               type="secondary",
                               key="btn_request"):
                        create_new_request(spell['name'], spell['level'], 
                                         st.session_state.user_name, st.session_state.user_id)
                        st.success("📨 Запрос отправлен мастеру!")
                        st.rerun()
                else:
                    st.button("📤 Запросить игру у мастера", 
                            disabled=True,
                            use_container_width=True,
                            help="Игра уже существует или запрос ожидает",
                            key="btn_request_disabled")
                
                # Кнопка 3: Запросить повтор
                if existing_block and existing_block['attempts'] >= existing_block['max_attempts']:
                    if not existing_request or existing_request['type'] != 'повтор':
                        if st.button("🔄 **Запросить повторную попытку**", 
                                   use_container_width=True,
                                   key="btn_repeat"):
                            create_repeat_request(spell['name'], spell['level'], 
                                                st.session_state.user_name, st.session_state.user_id)
                            st.success("📨 Запрос на повтор отправлен!")
                            st.rerun()
                    else:
                        st.button("🔄 Запросить повторную попытку", 
                                disabled=True,
                                use_container_width=True,
                                help="Запрос уже отправлен",
                                key="btn_repeat_disabled")
                else:
                    st.button("🔄 Запросить повторную попытку", 
                            disabled=True,
                            use_container_width=True,
                            help="Попытка еще не использована",
                            key="btn_repeat_disabled2")
                
                # Кнопка 4: Посмотреть прогресс
                if existing_block:
                    if st.button("👁️ **Посмотреть прогресс**", 
                               use_container_width=True,
                               key="btn_view"):
                        st.session_state.current_game = spell['name']
                        st.rerun()
                else:
                    st.button("👁️ Посмотреть прогресс", 
                            disabled=True,
                            use_container_width=True,
                            help="Игра не создана",
                            key="btn_view_disabled")
                
                # Информация
                st.markdown("---")
                st.write(f"**Информация:**")
                st.write(f"- **Уровень:** {spell['level']}")
                
                if existing_block:
                    st.write(f"- **Статус:** {'🎮 Доступно' if existing_block['attempts'] < existing_block['max_attempts'] else '⏳ Ожидает повторного запроса'}")
                    st.write(f"- **Угадано:** {len(existing_block['guessed'])}/{existing_block['level']}")
        else:
            st.button("🎮 Играть", disabled=True, use_container_width=True)
            st.button("📤 Запросить игру у мастера", disabled=True, use_container_width=True)
            st.button("🔄 Запросить повторную попытку", disabled=True, use_container_width=True)
            st.button("👁️ Посмотреть прогресс", disabled=True, use_container_width=True)
    
    with col_games:
        st.header("🎮 Активные игры")
        
        my_requests = [r for r in shared_data["client_requests"] 
                      if r['user_id'] == st.session_state.user_id and r['status'] == 'ожидает']
        if my_requests:
            with st.expander("📨 Мои запросы", expanded=True):
                for req in my_requests:
                    st.write(f"• **{req['spell_name']}** ({'повтор' if req['type'] == 'повтор' else 'новый'}) - {req['timestamp']}")
        
        if not shared_data["game_blocks"]:
            st.info("""
            ### 🎯 Как начать игру:
            1. Выберите заклинание слева
            2. Нажмите "📤 Запросить игру у мастера"
            3. Мастер создаст комбинацию
            4. Игра появится здесь автоматически
            """)
        else:
            game_search = st.text_input("🔍 Поиск по играм", placeholder="Введите название...", key="player_game_search")
            
            filtered_games = shared_data["game_blocks"]
            if game_search:
                filtered_games = [b for b in filtered_games if game_search.lower() in b['spell_name'].lower()]
            
            for block in filtered_games:
                display_player_game_block(block)

def display_player_game_block(block: Dict):
    """Отображение игрового блока для игрока"""
    with st.container():
        st.markdown("---")
        
        col_title, col_status = st.columns([3, 1])
        
        with col_title:
            status_icon = "✅" if len(block['guessed']) == block['level'] else "🎮" if block['attempts'] < block['max_attempts'] else "⏳"
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
        
        element_cols = st.columns(min(8, block['level']))
        for i in range(block['level']):
            with element_cols[i % 8]:
                if i < len(block['guessed']):
                    element = block['guessed'][i]
                    color = ELEMENT_COLORS.get(element, "#CCCCCC")
                    symbol = ELEMENT_SYMBOLS.get(element, "❓")
                    
                    st.markdown(
                        f'<div style="background-color: {color}; padding: 12px; border-radius: 50%; '
                        f'width: 50px; height: 50px; display: flex; align-items: center; '
                        f'justify-content: center; margin: 0 auto; border: 3px solid #06D6A0;">'
                        f'<span style="font-size: 1.3em;">{symbol}</span></div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f'<div style="background-color: #333; padding: 12px; border-radius: 50%; '
                        f'width: 50px; height: 50px; display: flex; align-items: center; '
                        f'justify-content: center; margin: 0 auto; border: 2px solid #666;">'
                        f'<span style="font-size: 1.3em; color: white;">?</span></div>',
                        unsafe_allow_html=True
                    )
        
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
                existing_request = next((r for r in shared_data["client_requests"] 
                                       if r['spell_name'] == block['spell_name'] and 
                                       r['user_id'] == st.session_state.user_id and
                                       r['status'] == 'ожидает'), None)
                
                if not existing_request:
                    if st.button("🔄 **Запросить повтор**", key=f"repeat_btn_{block['id']}", 
                                use_container_width=True, type="secondary"):
                        create_repeat_request(block['spell_name'], block['level'], 
                                            st.session_state.user_name, st.session_state.user_id)
                        st.success("📨 Запрос отправлен!")
                        st.rerun()
                else:
                    st.button("⏳ **Запрос отправлен**", disabled=True, 
                             use_container_width=True, key=f"requested_{block['id']}")
            else:
                if len(block['guessed']) < block['level']:
                    if st.button("👁️ **Посмотреть**", key=f"view_btn_{block['id']}", 
                               use_container_width=True):
                        st.session_state.current_game = block['spell_name']
                        st.rerun()

def play_spell_game(block: Dict):
    """Игровой интерфейс угадывания"""
    st.title(f"🎮 Угадайте: {block['spell_name']}")
    
    if block['attempts'] >= block['max_attempts']:
        st.error("❌ Попытка уже использована!")
        st.info("Нажмите '🔄 Запросить повтор' для получения новой попытки.")
        
        if st.button("← Назад к играм", use_container_width=True):
            st.session_state.current_game = None
            st.rerun()
        return
    
    if block['guessed']:
        st.success(f"✅ Уже угаданы: {', '.join(block['guessed'])}")
    
    elements_to_guess = block['level'] - len(block['guessed'])
    
    if elements_to_guess == 0:
        st.balloons()
        st.success(f"🎉 Поздравляем! Вы полностью разгадали '{block['spell_name']}'!")
        st.write(f"**Полная комбинация:** {block['combination']}")
        
        block['attempts'] += 1
        block['last_played'] = datetime.now().strftime("%H:%M:%S")
        
        if st.button("← Назад к играм", use_container_width=True):
            st.session_state.current_game = None
            st.rerun()
        return
    
    st.subheader(f"Угадайте {elements_to_guess} элементов:")
    
    # Используем форматированные элементы со смайликами
    formatted_elements = [format_element_option(e) for e in ELEMENTS]
    
    selected_elements = []
    guess_cols = st.columns(min(4, elements_to_guess))
    
    for i in range(elements_to_guess):
        with guess_cols[i % 4]:
            element_option = st.selectbox(
                f"Элемент {i+1}",
                formatted_elements,
                key=f"game_{block['id']}_{i}"
            )
            element = parse_element_option(element_option)
            selected_elements.append(element)
    
    if st.button("🔍 **Проверить**", type="primary", use_container_width=True):
        block['attempts'] += 1
        block['last_played'] = datetime.now().strftime("%H:%M:%S")
        
        # Используем правильную логику проверки
        actual_elements = block['elements'][len(block['guessed']):]
        new_guessed = check_guessed_elements(selected_elements, actual_elements)
        
        if new_guessed:
            block['guessed'].extend(new_guessed)
            st.success(f"✅ Угадано {len(new_guessed)} элементов!")
            
            if len(block['guessed']) == block['level']:
                st.balloons()
                st.success(f"🎉 Вы полностью разгадали заклинание!")
                st.write(f"**Полная комбинация:** {block['combination']}")
            
            st.rerun()
        else:
            st.error("❌ Элементы не угаданы!")
            st.info("Попытка использована. Для новой попытки нажмите '🔄 Запросить повтор'.")
            st.rerun()
    
    st.markdown("---")
    if st.button("← Назад к играм", use_container_width=True):
        st.session_state.current_game = None
        st.rerun()

# ========== ГЛАВНЫЙ ИНТЕРФЕЙС ==========
def main():
    init_user_session()
    
    # Сайдбар
    st.sidebar.title("⚔️ D&D Spell Caster")
    
    # Показываем текущего пользователя
    st.sidebar.write(f"**Пользователь:** {st.session_state.user_name}")
    if st.session_state.user_type == "player":
        st.sidebar.write(f"**Роль:** 🎮 Игрок")
    elif st.session_state.user_type == "host":
        st.sidebar.write(f"**Роль:** 👑 Мастер")
    else:
        st.sidebar.write(f"**Роль:** 👤 Гость")
    
    if st.sidebar.button("🔄 Обновить данные", use_container_width=True):
        st.rerun()
    
    if st.session_state.user_type in ["player", "host"]:
        if st.sidebar.button("🚪 Выйти", use_container_width=True):
            if st.session_state.user_id in shared_data["users"]:
                del shared_data["users"][st.session_state.user_id]
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    if st.session_state.user_type == "guest":
        registration_interface()
    elif st.session_state.user_type == "host":
        host_interface()
    elif st.session_state.user_type == "player":
        player_interface()

if __name__ == "__main__":
    main()

