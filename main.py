#!venv/bin/python
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
from state import GlobalState
from keyboards import get_admin_markup, get_inline_invite_stop_markup
from enum import Enum
from enums import URoles, CWorkes, CStatuses
from answer_generators import sendG_CAccounts, sendG_chats
import client_api
from config import TG_TOCKEN
from repositories.getRepo import get_client_repo, get_user_repo, get_member_repo
from telethon.errors.rpcerrorlist import PhoneCodeExpiredError

storage = MemoryStorage()

bot = Bot(token=TG_TOCKEN)
dp = Dispatcher(bot, storage=storage)


class Bts(Enum):
    """ Надписи на кнопках """
    ACCOUNTS = 'Аккаунты'
    GROUPS = 'Группы'
    GO_TO_MAIN = '◀️На главную'
    ADD_ACCOUNT = 'Добавить аккаунт'
    CANCEL = 'отмена'

MAIN_MARKUP = get_admin_markup((Bts.ACCOUNTS.value, Bts.GROUPS.value))



# @dp.message_handler(commands='start', state=None)
async def start(message: types.Message):
    u_repo = get_user_repo()
    user = await u_repo.get_by_id(message.chat.id)
    if user is None:
        await u_repo.create(
            id=message.from_id,
            first_name=message.chat.first_name,
            last_name=message.chat.last_name,
            username=message.chat.username,
            role_id=URoles.PENDING.value['id']
            )
        await message.answer("Ожидание регистрации")

    elif user.role_id == URoles.ADMIN.value['id']:
        await GlobalState.admin.set()
        await message.answer('Вы в главном меню', reply_markup=MAIN_MARKUP)
    else:
        await message.answer("Ожидание регистрации")


# @dp.message_handler(Text(equals=Bts.ACCOUNTS.value), state=GlobalState.admin)
async def send_accounts(message: types.Message):
    c_repo = get_client_repo()
    accounts = await c_repo.get_all()
    markup = get_admin_markup((Bts.GO_TO_MAIN.value, Bts.ADD_ACCOUNT.value))
    if len(accounts):
        await sendG_CAccounts(message, accounts, reply_markup=markup)
    else:
        await message.answer("Аккаунтов нет. Выберите действие", reply_markup=markup)


# @dp.callback_query_handler(text_contains='client:delete', state=GlobalState.admin)
async def account_delete(call: types.CallbackQuery):
    client_repo = get_client_repo()
    client_id = call.data.split(':')[-1]
    await client_repo.delete(client_id)
    await call.answer(cache_time=60)
    await call.message.answer("Аккаунт удален.")
    await call.message.edit_reply_markup(reply_markup=None)


# @dp.callback_query_handler(text_contains='client:authorization', state=GlobalState.admin)
async def send_authorization_code(call: types.CallbackQuery, state: FSMContext):
    client_repo = get_client_repo()
    client_id = call.data.split(':')[-1]
    client_data = await client_repo.get_by_id(client_id)
    async with state.proxy() as data:
        data['client_data'] = client_data

    if  await client_api.client_is_authorized(client_data):
        client_repo = get_client_repo()
        await client_repo.update(data['client_data'].id, status_id=CStatuses.AUTHORIZED.value['id'])
        await call.message.answer("Аккаунт авторизован!", reply_markup=MAIN_MARKUP)
    else:
        await client_api.send_phone_hash_code(client_data)
        await GlobalState.auth_acc.set()
        await call.message.answer('Введите код: ')
        await call.message.edit_reply_markup(reply_markup=None)


# @dp.message_handler(state=GlobalState.auth_acc)
async def authorization(message: types.Message, state: FSMContext):
    client_repo = get_client_repo()
    async with state.proxy() as data:
        try:
            await client_api.authorize(data['client_data'], int(message.text))
            await client_repo.update(data['client_data'].id, status_id=CStatuses.AUTHORIZED.value['id'])
            await state.finish()
            await GlobalState.admin.set()
            await message.answer("Аккаунт успешно авторизован!", reply_markup=MAIN_MARKUP)
        except PhoneCodeExpiredError as e:
            print(e)
            await message.answer("Авторизация не возможна, попробуйте другйо аккаунт", reply_markup=MAIN_MARKUP)
            await state.finish()
            await GlobalState.admin.set()



# @dp.message_handler(Text(equals=Bts.ADD_ACCOUNT.value), state=GlobalState.admin)
async def ehco_add_account(message: types.Message):
    await GlobalState.set_api_id.set()
    await message.answer('Введите api_id', reply_markup=types.ReplyKeyboardRemove())


# @dp.message_handler(Text(equals=Bts.CANCEL.value, ignore_case=True), commands=Bts.CANCEL.value, state='*')
async def cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None or current_state == 'GlobalState:admin':
        return
    await state.finish()
    await GlobalState.admin.set()
    await message.reply('OK')
    await message.answer('Вы в главном меню', reply_markup=MAIN_MARKUP)


# @dp.message_handler(state=GlobalState.set_api_id)
async def set_api_id(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['api_id'] = int(message.text)
    await GlobalState.set_api_hash.set()
    await message.answer('Введите api_hash')


# @dp.message_handler(state=GlobalState.set_api_hash)
async def set_api_hash(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['api_hash'] = message.text
    await GlobalState.set_phone.set()
    await message.answer('Введите номер телефона в формате: +79998887766')


# @dp.message_handler(state=GlobalState.set_phone)
async def set_phone(message: types.Message, state: FSMContext):
    c_repo = get_client_repo()
    async with state.proxy() as data:
        data['phone'] = message.text
    
    async with state.proxy() as data:
        await c_repo.create(
            work_id=CWorkes.UNWORKING.value['id'],
            status_id=CStatuses.WAITING_AUTHORIZATION.value['id'],
            api_id=data['api_id'],
            api_hash=data['api_hash'],
            phone=data['phone']
        )
    await message.answer("Аккаунт сохранен")

    await GlobalState.admin.set()
    await message.answer('Вы в главном меню', reply_markup=MAIN_MARKUP)


# @dp.message_handler(Text(equals=Bts.GROUPS.value), state=GlobalState.admin)
async def send_chats(message: types.Message):
    client_repo = get_client_repo()
    client  = await client_repo.get_by_status_id(CStatuses.AUTHORIZED.value['id'], limit=1)
    if client:
        chats = await client_api.get_chats(client_data=client[0])
        if chats:
            await sendG_chats(message, client[0], chats)
        else:
            await message.answer("Групп нет.")
    else:
        await message.answer("Нет авторизованых аккаунтов")
        
# @dp.callback_query_handler(text_contains='parsing:', state=GlobalState.admin)
async def parsing(call: types.CallbackQuery):
    await call.answer(cache_time=60)
    await call.message.edit_reply_markup(reply_markup=None)

    client_repo = get_client_repo()
    client_id, chat_id = call.data.split(':')[1:]
    client_data = await client_repo.get_by_id(int(client_id))
    members = await client_api.get_members(client_data, int(chat_id))
    member_repo = get_member_repo()
    new_mem_count = 0
    for mem in members:
        try:
            await member_repo.create(
                id=mem['id'],
                first_name=mem['first_name'],
                last_name=mem['last_name'],
                username=mem['username'],
                chat_id=mem['chat_id'],
            )
            new_mem_count+=1
        except:
            continue
    await call.message.answer(f"Добавлено в базу <b>{new_mem_count}</b> новых пользователей",parse_mode="html")
    

# @dp.callback_query_handler(text_contains='inviting:', state=GlobalState.admin)
async def send_inviting_result(call: types.CallbackQuery):
    await call.answer(cache_time=60)
    await call.message.edit_reply_markup(reply_markup=None)
    chat_id = int(call.data.split(':')[-1])
    client_repo = get_client_repo()
    member_repo = get_member_repo()
    active_accs = await client_repo.get_by_status_id(CStatuses.AUTHORIZED.value['id'])
    active_accs = [acc for acc in active_accs if acc.work_id == CWorkes.UNWORKING.value['id']]
    client_api.stop_invite = False
    members = await member_repo.get_all()
    msg = await call.message.answer(f'Отправленно 0/{len(members)} инвайтов'
                                    , reply_markup=get_inline_invite_stop_markup())
    await client_api.inviting(msg, active_accs, chat_id, members)


# @dp.callback_query_handler(text_contains='stop_inviting:', state=GlobalState.admin)
async def stop_inviting(call: types.CallbackQuery):
    client_api.stop_invite = True
    await call.answer(cache_time=60)
    await call.message.edit_reply_markup(reply_markup=None)


# @dp.message_handler(Text(equals=Bts.GO_TO_MAIN.value), state=GlobalState.admin)
async def go_to_main(message: types.Message):
    await message.answer('Вы в главном меню', reply_markup=MAIN_MARKUP)


# @dp.message_handler()
async def ehco_waiting_for_registration(message: types.Message):
    await message.answer("Ожидание регистрации")


async def test(message: types.Message, state: FSMContext):
    client_repo = get_client_repo()
    client_data = await client_repo.get_by_id(2)
    await client_api.send_phone_hash_code(client_data)



def register_handlers_admin(dp: Dispatcher):

    # dp.register_message_handler(test,Text(equals='conn'))


    dp.register_message_handler(start, commands='start', state=None)

    dp.register_message_handler(send_accounts, Text(equals=Bts.ACCOUNTS.value), state=GlobalState.admin)
    dp.register_message_handler(ehco_add_account, Text(equals=Bts.ADD_ACCOUNT.value), state=GlobalState.admin)
    dp.register_message_handler(cancel, Text(equals=Bts.CANCEL.value, ignore_case=True),  state='*') # любой кроме admin
    dp.register_message_handler(set_api_id, state=GlobalState.set_api_id)
    dp.register_message_handler(set_api_hash, state=GlobalState.set_api_hash)
    dp.register_message_handler(set_phone, state=GlobalState.set_phone)
    dp.register_callback_query_handler(account_delete,text_contains='client:delete', state=GlobalState.admin)
    dp.register_callback_query_handler(send_authorization_code, text_contains='client:authorization', state=GlobalState.admin)
    dp.register_message_handler(authorization,state=GlobalState.auth_acc)

    dp.register_message_handler(send_chats, Text(equals=Bts.GROUPS.value), state=GlobalState.admin)
    dp.register_callback_query_handler(parsing, text_contains='parsing:', state=GlobalState.admin)
    dp.register_callback_query_handler(send_inviting_result, text_contains='inviting:', state=GlobalState.admin)
    dp.register_callback_query_handler(stop_inviting, text_contains='stop_inviting:', state=GlobalState.admin)
    dp.register_message_handler(go_to_main, Text(equals=Bts.GO_TO_MAIN.value), state=GlobalState.admin)
    dp.register_message_handler(ehco_waiting_for_registration)

    

register_handlers_admin(dp)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
