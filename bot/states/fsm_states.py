from aiogram.fsm.state import State, StatesGroup


class MainMenuStates(StatesGroup):
    waiting_for_language = State()
    waiting_for_query = State()


class SearchStates(StatesGroup):
    waiting_for_search_type = State()
    waiting_for_gs_select_entity = State()
    waiting_for_gs_action_entity = State()
    waiting_for_gs_add_to_list = State()


class UserListStates(StatesGroup):
    waiting_for_ls_select_entity = State()
    waiting_for_ls_action_entity = State()
    waiting_for_ls_entity_change_status = State()
    waiting_for_ls_entity_change_rating = State()
    waiting_for_ls_entity_change_season = State()
    waiting_for_ls_entity_delete_entity = State()
