import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

TOKEN = "8426552375:AAF3V40mXgUSGEFKncOiv_tQ_L07kVbqZyA"

bot = Bot(token=TOKEN)
dp = Dispatcher()


# --- Машина состояний ---
class VolunteerForm(StatesGroup):
    name = State()
    age = State()
    phone = State()
    topics = State()


# --- /start ---
@dp.message(F.text == "/start")
async def start_cmd(message: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="Сбор денег", callback_data="fundraising")
    kb.button(text="Стать волонтером", callback_data="volunteer")
    kb.adjust(1)
    await message.answer(
        "Приветствую! Я бот от туба, твой ориентир.\nВыберите, что тебя интересует:",
        reply_markup=kb.as_markup()
    )


# ========== Ветка: Готовый сбор денег ==========
@dp.callback_query(F.data == "fundraising")
async def fundraising_handler(callback: CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="Внести пожертвование", callback_data="donate")
    kb.button(text="Вернуться", callback_data="back_start")
    kb.adjust(1)
    await callback.message.edit_text("Выберите действие:", reply_markup=kb.as_markup())


@dp.callback_query(F.data == "donate")
async def donate_handler(callback: CallbackQuery):
    await callback.message.edit_text("Спасибо за пожертвование 🙏")


# ========== Ветка: Волонтерство ==========
@dp.callback_query(F.data == "volunteer")
async def volunteer_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(VolunteerForm.name)
    await callback.message.edit_text("1. Как вас зовут?")


@dp.message(VolunteerForm.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(VolunteerForm.age)
    await message.answer("2. Сколько вам лет?")


@dp.message(VolunteerForm.age)
async def process_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await state.set_state(VolunteerForm.phone)
    await message.answer("3. Оставьте номер телефона, чтобы мы могли связаться с вами")


@dp.message(VolunteerForm.phone)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(VolunteerForm.topics)
    await message.answer(
        "Теперь выберите тематики, в которых хотите участвовать (можно несколько):",
        reply_markup=get_topics_keyboard([])
    )


# --- Словарь тем ---
TOPICS = {
    "topic_kid": "Помощь детям в дет. домах/больницах",
    "topic_online": "Помощь онлайн",
    "topic_pets": "Помощь с животными",
    "topic_clean": "Помощь в облагораживании территорий"
}


# --- Построение клавиатуры с галочками ---
def get_topics_keyboard(selected: list[str]):
    kb = InlineKeyboardBuilder()
    for key, text in TOPICS.items():
        if key in selected:
            text = f"✅ {text}"
        kb.button(text=text, callback_data=key)
    kb.button(text="Завершить", callback_data="finish_topics")
    kb.adjust(1)
    return kb.as_markup()


# --- Обработка выбора тематик ---
@dp.callback_query(F.data.in_(TOPICS.keys()))
async def select_topic(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("topics", [])

    if callback.data in selected:
        selected.remove(callback.data)
    else:
        selected.append(callback.data)

    await state.update_data(topics=selected)

    await callback.message.edit_text(
        "Теперь выберите тематики, в которых хотите участвовать (можно несколько):",
        reply_markup=get_topics_keyboard(selected)
    )
    await callback.answer()


# --- Завершение ---
@dp.callback_query(F.data == "finish_topics")
async def finish_form(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    name = data.get("name")
    age = data.get("age")
    phone = data.get("phone")
    topics = [TOPICS[t] for t in data.get("topics", [])]

    await callback.message.edit_text(
        f"Спасибо за обратную связь!\n\n"
        f"📌 Имя: {name}\n"
        f"📌 Возраст: {age}\n"
        f"📌 Телефон: {phone}\n"
        f"📌 Тематики: {', '.join(topics) if topics else 'не выбраны'}\n\n"
        f"В дальнейшем будем отправлять вам информацию по выбранным темам 🙌"
    )
    await state.clear()


# ========== Общая кнопка назад ==========
@dp.callback_query(F.data == "back_start")
async def back_to_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await start_cmd(callback.message)


# --- Запуск бота ---
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
