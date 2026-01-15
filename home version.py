#!/usr/bin/env python3.11
# coding=utf-8

"""
tested in Python 3.11
"""
import csv, pygame, sys, os, serial
from pygame.locals import FULLSCREEN, USEREVENT, KEYUP, K_SPACE, K_RETURN, K_ESCAPE, QUIT, Color, K_p, K_v, K_n
from os.path import isfile, join
from random import randint, shuffle
from time import gmtime, strftime

from pathlib import Path

script_path = Path(__file__).parent.resolve()

debug_mode = True # Modo de depuración (True/False)

class TextRectException(Exception):
    def __init__(self, message=None):
        self.message = message

    def __str__(self):
        return self.message

# Configurations:
FullScreenShow = True  # Pantalla completa automáticamente al iniciar el experimento
test_name = "Stroop Task"
date_name = strftime("%Y-%m-%d_%H-%M-%S", gmtime())

# Image Loading
happy_images_list = [script_path/"media"/"images"/"Happy"/ f for f in os.listdir(
    script_path/"media"/"images"/"Happy") if isfile(join(script_path/"media"/"images"/"Happy", f))]
sad_images_list = [script_path/"media"/"images"/"Sad"/ f for f in os.listdir(
    script_path/"media"/"images"/"Sad") if isfile(join(script_path/"media"/"images"/"Sad", f))]

shuffle(happy_images_list)
shuffle(sad_images_list)

first_experiment_block = [(img, "Happy") for img in happy_images_list[:60]] + [(img, "Sad") for img in happy_images_list[:60]] + \
                         [(img, "Sad") for img in sad_images_list[:60]] + [(img, "Happy") for img in sad_images_list[:60]]

shuffle(first_experiment_block)

second_experiment_block = [(img, "Happy") for img in happy_images_list[:60]] + [(img, "Sad") for img in happy_images_list[:60]] + \
                          [(img, "Sad") for img in sad_images_list[:60]] + [(img, "Happy") for img in sad_images_list[:60]]

shuffle(second_experiment_block)

text_convertor = {"Happy": "Feliz", "Sad": "Triste"}

base_size = 350

# Port address and triggers
lpt_address = 0xD100
trigger_latency = 5
start_trigger = 254
stop_trigger = 255

# Experiment Trigger list

# 001: Cruz de fijación
# 011: Cara Feliz + Palabra Feliz
# 012: Cara Triste + Palabra Triste
# 021: Cara Feliz + Palabra Triste
# 022: Cara Triste + Palabra Feliz
# 100: Respuesta Correcta
# 200: Respuesta Incorrecta
# 250: Time-out (Sin respuesta)
# 030: Estímulo Neutro (Opcional)
# 051: Inicio bloque 1
# 052: Inicio bloque 2

# 254: Start experiment
# 255: Stop experiment

trigger_helper = {
    "fixation": 1,
    "happy_happy": 11,
    "sad_sad": 12,
    "happy_sad": 21,
    "sad_happy": 22,
    "correct_response": 100,
    "incorrect_response": 200,
    "no_response": 250,
    "start_block_1": 51,
    "start_block_2": 52,
    "neutral_stimulus": 30
}

# Onscreen instructions
def select_slide(slide_name, variables=None):

    if variables is None:
        variables = {"blockNumber": 0, "practice": True, "happyV": True, "blockType": "C"}

    basic_slides = {
        'welcome': [
            u"Bienvenido/a, a este experimento!!!",
            " ",
            u"Se te indicará paso a paso que hacer."
        ],
        'Practice_1': [
            u"Empezaremos con una práctica para familiarizarnos con la tarea.",
            " ",
            u"Luego de ver un rostro deberás categorizar su expresión emocional lo más rápido y preciso posible.",
            " ",
        ],
        'Practice_2': [
            u"Ahora haremos una segunda práctica.",
            " ",
            u"Recuerda que luego de ver un rostro deberás categorizar su expresión emocional lo más rápido y preciso posible.",
            " ",
        ],
        'face_block': [
            u"Ahora comenzaremos con el experimento.",
            " ",
            u"En esta prueba vamos a ver una serie de fotografías de rostros de personas en la pantalla.", 
            u"Notará que sobre cada rostro hay una palabra escrita en color rojo.",
            u"" + ("Esta vez s" if variables["blockNumber"] == 2 else  "S") + "u tarea principal es identificar la emoción del rostro (si la persona está triste o feliz),",
            u"ignorando por completo la palabra que está escrita encima. No intente leer la palabra, solo mire la cara.", 
            u"Debe responder lo más rápido posible, siguiendo su primera impresión, pero intentando no cometer errores.",
            u"No se detenga a analizar demasiado cada imagen; confíe en lo que perciba de inmediato.",
            " ",
            u"Para responder, utilizaremos únicamente su mano derecha sobre el teclado. Por favor, coloque sus dedos así:",
            " ",
            u"El dedo índice sobre la tecla [V] para indicar " + ("FELIZ" if variables["happyV"] else "TRISTE") + ".",
            u"El dedo medio sobre la tecla [N] para indicar " + ("TRISTE" if variables["happyV"] else "FELIZ") + ".",
        ],
        'word_block': [
            u"Ahora comenzaremos con el experimento.",
            " ",
            u"En esta prueba vamos a ver una serie de fotografías de rostros de personas en la pantalla.", 
            u"Notará que sobre cada rostro hay una palabra escrita en color rojo.",
            u"" + ("Esta vez s" if variables["blockNumber"] == 2 else  "S") + "u tarea principal es responder usando la emoción que aparece escrita en la palabra, ignorando por completo la emoción",
            u"que expresa el rostro (si la persona está triste o feliz). No intente descifrar la emoción en el rostro, sólo lea la palabra.", 
            u"Debe responder lo más rápido posible, siguiendo su primera impresión, pero intentando no cometer errores.",
            u"No se detenga a analizar demasiado cada imagen; confíe en lo que perciba de inmediato.",
            " ",
            u"Para responder, utilizaremos únicamente su mano derecha sobre el teclado. Por favor, coloque sus dedos así:",
            " ",
            u"El dedo índice sobre la tecla [V] para indicar " + ("FELIZ" if variables["happyV"] else "TRISTE") + ".",
            u"El dedo medio sobre la tecla [N] para indicar " + ("TRISTE" if variables["happyV"] else "FELIZ") + ".",
        ],
        'Break': [
            u"Fin del bloque " + variables["blockNumber"] + ".",
            " ",
            u"Tómate de 2 a 3 minutos para descansar.",
            " ",
            u"Cuando estés lista/o para continuar presiona la barra espaciadora."
        ],
        'farewell': [
            u"La tarea ha finalizado.",
            "",
            u"Muchas gracias por su colaboración!!"
        ]
    }

    return (basic_slides[slide_name])


# EEG Functions
def init_lpt(address):
    """Creates and tests a parallell port"""
    try:
        from ctypes import windll
        global io
        io = windll.dlportio  # requires dlportio.dll !!!
        print('Parallel port opened')
    except:
        pass
        print("Oops!", sys.exc_info(), "occurred.")
        print('The parallel port couldn\'t be opened')
    try:
        io.DlPortWritePortUchar(address, 0)
        print('Parallel port set to zero')
    except:
        pass
        print('Failed to send initial zero trigger!')


def send_trigger(trigger, address, latency):
    """Sends a trigger to the parallell port"""
    try:
        io.DlPortWritePortUchar(address, trigger)  # Send trigger
        pygame.time.delay(latency)  # Keep trigger pulse for some ms
        io.DlPortWritePortUchar(address, 0)  # Get back to zero after some ms
        print('Trigger ' + str(trigger) + ' sent')
    except:
        pass
        print('Failed to send trigger ' + str(trigger))


def init_com(address="COM3"):
    """Creates and tests a serial port"""
    global ser
    try:
        ser = serial.Serial()
        ser.port = address
        ser.baudrate = 115200
        ser.open()
        print('Serial port opened')
    except:
        pass
        print('The serial port couldn\'t be opened')


def send_triggert(trigger):
    """Sends a trigger to the serial port"""
    try:
        ser.write((trigger).to_bytes(1, 'little'))
        print('Trigger ' + str(trigger) + ' sent')
    except:
        pass
        print('Failed to send trigger ' + str(trigger))


def sleepy_trigger(trigger, latency=100):
    send_triggert(trigger)
    pygame.time.wait(latency)


def close_com():
    """Closes the serial port"""
    try:
        ser.close()
        print('Serial port closed')
    except:
        pass
        print('The serial port couldn\'t be closed')


# Text Functions
def setfonts():
    """Sets font parameters"""
    global bigchar, char, charnext
    pygame.font.init()
    font = join('media', 'Arial_Rounded_MT_Bold.ttf')
    bigchar = pygame.font.Font(script_path/font, 96)
    char = pygame.font.Font(script_path/font, 32)
    charnext = pygame.font.Font(script_path/font, 24)


def paragraph(text, key=None, no_foot=False, color=None, limit_time=0, row=None, is_clean=True):
    """Organizes a text into a paragraph"""
    if is_clean:
        screen.fill(background)

    # if text is a string, convert to list
    if isinstance(text, str):
        text = [text]

    if row == None:
        row = center[1] - 20 * len(text)

    if color == None:
        color = char_color    

    print(text) if debug_mode else None
    for line in text:
        phrase = char.render(line, True, color)
        phrasebox = phrase.get_rect(centerx=center[0], top=row)
        screen.blit(phrase, phrasebox)
        row += 40
    if key != None:
        if key == K_SPACE:
            foot = u"Para continuar presione la tecla Espacio..."
        elif key == K_RETURN:
            foot = u"Para continuar presione la tecla ENTER..."
    else:
        foot = u"Responda con la fila superior de teclas de numéricas"
    if no_foot:
        foot = ""
    nextpage = charnext.render(foot, True, charnext_color)
    nextbox = nextpage.get_rect(left=15, bottom=resolution[1] - 15)
    screen.blit(nextpage, nextbox)
    pygame.display.flip()

    if key != None or limit_time != 0:
        wait(key, limit_time)


# Program Functions
def init():
    """Init display and others"""
    setfonts()
    global screen, resolution, center, background, char_color, charnext_color, fix, fixbox
    pygame.init()  # soluciona el error de inicializacion de pygame.time
    pygame.display.init()
    pygame.display.set_caption(test_name)
    pygame.mouse.set_visible(False)
    if FullScreenShow:
        resolution = (pygame.display.Info().current_w,
                      pygame.display.Info().current_h)
        screen = pygame.display.set_mode(resolution, FULLSCREEN)
    else:
        try:
            resolution = pygame.display.list_modes()[3]
        except:
            resolution = (1280, 720)
        screen = pygame.display.set_mode(resolution)
    center = (int(resolution[0] / 2), int(resolution[1] / 2))
    background = Color('white')
    char_color = Color('black')
    charnext_color = Color('black')
    fix = char.render('+', True, char_color)
    fixbox = fix.get_rect(centerx=center[0], centery=center[1])
    screen.fill(background)
    pygame.display.flip()


def blackscreen(blacktime=0):
    """Erases the screen"""
    screen.fill(background)
    pygame.display.flip()
    pygame.time.delay(blacktime)


def ends():
    """Closes the show"""
    blackscreen()
    dot = char.render('.', True, char_color)
    dotbox = dot.get_rect(left=15, bottom=resolution[1] - 15)
    screen.blit(dot, dotbox)
    pygame.display.flip()
    while True:
        for evento in pygame.event.get():
            if evento.type == KEYUP and evento.key == K_ESCAPE:
                pygame_exit()


def pygame_exit():
    pygame.quit()
    sys.exit()


def wait(key, limit_time):
    """Hold a bit"""

    TIME_OUT_WAIT = USEREVENT + 1
    if limit_time != 0:
        pygame.time.set_timer(TIME_OUT_WAIT, limit_time, loops=1)

    tw = pygame.time.get_ticks()

    switch = True
    while switch:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                pygame_exit()
            elif event.type == KEYUP:
                if event.key == key:
                    switch = False
            elif event.type == TIME_OUT_WAIT and limit_time != 0:
                switch = False

    pygame.time.set_timer(TIME_OUT_WAIT, 0)
    pygame.event.clear()                    # CLEAR EVENTS

    return (pygame.time.get_ticks() - tw)


def image_in_center(picture, xdesv=0, ydesv=0):
    center = [int(resolution[0] / 2) + xdesv, int(resolution[1] / 2) + ydesv]
    return [x - picture.get_size()[count]/2 for count, x in enumerate(center)]


def show_image(image, scale, grayscale=False):
    screen.fill(background)
    try:
        picture = pygame.image.load(image)
    except pygame.error as e:
        print(f"Error al cargar imagen {image}: {e}") if debug_mode else None
        return
    
    image_real_size = picture.get_size()
    percentage = scale / image_real_size[0]
    picture = pygame.transform.scale(picture, [int(scale), int(image_real_size[1]*percentage)])

    # Convertir a blanco y negro si se requiere
    if grayscale:
        width, height = picture.get_size()
        for x in range(width):
            for y in range(height):
                r, g, b, a = picture.get_at((x, y))
                gray = int(0.299 * r + 0.587 * g + 0.114 * b)
                picture.set_at((x, y), (gray, gray, gray, a))

    screen.blit(picture, image_in_center(picture))
    
    pygame.display.flip()


def wait_answer(image, testing = False, VKeyboardSelection = "F", NKeyboardSelection = "T", type_of_answer = "image"):
    tw = pygame.time.get_ticks()
    done = False
    selected_answer = None
    is_correct = None

    next_image = USEREVENT + 4
    pygame.time.set_timer(next_image, 1000, loops=1)

    while not done:
        for event in pygame.event.get():

            if event.type == KEYUP and event.key == K_ESCAPE and debug_mode:
                pygame_exit()

            elif event.type == KEYUP and event.key == K_v:
                selected_answer = "Happy" if VKeyboardSelection == "F" else "Sad"
                done = True
            
            elif event.type == KEYUP and event.key == K_n:
                selected_answer = "Sad" if NKeyboardSelection == "T" else "Happy"
                done = True

            elif event.type == next_image:
                selected_answer = "Missed"
                done = True
                break

    pygame.time.set_timer(next_image, 0)
    rt = pygame.time.get_ticks() - tw

    # Se obtiene el path relativo de la imagen
    relative_path = Path(image[0]).relative_to(script_path)

    # Se divide el path relativo para obtener las carpetas que contienen la imagen
    if (len(relative_path.parts) >= 3 and not testing):
        image_type = relative_path.parts[2]
        image_text = image[1]

        if type_of_answer == "image":
            print(image_type) if debug_mode else None
            is_correct = selected_answer == image_type
        elif type_of_answer == "word":
            print(image_text) if debug_mode else None
            is_correct = selected_answer == image_text
            
        print(selected_answer) if debug_mode else None
        print(is_correct) if debug_mode else None

        #print(252 + (0 if image_type == "B" else 1)) if debug_mode else None
        # sleepy_trigger(252 + (0 if image_type == "B" else 1) , lpt_address, trigger_latency) # user answer
        
    pygame.event.clear()                    # CLEAR EVENTS
    return ({"rt": rt, "is_correct": is_correct, "selected_answer": selected_answer})

def show_images(image_list, practice=False, uid=None, dfile=None, block=None, VKeyboardSelection="F", NKeyboardSelection="T"):
    phase_change = USEREVENT + 2
    pygame.time.set_timer(phase_change, 500, loops=1)

    done = False
    count = 0

    screen.fill(background)
    pygame.display.flip()

    answers_list = []

    actual_phase = 1

    while not done:
        for event in pygame.event.get():
            if event.type == KEYUP and event.key == K_ESCAPE and debug_mode:
                pygame_exit()

            elif event.type == KEYUP and event.key == K_p and debug_mode:
                done = True

            elif event.type == phase_change:
                if actual_phase == 1:
                    screen.fill(background)
                    screen.blit(fix, fixbox)
                    pygame.display.update(fixbox)
                    pygame.display.flip()
                    sleepy_trigger(1, lpt_address, trigger_latency) # fixation
                    pygame.time.set_timer(phase_change, 1000, loops=1)
                    actual_phase = 2
                elif actual_phase == 2:
                    show_image(image_list[count][0], base_size, grayscale=True)
                    paragraph(text_convertor[image_list[count][1]], key=None, no_foot=True, color=Color('blue'), limit_time=0, row=None, is_clean=False)

                    # Se verifica tipo de cara y palabra para enviar el trigger correspondiente
                    relative_path = Path(image_list[count][0]).relative_to(script_path)
                    image_type = relative_path.parts[2]  # Obtener la carpeta que contiene la imagen
                    word_type = image_list[count][1]

                    sleepy_trigger(
                        trigger_helper[
                            f"{'happy' if image_type == 'Happy' else 'sad'}_{'happy' if word_type == 'Happy' else 'sad'}"
                        ],
                        lpt_address,
                        trigger_latency
                    )  # Exposure image trigger first

                    # sleepy_trigger(int(image_list[count].split('\\')[3].split("_")[0]), lpt_address, trigger_latency) # image ID
                    pygame.time.set_timer(phase_change, 200, loops=1)
                    actual_phase = 3
                elif actual_phase == 3:
                    answer = wait_answer(image_list[count], practice, VKeyboardSelection=VKeyboardSelection, NKeyboardSelection=NKeyboardSelection, type_of_answer = ("image" if block == 1 else "word"))
                    answers_list.append([image_list[count], answer])

                    # Lanzamiento de trigger según la respuesta
                    if answer['selected_answer'] == "Missed":
                        sleepy_trigger(trigger_helper["no_response"], lpt_address, trigger_latency)
                    elif answer['is_correct']:
                        sleepy_trigger(trigger_helper["correct_response"], lpt_address, trigger_latency)
                    else:
                        sleepy_trigger(trigger_helper["incorrect_response"], lpt_address, trigger_latency)

                    count += 1
                    if count >= len(image_list):
                        done = True
                    
                    screen.fill(background)
                    pygame.display.flip()
                    pygame.time.set_timer(phase_change, randint(1000, 1200), loops=1)
                    actual_phase = 1

    pygame.time.set_timer(phase_change, 0)

    pygame.event.clear()                    # CLEAR EVENTS

    # acá se almacenará la answers_list en el archivo dfile
    if dfile is not None:
        for answer in answers_list:
            # Unir la lista con guiones en lugar de comas
            dfile.write("%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % (uid,
                                                    (Path(answer[0][0]).relative_to(script_path)).parts[-1].split('.')[0],
                                                    block,
                                                    answer[1]['rt'],
                                                    (Path(answer[0][0]).relative_to(script_path)).parts[2],
                                                    answer[0][1],
                                                    "Cara" if block == 1 else "Palabra",
                                                    answer[1]['selected_answer'],
                                                    int(answer[1]['is_correct']) if answer[1]['is_correct'] is not None else ""
                                                 ))
            #("Sujeto", "IdImagen", "Bloque", "TReaccion", "TipoImagen", "Palabra", "TipoRespuesta", "Respuesta", "Acierto"))
        dfile.flush()
    else:
        print("Error al cargar el archivo de datos")


def fixation_image_list(fixation_time, fixation=True):

    fixation_event = USEREVENT + 3
    pygame.time.set_timer(fixation_event, fixation_time, loops=1)
    done = False

    screen.fill(background)
    pygame.display.flip()
    if fixation:
        screen.blit(fix, fixbox)
        pygame.display.update(fixbox)
    pygame.display.flip()

    tw = pygame.time.get_ticks()

    while not done:
        for event in pygame.event.get():
            if event.type == KEYUP and event.key == K_ESCAPE:
                pygame_exit()
            elif event.type == KEYUP and event.key == K_p:
                done = True

            elif event.type == fixation_event:  # and pygame.time.get_ticks() - tw >= fixation_time
                # if fixation:
                    # sleepy_trigger(244, lpt_address, trigger_latency) # fixation
                done = True
                break

    pygame.time.set_timer(fixation_event, 0)
    pygame.event.clear()                    # CLEAR EVENTS

# Main Function
def main():
    """Game's main loop"""

    init_com()

    # Si no existe la carpeta data se crea
    if not os.path.exists(script_path/'data/'):
        os.makedirs(script_path/'data/')

    # Username = id_keyboardSelection_firstBlock
    # keyboardSelection = V is F or T (feliz o triste), firstBlock = C or P (cara o palabra, que es lo que la persona debe identificar en el primer bloque)
    # example: 4321_F_C sería un usuario con id 4321 el cual al presionar la V representa Feliz, el primer bloque es Cara y el segundo es Palabra
    # example: 4321_T_P sería un usuario con id 4321 el cual al presionar la V representa Triste, el primer bloque es Palabra y el segundo es Cara

    correct_sub_name = False
    first_round = True

    while not correct_sub_name:
        os.system('cls')
        if not first_round:
            print("ID ingresado no cumple con las condiciones, contacte con el encargado...")

        first_round = False
        subj_name = input(
            "Ingrese el ID del participante y presione ENTER para iniciar: ")
        
        print(len(subj_name.split("_")))
        if not subj_name or subj_name.strip() == "" or len(subj_name.split("_")) != 3:
            continue

        uid = subj_name.split("_")[0].strip()
        VKeyboardSelection = subj_name.split("_")[1].strip()
        NKeyboardSelection = "T" if VKeyboardSelection == "F" else "F"
        firstBlock = subj_name.split("_")[2].strip()
        secondBlock = "C" if firstBlock == "P" else "P"

        print(uid) if debug_mode else None
        print(VKeyboardSelection) if debug_mode else None
        print(firstBlock) if debug_mode else None

        if VKeyboardSelection in ["F", "T"] and firstBlock in ["C", "P"]:
            correct_sub_name = True
    
    print("Tecla Feliz: " + ("V" if subj_name.split("_")[1].strip() == "F" else "N")) if debug_mode else None
    print("Tecla Triste: " + ("V" if subj_name.split("_")[1].strip() == "T" else "N")) if debug_mode else None
    print("Primer bloque: " + ("Cara" if firstBlock == "C" else "Palabra")) if debug_mode else None
    print("Segundo bloque: " + ("Palabra" if secondBlock == "P" else "Cara")) if debug_mode else None
    
    csv_name = date_name + '_' + subj_name + '.csv'
    dfile = open(script_path/"data"/csv_name, 'w')
    dfile.write("%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % ("Sujeto", "IdImagen", "Bloque", "TReaccion", "TipoImagen", "Palabra", "TipoRespuesta", "Respuesta", "Acierto"))
    dfile.flush()

    init()

    send_triggert(start_trigger)

    paragraph(select_slide('welcome'), key = K_SPACE)

    # ------------------------ first block ------------------------

    paragraph(select_slide('word_block' if firstBlock == "P" else 'face_block', variables= {"blockType": firstBlock, "happyV": True if VKeyboardSelection == "F" else False, "blockNumber": 1}), key = K_SPACE)

    sleepy_trigger(51, lpt_address, trigger_latency) # block number
    show_images(first_experiment_block, practice = False, uid=uid, dfile=dfile, block=1, VKeyboardSelection=VKeyboardSelection, NKeyboardSelection=NKeyboardSelection)
    
    paragraph(select_slide('farewell', variables={"blockNumber": 1, "practice": False, "happyV": True, "blockType": "C"}), key = K_SPACE, no_foot = True)

    # ------------------------ second block ------------------------

    paragraph(select_slide('word_block' if secondBlock == "P" else 'face_block', variables= {"blockType": secondBlock, "happyV": True if VKeyboardSelection == "F" else False, "blockNumber": 2}), key = K_SPACE, no_foot = True)

    sleepy_trigger(52, lpt_address, trigger_latency) # block number
    show_images(second_experiment_block, practice = False, uid=uid, dfile=dfile, block=2, VKeyboardSelection=VKeyboardSelection, NKeyboardSelection=NKeyboardSelection)

    paragraph(select_slide('farewell', variables={"blockNumber": 2, "practice": False, "happyV": True, "blockType": "C"}), key = K_SPACE, no_foot = True)

    paragraph(select_slide('farewell'), key = K_SPACE, no_foot = True)
    send_triggert(stop_trigger)
    dfile.close()

    close_com()
    ends()


# Experiment starts here...
if __name__ == "__main__":
    main()
