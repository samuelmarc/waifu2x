from pyroaddon import listen
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from pyrogram.enums import ParseMode
from re import findall
from re import MULTILINE
from pyroaddon.helpers import ikb
import os
import random
from requests_toolbelt import MultipartEncoder
import requests
import urllib3
import uvloop
urllib3.disable_warnings()

api_id = '<YOUR_API_ID>'
api_hash = '<YOUR_API_HASH>'
bot_token = '<YOUR_BOT_TOKEN>'
image_mime_types = ['image/jpeg', 'image/png']
api_convert = 'https://api.alcaamado.es/api/v1/waifu2x/convert'

uvloop.install()

waifu2x = Client(name='waifu2x', api_id=api_id, api_hash=api_hash, bot_token=bot_token)
waifu2x.set_parse_mode(ParseMode.HTML)

choices = {}
async def menu_choise(mc: Message or CallbackQuery):
    global choices
    user_id = mc.from_user.id
    choice_text = 'Ok, Choose <u>Noise Reduction</u> and <u>Scale</u>:'
    user_choices = choices.get(user_id)
    if user_choices is None:
        initial_configs = {
            'Noise': 'Medium',
            'Scale': 'No',
        }
        choices[user_id] = initial_configs
        user_choices = initial_configs
    noise_selected = user_choices['Noise']
    scale_selected = user_choices['Scale']
    if noise_selected == 'None':
        noise_button = [('None 🔘', 'n'), ('Medium', f'SetNoiseMedium={user_id}'),
                        ('High', f'SetNoiseHigh={user_id}')]
    elif noise_selected == 'Medium':
        noise_button = [('None', f'SetNoiseNone={user_id}'), ('Medium 🔘', 'n'),
                        ('High', f'SetNoiseHigh={user_id}')]
    elif noise_selected == 'High':
        noise_button = [('None', f'SetNoiseNone={user_id}'), ('Medium', f'SetNoiseMedium={user_id}'),
                        ('High 🔘', 'n')]
    if scale_selected == 'No':
        scale_button = [('No 🔘', 'n'), ('2x', f'SetScale2x={user_id}')]
    elif scale_selected == '2x':
        scale_button = [('No', f'SetScaleNo={user_id}'), ('2x 🔘', 'n')]
    convert_button = [('Convert', f'Convert={user_id}')]
    keyboard = ikb([noise_button, scale_button, convert_button])
    if type(mc) == Message:
        await mc.reply(choice_text, reply_markup=keyboard, quote=True)
    elif type(mc) == CallbackQuery:
        await mc.edit_message_reply_markup(keyboard)


async def get_loading_gifs():
    gif_num = random.randint(a=1, b=8)
    loading_gif = f'https://waifu2x.pro/assets/images/app_loading_waifu_{gif_num}.gif'
    return loading_gif


@waifu2x.on_message(filters.command('start') & filters.private)
async def start(c: Client, m: Message):
    start_message = f'Hello {m.from_user.mention} Welcome to <b>Waifu2x Bot</b>, to get started use the <code>/generate</code> command'
    await m.reply(start_message)


@waifu2x.on_message(filters.command('generate') & filters.private)
async def generate(c: Client, m: Message):
    try:
        answer = await m.chat.ask('Ok, send me the image to be processed (in file):', timeout=30)
    except:
        await m.reply('Time is over.')
        return
    answer_document = answer.document
    if answer_document:
        answer_mime_type = answer_document.mime_type
        if answer_mime_type in image_mime_types:
            await menu_choise(answer)
        else:
            await m.reply('Invalid image file.')
    else:
        await m.reply('Invalid image file.')


@waifu2x.on_callback_query()
async def buttons(c: Client, call: CallbackQuery):
    global choices
    setnoisenone = findall(r'^SetNoiseNone=([0-9]+)$', call.data, flags=MULTILINE)
    setnoisemedium = findall(r'^SetNoiseMedium=([0-9]+)$', call.data, flags=MULTILINE)
    setnoisehigh = findall(r'^SetNoiseHigh=([0-9]+)$', call.data, flags=MULTILINE)
    setscaleno = findall(r'^SetScaleNo=([0-9]+)$', call.data, flags=MULTILINE)
    setscale2x = findall(r'^SetScale2x=([0-9]+)$', call.data, flags=MULTILINE)
    convert = findall(r'^Convert=([0-9]+)$', call.data, flags=MULTILINE)
    if setnoisenone:
        user_id = int(setnoisenone[0])
        try:
            user_choices = choices[user_id]
        except KeyError:
            return
        choices[user_id]['Noise'] = 'None'
        await menu_choise(call)
    elif setnoisemedium:
        user_id = int(setnoisemedium[0])
        try:
            user_choices = choices[user_id]
        except KeyError:
            return
        choices[user_id]['Noise'] = 'Medium'
        await menu_choise(call)
    elif setnoisehigh:
        user_id = int(setnoisehigh[0])
        try:
            user_choices = choices[user_id]
        except KeyError:
            return
        choices[user_id]['Noise'] = 'High'
        await menu_choise(call)
    elif setscaleno:
        user_id = int(setscaleno[0])
        try:
            user_choices = choices[user_id]
        except KeyError:
            return
        choices[user_id]['Scale'] = 'No'
        await menu_choise(call)
    elif setscale2x:
        user_id = int(setscale2x[0])
        try:
            user_choices = choices[user_id]
        except KeyError:
            return
        choices[user_id]['Scale'] = '2x'
        await menu_choise(call)
    elif convert:
        user_id = int(convert[0])
        try:
            user_choices = choices[user_id]
        except KeyError:
            return
        noise_selected = user_choices['Noise']
        scale_selected = user_choices['Scale']
        if noise_selected == 'None':
            noise_selected = '0'
        elif noise_selected == 'Medium':
            noise_selected = '1'
        elif noise_selected == 'High':
            noise_selected = '2'
        if scale_selected == 'No':
            scale_selected = 'false'
        elif scale_selected == '2x':
            scale_selected = 'true'
        image_document = call.message.reply_to_message.document
        if image_document:
            mime_type = image_document.mime_type
            if mime_type in image_mime_types:
                file_name = image_document.file_name
                await c.download_media(image_document, file_name=f'./{file_name}')
                try:
                    image_file = open(file_name, 'rb')
                    image_file_b = image_file.read()
                    image_file.close()
                    multiparty = MultipartEncoder(
                        {
                            'denoise': noise_selected,
                            'scale': scale_selected,
                            'file': (file_name, image_file_b, mime_type)
                        }
                    )
                    headers = {
                        'Connection': 'keep-alive',
                        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
                        'Accept': 'application/json, text/plain, */*',
                        'sec-ch-ua-platform': '"Windows"',
                        'sec-ch-ua-mobile': '?0',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
                        'Content-Type': multiparty.content_type,
                        'Origin': 'https://waifu2x.pro',
                        'Sec-Fetch-Site': 'cross-site',
                        'Sec-Fetch-Mode': 'cors',
                        'Sec-Fetch-Dest': 'empty',
                        'Referer': 'https://waifu2x.pro/',
                        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                    }
                    loading_animation_url = await get_loading_gifs()
                    loading_animation_msg = await call.message.reply_animation(loading_animation_url, caption='Loading...')
                    req = requests.post(api_convert, data=multiparty, headers=headers, verify=False)
                    if req.status_code == 200:
                        os.remove(file_name)
                        hash_image = req.json()
                        hash_image = hash_image['hash']
                        image_jpeg_url = f'https://api.alcaamado.es/api/v2/waifu2x/get?hash={hash_image}&type=jpg'
                        image_png_url = f'https://api.alcaamado.es/api/v2/waifu2x/get?hash={hash_image}&type=png'
                        image_jpeg_path = f'{hash_image}.jpg'
                        image_png_path = f'{hash_image}.png'
                        download_headers = {
                            'Connection': 'keep-alive',
                            'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
                            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                            'sec-ch-ua-mobile': '?0',
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
                            'sec-ch-ua-platform': '"Windows"',
                            'Sec-Fetch-Site': 'cross-site',
                            'Sec-Fetch-Mode': 'no-cors',
                            'Sec-Fetch-Dest': 'empty',
                            'Referer': 'https://waifu2x.pro/',
                            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                        }
                        image_jpeg_req = requests.get(image_jpeg_url, headers=download_headers)
                        image_png_req = requests.get(image_png_url, headers=download_headers)
                        with open(image_jpeg_path, 'wb') as image_jpeg_file:
                            image_jpeg_file.write(image_jpeg_req.content)
                            image_jpeg_file.close()
                        with open(image_png_path, 'wb') as image_png_file:
                            image_png_file.write(image_png_req.content)
                            image_png_file.close()
                        await loading_animation_msg.delete()
                        await call.message.reply_document(image_jpeg_path)
                        await call.message.reply_document(image_png_path)
                        await call.edit_message_text('Completed process, JPG and PNG file below:')
                        os.remove(image_jpeg_path)
                        os.remove(image_png_path)
                    else:
                        await loading_animation_msg.delete()
                        await call.answer(f'HTTP Error: {req.status_code}', show_alert=True)
                except:
                    if os.path.exists(file_name):
                        os.remove(file_name)
                    if os.path.exists(image_jpeg_path):
                        os.remove(image_jpeg_path)
                    if os.path.exists(image_png_path):
                        os.remove(image_png_path)
                    if loading_animation_msg:
                        await loading_animation_msg.delete()
                    await call.answer(f'There was an error processing the image, please try again later.', show_alert=True)
                del choices[user_id]
            else:
                await call.answer('Invalid image file.')
        else:
            await call.answer('The message containing the image has been deleted.')


waifu2x.run()