from aiogram.fsm.state import State, StatesGroup


class SupportStates(StatesGroup):
    active = State()


class AdminStates(StatesGroup):
    waiting_ttn     = State()   # admin entered ship flow, waiting for TTN text
    waiting_message = State()   # admin entered write flow, waiting for message text
