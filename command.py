#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
bot command
"""
from telegram import Update, Bot, MessageEntity
from telegram.ext import Dispatcher
from telegram.chatmember import ChatMember
from constant import START_MSG, ADD_ADMIN_OK_MSG, RUN, ADMIN, BOT_NO_ADMIN_MSG, BOT_IS_ADMIN_MSG, ID_MSG, ADMIN_FORMAT, \
    GET_ADMINS_MSG, GROUP_FORMAT
from tool import command_wrap, check_admin
from admin import update_admin_list
from module import DBSession
from module.user import User
from module.group import Group


@command_wrap()
def start(bot, update):
    """
    send start info
    """
    bot.send_message(chat_id=update.message.chat_id, text=START_MSG)


@command_wrap(name="add", pass_args=True)
@check_admin()
def add_admin(bot, update, args):
    """
    add admin
    :param bot:
    :param update:
    :param args:
    :return:
    """
    if not len(args):
        # TODO add msg
        return
    # TODO check id
    session = DBSession()
    for user_id in args:
        user = User(id=user_id, isadmin=True)
        session.merge(user)
    session.commit()
    session.close()
    update_admin_list()
    bot.send_message(chat_id=update.message.chat_id, text=ADD_ADMIN_OK_MSG)


@command_wrap()
@check_admin()
def run(bot, update):
    """
    :param bot:
    :type bot: Bot
    :param update:
    :type update: Update
    :return:
    """
    bot_id = bot.get_me()['id']
    info = bot.get_chat_member(update.message.chat_id, bot_id)
    if info['status'] == ADMIN:
        bot.send_message(chat_id=update.message.chat_id, text=BOT_NO_ADMIN_MSG)
        return
    session = DBSession()
    group = Group(id=update.message.chat_id, title=update.message.chat.title, link=update.message.chat.invite_link)
    session.merge(group)
    session.commit()
    session.close()
    bot.send_message(chat_id=update.message.chat_id, text=BOT_IS_ADMIN_MSG)
    return RUN


@command_wrap(pass_args=True)
@check_admin()
def clearwarns(bot, update, args):
    user_list = [args]
    if update.message.reply_to_message:
        user_list.append(update.reply_to_message.from_user['id'])
    if update.message.entities:
        for entity in update.message.entities:
            if entity.type == MessageEntity.MENTION:
                user_list.append(entity.user['id'])

    dispatcher = Dispatcher.get_instance()
    user_data = dispatcher.user_data
    for user in user_list:
        user_data[user]['warn'] = 0


@command_wrap(name='id')
def get_id(bot, update):
    """

    :param bot:
    :param update:
    :return:
    """
    bot.send_message(chat_id=update.message.chat_id,
                     text=ID_MSG.format(user_id=update.message.from_user['id'],
                                        group_id=update.message.chat_id
                                        )
                     )


@command_wrap()
def admins(bot, update):
    """

    :param bot:
    :type bot: Bot
    :param update:
    :return:
    """
    admin_list = bot.get_chat_administrators(chat_id=update.message.chat_id)
    createors = ""
    adminors = ""
    for admin in admin_list:
        if admin['status'] == ChatMember.CREATOR:
            createors = createors + ADMIN_FORMAT.format(username=admin.user.full_name, user_id=admin.user.id)
        if admin['status'] == ChatMember.ADMINISTRATOR:
            adminors = adminors + ADMIN_FORMAT.format(username=admin.user.full_name, user_id=admin.user.id)
    bot.send_message(chat_id=update.message.chat_id, text=GET_ADMINS_MSG.format(creators=createors, admins=adminors))


@command_wrap()
@check_admin()
def get_groups(bot, update):
    """
    :param bot:
    :type bot: Bot
    :param update:
    :type update: Update
    :return:
    """
    session = DBSession()
    groups = session.query(Group).all()
    ret_text = ""
    for group in groups:
        info = bot.get_chat(chat_id=group.id)
        ret_text = ret_text + GROUP_FORMAT.format(group_title=info.title, group_id=info.id, group_link=info.invite_link)
