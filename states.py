from aiogram.fsm.state import State, StatesGroup


class VideoState(StatesGroup):
    waiting_for_video = State()


class AudioState(StatesGroup):
    waiting_for_audio = State()


class Mp3State(StatesGroup):
    waiting_for_mp3 = State()


class KeywordState(StatesGroup):
    waiting_for_text = State()