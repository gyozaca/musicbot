import asyncio
import os
import uuid
import aiohttp
import subprocess

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.fsm.context import FSMContext

from config import BOT_TOKEN, AUDD_TOKEN
from states import (
    VideoState,
    AudioState,
    Mp3State,
    KeywordState
)

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🎤 Аудио"),
            KeyboardButton(text="🎬 Видео")
        ],
        [
            KeyboardButton(text="🎵 MP3"),
            KeyboardButton(text="🔎 Ключ. слово")
        ],
        [
            KeyboardButton(text="⬅️ Назад")
        ]
    ],
    resize_keyboard=True
)


async def recognize_music(file_path):

    url = "https://api.audd.io/"

    timeout = aiohttp.ClientTimeout(
        total=300,
        connect=60
    )

    async with aiohttp.ClientSession(
        timeout=timeout
    ) as session:

        with open(file_path, "rb") as f:

            form = aiohttp.FormData()

            form.add_field(
                "api_token",
                AUDD_TOKEN
            )

            form.add_field(
                "return",
                "spotify,apple_music"
            )

            form.add_field(
                "file",
                f,
                filename="audio.mp3",
                content_type="audio/mpeg"
            )

            async with session.post(
                url,
                data=form
            ) as response:

                return await response.json()


@dp.message(CommandStart())
async def start(message: Message):

    await message.answer(
        "🎵 Добро пожаловать в Music Recognizer!\n\n"
        "Выберите способ поиска музыки:",
        reply_markup=main_menu
    )


@dp.message(F.text == "⬅️ Назад")
async def back_to_menu(
    message: Message,
    state: FSMContext
):

    await state.clear()

    await message.answer(
        "🏠 Главное меню",
        reply_markup=main_menu
    )


# ==========================
# MP3
# ==========================

@dp.message(F.text == "🎵 MP3")
async def mp3_mode(
    message: Message,
    state: FSMContext
):

    await state.set_state(
        Mp3State.waiting_for_mp3
    )

    await message.answer(
        "🎵 Отправьте MP3-файл для распознавания."
    )


@dp.message(
    Mp3State.waiting_for_mp3,
    F.audio
)
async def process_mp3(
    message: Message,
    state: FSMContext
):

    filename = (
        f"audio_{message.from_user.id}_"
        f"{uuid.uuid4()}.mp3"
    )

    try:

        status = await message.answer(
            "🔍 Анализирую музыку..."
        )

        file_info = await bot.get_file(
            message.audio.file_id
        )

        await bot.download_file(
            file_info.file_path,
            destination=filename
        )

        result = await recognize_music(
            filename
        )

        if not result.get("result"):

            await status.edit_text(
                "❌ Не удалось определить песню."
            )

            return

        track = result["result"]

        artist = track.get(
            "artist",
            "Неизвестно"
        )

        title = track.get(
            "title",
            "Неизвестно"
        )

        album = track.get("album")

        text = (
            f"🎵 {artist}\n"
            f"🎶 {title}"
        )

        if album:
            text += f"\n💿 {album}"

        await status.edit_text(text)

    except Exception as e:

        await message.answer(
            f"❌ Ошибка:\n{e}"
        )

    finally:

        if os.path.exists(filename):
            os.remove(filename)

        await state.clear()


@dp.message(Mp3State.waiting_for_mp3)
async def wrong_mp3(
    message: Message
):

    await message.answer(
        "❌ Сейчас я ожидаю MP3-файл."
    )


# ==========================
# АУДИО / ГОЛОСОВЫЕ
# ==========================

@dp.message(F.text == "🎤 Аудио")
async def audio_mode(
    message: Message,
    state: FSMContext
):

    await state.set_state(
        AudioState.waiting_for_audio
    )

    await message.answer(
        "🎤 Отправьте голосовое сообщение "
        "или аудиозапись."
    )


@dp.message(
    AudioState.waiting_for_audio,
    F.voice
)
async def process_voice(
    message: Message,
    state: FSMContext
):

    filename = (
        f"voice_{message.from_user.id}_"
        f"{uuid.uuid4()}.ogg"
    )

    try:

        status = await message.answer(
            "🔍 Анализирую запись..."
        )

        file_info = await bot.get_file(
            message.voice.file_id
        )

        await bot.download_file(
            file_info.file_path,
            destination=filename
        )

        result = await recognize_music(
            filename
        )

        if not result.get("result"):

            await status.edit_text(
                "❌ Музыка не найдена."
            )

            return

        track = result["result"]

        await status.edit_text(
            f"🎵 {track.get('artist')}\n"
            f"🎶 {track.get('title')}"
        )

    except Exception as e:

        await message.answer(
            f"❌ Ошибка:\n{e}"
        )

    finally:

        if os.path.exists(filename):
            os.remove(filename)

        await state.clear()


@dp.message(AudioState.waiting_for_audio)
async def wrong_audio(
    message: Message
):

    await message.answer(
        "❌ Сейчас я ожидаю голосовое сообщение."
    )


# ==========================
# ВИДЕО
# ==========================

@dp.message(F.text == "🎬 Видео")
async def video_mode(
    message: Message,
    state: FSMContext
):

    await state.set_state(
        VideoState.waiting_for_video
    )

    await message.answer(
        "🎬 Отправьте видео с музыкой."
    )


@dp.message(
    VideoState.waiting_for_video,
    F.video
)
async def process_video(
    message: Message,
    state: FSMContext
):

    video_file = (
        f"video_{message.from_user.id}_"
        f"{uuid.uuid4()}.mp4"
    )

    audio_file = (
        f"audio_{message.from_user.id}_"
        f"{uuid.uuid4()}.mp3"
    )

    try:

        status = await message.answer(
            "🎬 Извлекаю звук из видео..."
        )

        file_info = await bot.get_file(
            message.video.file_id
        )

        await bot.download_file(
            file_info.file_path,
            destination=video_file
        )

        extract_audio(
            video_file,
            audio_file
        )

        await status.edit_text(
            "🔍 Ищу музыку..."
        )

        result = await recognize_music(
            audio_file
        )

        if not result.get("result"):

            await status.edit_text(
                "❌ Не удалось определить музыку."
            )

            return

        track = result["result"]

        artist = track.get(
            "artist",
            "Неизвестно"
        )

        title = track.get(
            "title",
            "Неизвестно"
        )

        album = track.get("album")

        text = (
            f"🎵 {artist}\n"
            f"🎶 {title}"
        )

        if album:
            text += f"\n💿 {album}"

        await status.edit_text(text)

    except Exception as e:

        await message.answer(
            f"❌ Ошибка:\n{e}"
        )

    finally:

        if os.path.exists(video_file):
            os.remove(video_file)

        if os.path.exists(audio_file):
            os.remove(audio_file)

        await state.clear()


# ==========================
# ПОИСК ПО КЛЮЧЕВОМУ СЛОВУ
# ==========================

@dp.message(F.text == "🔎 Ключ. слово")
async def keyword_mode(
    message: Message,
    state: FSMContext
):

    await state.set_state(
        KeywordState.waiting_for_text
    )

    await message.answer(
        "🔎 Введите название песни "
        "или исполнителя."
    )


@dp.message(
    KeywordState.waiting_for_text,
    F.text
)
async def process_keyword(
    message: Message,
    state: FSMContext
):

    await message.answer(
        f"🔎 Поиск по запросу:\n{message.text}\n\n"
        "🚧 Функция в разработке."
    )

    await state.clear()


async def main():

    print("Бот запущен")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())