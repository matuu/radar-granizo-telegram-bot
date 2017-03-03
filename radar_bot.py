import os
import shutil
import requests
from datetime import datetime
import telebot
from telebot import types


secret = open(".secret", "r")
token = secret.read()
secret.close()
bot = telebot.TeleBot(token=token.strip())

RADAR_TYPE = ['Última imagen', 'Animación', 'Zoom Norte', 'Zoom Centro', 'Zoom Sur']


@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.row("/radar")
    bot.send_message(message.chat.id, "Hola! Envía /radar para solicitar una imagen.", reply_markup=markup)


@bot.message_handler(commands=['help'])
def send_help(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.row("/radar")
    bot.send_message(message.chat.id, "Envía /radar para solicitar una imagen actual.", reply_markup=markup)


@bot.message_handler(commands=['radar'])
def send_options(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row(*RADAR_TYPE[:2])
    markup.row(*RADAR_TYPE[2:4])
    markup.row(RADAR_TYPE[4])
    msg = bot.send_message(message.chat.id, "Seleccioná la imagen que deseas visualizar:", reply_markup=markup)
    bot.register_next_step_handler(msg, send_radar_image)


def send_other_images(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.row("/radar")
    bot.send_message(message.chat.id, "¿Deseas ver otra imagen?", reply_markup=markup)


def send_radar_image(message):
    chat_id = message.chat.id
    name = message.text
    if name == RADAR_TYPE[0]:
        send_image(chat_id, name, "latest.gif")
    elif name == RADAR_TYPE[1]:
        send_image(chat_id, name, "animacion.gif")
    elif name == RADAR_TYPE[2]:
        send_image(chat_id, name, "norte.gif")
    elif name == RADAR_TYPE[3]:
        send_image(chat_id, name, "centro.gif")
    elif name == RADAR_TYPE[4]:
        send_image(chat_id, name, "sur.gif")
    else:
        bot.send_message(chat_id, 'Oooops!!. Opción no válida')
    send_other_images(message)


# default handler for every other text
@bot.message_handler(func=lambda message: message.text not in RADAR_TYPE, content_types=['text'])
def command_default(m):
    # this is the standard reply to a normal message
    bot.send_message(m.chat.id, "Lo siento, no te entiendo. Enviá /help para obtener ayuda sobre lo que puedo hacer.")


def download_image(image, image_path):
    try:
        base_url = "http://www.contingencias.mendoza.gov.ar/radar/"
        response = requests.get("{}{}".format(base_url, image), stream=True, timeout=None)
        with open(image_path, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
        del response
        return True
    except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout):
        return False


def _send_image(chat_id, image_path, caption):
    bot.send_chat_action(chat_id, 'upload_photo')
    try:
        with open(image_path, "rb") as img:
            if "animacion" in image_path:
                bot.send_video(chat_id, img, caption)
            else:
                bot.send_photo(chat_id, img, caption)
    except requests.exceptions.ConnectionError:
        bot.send_message(chat_id, "Ocurrió un error al enviarte la imagen. Por favor, intentá de nuevo.")


def send_image(chat_id, caption, image):
    image_path = os.path.join("tmp", image)
    if os.path.exists(image_path):
        # checar antiguedad
        img_exists = True
        if datetime.timestamp(datetime.now()) - os.path.getmtime(image_path) > 10:  # 10 seconds
            is_updated = download_image(image, image_path)
        else:
            is_updated = True
    else:
        is_updated = download_image(image, image_path)
        img_exists = is_updated
    if not is_updated:
        if img_exists:
            bot.send_message(chat_id, "Uy, lo siento! No puedo acceder "
                                      "a una imagen actualizada.\nTe envío una con fecha "
                                      "{:%d/%m/%Y %H:%I}".format(datetime.fromtimestamp(os.path.getmtime(image_path))))
            _send_image(chat_id, image_path, caption)
        else:
            bot.send_message(chat_id, "Uy, lo siento! No puedo acceder a una imagen actualizada "
                                      "en este momento. Intenta más tarde.")
    else:
        _send_image(chat_id, image_path, caption)


bot.polling()
