import threading

import cv2
import time
import keyboard as K
from pynput.keyboard import Key, Controller
import numpy as np
from PIL import ImageGrab


pociski = []

class Gracz:
    def __init__(self, x):
        self.x1 = x
        self.x2 = x + 90


class Pole:
    def __init__(self, x1, x2):
        self.x1 = x1
        self.x2 = x2

    def __str__(self):
        return f"{self.x1} od {self.x2}"

    def czy_pasuje(self,gracz):
        return abs(self.x1 - self.x2) > abs(gracz.x1 - gracz.x2) + 12

    def odleglosc(self,gracz):
        if self.x1 < gracz.x1 and self.x2 > gracz.x2:
            return 0
        srodekpola = (self.x1 + self.x2)/2
        srodekgracza = (gracz.x1 + gracz.x2)/2
        dif = srodekpola - srodekgracza
        return dif

    def odleglosc_od_boku(self,gracz):
        if self.x1 < gracz.x1 and self.x2 > gracz.x2:
            return 0
        elif self.x2 < gracz.x1:
            return gracz.x1 - self.x2
        return self.x1 - gracz.x2

class Pocisk:
    def __init__(self, sx, sy, i):
        self.sx = sx
        self.sy = sy
        self.x1 = sx - 10
        self.x2 = sx + 10
        self.i = i

    def __lt__(self, other):
        return self.sx < other.sx

class Przeciwnik:
    def __init__(self, sx, sy):
        self.sx = sx
        self.sy = sy


def find_best_space(lista_pol, gracz):
    minimum = 2000
    najlepsze_pole = None
    for p in lista_pol:
        if p.czy_pasuje(gracz):
            if p.odleglosc_od_boku(gracz) < minimum:
                minimum = p.odleglosc_od_boku(gracz)
                najlepsze_pole = p
    if najlepsze_pole:
        return (abs(najlepsze_pole.odleglosc(gracz)),najlepsze_pole.odleglosc(gracz),najlepsze_pole)
    return None

def generate_spaces(lista_pociskow):
    pola = []
    for i,p in enumerate(lista_pociskow):
        if i == 0:
            pola.append(Pole(6,p.x1))
        else:
            pola.append(Pole(lista_pociskow[i-1].x2,p.x1))
            if i == len(lista_pociskow) - 1:
                pola.append(Pole(p.x2,1430))
    return pola

def get_screen(index):
    printscreen_pil = ImageGrab.grab(bbox=[13, 170, 1450, 975])
    printscreen_numpy = np.array(printscreen_pil.getdata(), dtype=
    'uint8').reshape((printscreen_pil.size[1], printscreen_pil.size[0], 3))
    gray = cv2.cvtColor(printscreen_numpy, cv2.COLOR_BGR2GRAY)
    Blur = cv2.GaussianBlur(gray, (5, 5), 1)
    Canny = cv2.Canny(Blur, 10, 50)
    contours = cv2.findContours(Canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
    cntrRect = []
    przeciwnicy = []

    for i in contours:
        epsilon = 0.05 * cv2.arcLength(i, True)
        approx = cv2.approxPolyDP(i, epsilon, True)
        if len(approx) == 4:
            #cv2.drawContours(printscreen_numpy, cntrRect, -1, (0, 255, 0), 2)

            xdif = abs(approx[0][0][0] - approx[-1][0][0])
            ydif = abs(approx[0][0][1] - approx[-1][0][1])

            sumax = 0
            sumay = 0
            ignoruj = False
            for j in approx:
                if (j[0][0] < 100 and j[0][1] < 50) or (j[0][1] > 780):
                    ignoruj = True
                    break
                sumax += j[0][0]
                sumay += j[0][1]
            if ignoruj:
                continue

            sredniax = int(sumax / 4)
            sredniay = int(sumay / 4)

            if 30 > xdif > 5:
                czy_istnieje = False
                for p in pociski:
                    if sredniax + 5 > p.sx > sredniax - 5:
                        czy_istnieje = True
                        break
                if not czy_istnieje:
                    pociski.append(Pocisk(sredniax, sredniay, index))
                cv2.line(printscreen_numpy, (sredniax, sredniay), (sredniax, 804), color=(255, 255, 255), thickness=1)
            elif 30 < xdif:
                przeciwnicy.append(Przeciwnik(sredniax, sredniay))
                cv2.line(printscreen_numpy, (sredniax, sredniay), (sredniax, 804), color=(255, 0, 255), thickness=1)

            cntrRect.append(approx)

    for ind,x in enumerate(pociski):
        if x.i <= index - 3:
            pociski.pop(ind)

    pola = generate_spaces(sorted(pociski))

    for p in pola:
        x1 = (p.x1, 800)
        x2 = (p.x2, 800)
        cv2.circle(printscreen_numpy, x1, color=(255, 0, 255), thickness=-1, radius=5)
        cv2.circle(printscreen_numpy, x2, color=(255, 0, 255), thickness=-1, radius=5)

    gracz_punkty = []
    wykryto_gracza = False

    for i, x in enumerate(printscreen_numpy[790]):
        if x[0] == 255:
            gracz_punkty.append(i)

    if len(gracz_punkty):
        wykryto_gracza = True
        gracz = Gracz(int(np.median(gracz_punkty))-48)
        cv2.circle(printscreen_numpy, (gracz.x1,785), color=(0, 0, 255), thickness=-1, radius=5)
        cv2.circle(printscreen_numpy, (gracz.x2,785), color=(0, 0, 255), thickness=-1, radius=5)
        to_move = find_best_space(pola, gracz)
        if to_move is None:
            return wykryto_gracza
        hmmm = to_move
        #for x in to_move:
        cv2.line(printscreen_numpy, (hmmm[2].x1, 790), (hmmm[2].x2, 790), color=(255, 0, 0), thickness=1)
        if hmmm[0]<500:
            move_to(hmmm[1])
    #printscreen_pil.save(f"x{index}.png")
    cv2.imwrite(f'g{index}.png', printscreen_numpy)
    return wykryto_gracza

def move_to(pixels):
    kb = Controller()
    def foo(key,t):
        time.sleep(t)
        kb.release(key)
    if pixels < 0:
        k = Key.left
        kb.release(Key.right)
    else:
        k = Key.right
        kb.release(Key.left)
    kb.press(k)
    t = threading.Thread(target=foo,args=(k,(abs(pixels) * 0.5 / 1000)))
    t.start()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    i = 0
    time.sleep(5)
    while True:
        if K.is_pressed('q'):  # if key 'q' is pressed
            print('You Pressed A Key!')
            break
        start_time = time.time()
        if get_screen(i):
            print(f"gracz znalezion {i}")
        stop_time = time.time()
        print(stop_time - start_time)
        i+=1

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
