from aiogram.fsm.state import State, StatesGroup


class MainMenuStates(StatesGroup):
    awaiting_query = State()


class OmdbSearchStates(StatesGroup):
    waiting_for_search_type = State()
    waiting_for_omdb_selection = State()
    waiting_for_omdb_action_entity = State()
    waiting_for_omdb_entity_add_to_list = State()