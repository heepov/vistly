from aiogram.fsm.state import State, StatesGroup


class MainMenuStates(StatesGroup):
    waiting_for_language = State()
    waiting_for_query = State()


class SearchStates(StatesGroup):
    waiting_for_search_type = State()


class SearchOmdbStates(StatesGroup):
    waiting_for_omdb_selection = State()
    waiting_for_omdb_action_entity = State()
    waiting_for_omdb_entity_add_to_list = State()


class SearchKpStates(StatesGroup):
    waiting_for_kp_selection = State()
    waiting_for_kp_action_entity = State()
    waiting_for_kp_entity_add_to_list = State()


class UserListStates(StatesGroup):
    waiting_for_list_search_selection = State()
    waiting_for_list_selection = State()
    waiting_for_list_action_entity = State()
    waiting_for_list_entity_change_status = State()
    waiting_for_list_entity_change_rating = State()
    waiting_for_list_entity_change_comment = State()
    waiting_for_list_entity_change_season = State()
    waiting_for_list_entity_delete_entity = State()
