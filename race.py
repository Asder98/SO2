import threading
import random
import time
import curses

AMOUNT = 15  # ilość aut
PITSTOPSAMOUNT = 2
LAPS = 15
WIDTH = 72  # szerokość okna programu
HEIGHT = AMOUNT + 3  # wyskość okna programu
COL1 = 0  # kolumna pierwsza
COL2 = 15  # kolumna druga
COL3 = 34  # kolumna trzecia
COL4 = 50
COL5 = 60
TIMEOUT = 100  # timeout funkcji getch(). Ustala również częstotliwość odświeżania okna


class Car(threading.Thread):  # obiekt filozofa
    running = True

    def __init__(self, xid, pitstops, lapstogo):
        threading.Thread.__init__(self)
        self.id = xid  # id filozofa
        self.pitstops = pitstops
        self.state = "Gotów"  # "stan" filozofa, używany do celu wyświetlenia go w oknie
        self.progress = 0  # progres aktualnej czynności, używany do loading barów w oknie
        self.fuellevel = random.randint(50, 100)
        self.laps = 0
        self.lapstogo = lapstogo

    def run(self):
        while self.running:
            self.state = "Na torze"
            laptime = random.uniform(.15, .20)  # ustalenie czasu okrążenia
            for i in range(10):
                time.sleep(laptime)
                self.progress += 1
            self.progress = 0
            self.calcFuel()
            if self.fuellevel <= 0:
                self.state = "Zabrakło paliwa"
                self.running = False
            else:
                self.laps += 1
                if self.laps == self.lapstogo:
                    self.state = "Meta"
                    self.running = False
                elif self.fuellevel <= 30:
                    self.state = "Chce zjechać"
                    self.service()

    def calcFuel(self):
        self.fuellevel -= random.randint(8, 15)

    def service(self):
        locked = False
        currentpitstop = None
        while self.running:
            for pitstop in pitstops:
                locked = pitstop.acquire(False)
                if locked:
                    currentpitstop = pitstop
                    break  # wolny pitstop - zjedź z toru
            break
        else:
            self.state = "Zakończył wyścig"
            return

        if locked:
            self.operation()  # funkcja "jedzenia"
            currentpitstop.release()  # odłóz widelce

    def operation(self):
        self.state = "W pitstopie"
        operationtime = random.uniform(.08, .10)  # ustalanie czasu postoju. postój zajmie 10x operationtime
        for i in range(10):
            time.sleep(operationtime)
            self.progress += 1
        self.fuellevel = random.randint(70, 100)
        self.progress = 0
        if self.running:
            self.state = "Wyjazd z pitstopu"
        else:
            self.state = "Zakończył wyścig"


def renderWindow(xwindow):  # generowanie wyświetlanego okna
    xwindow.clear()
    xwindow.border(0)
    xwindow.addstr(1, COL1 + 1, "Auta:", curses.A_DIM)
    xwindow.addstr(1, COL2, "|")
    xwindow.addstr(1, COL2 + 1, "Stan: ", curses.A_DIM)
    xwindow.addstr(1, COL3, "|")
    xwindow.addstr(1, COL3 + 1, "Progress: ", curses.A_DIM)
    xwindow.addstr(1, COL4, "|")
    xwindow.addstr(1, COL4 + 1, "Paliwo: ", curses.A_DIM)
    xwindow.addstr(1, COL5, "|")
    xwindow.addstr(1, COL5 + 1, "Okrążenie: ", curses.A_DIM)

    for i in range(AMOUNT):
        xwindow.addstr(i + 2, COL2, "|")
        xwindow.addstr(i + 2, COL3, "|")
        xwindow.addstr(i + 2, COL4, "|")
        xwindow.addstr(i + 2, COL5, "|")
        xwindow.addstr(i + 2, COL1 + 1, "Pojazd " + str(i))
        state = cars[i].state

        if state == "Na torze":
            color = 35  # 35
        elif state == "W pitstopie":
            color = 40
        elif state == "Zabrakło paliwa":
            color = 161
        else:
            color = 1  # 1

        xwindow.addstr(i + 2, COL2 + 1, str(state), curses.color_pair(color))
        xwindow.addstr(i + 2, COL3 + 1, " [")
        xwindow.addstr(i + 2, COL4 - 3, "] ")
        progress = cars[i].progress
        for j in range(progress):
            xwindow.addstr(i + 2, COL3 + 3 + j, "#", curses.color_pair(color))
        fuel = cars[i].fuellevel

        if fuel > 50:
            color = 35  # 35
        elif 30 <= fuel <= 50:
            color = 167
        elif 1 <= fuel <= 29:
            color = 161
        elif fuel <= 0:
            color = 9
        else:
            color = 1  # 1

        xwindow.addstr(i + 2, COL4 + 1, str(fuel), curses.color_pair(color))
        laps = cars[i].laps
        xwindow.addstr(i + 2, COL5 + 1, str(laps))


if __name__ == '__main__':
    curses.initscr()
    window = curses.newwin(HEIGHT, WIDTH, 0, 0)
    window.timeout(TIMEOUT)
    window.keypad(1)
    curses.noecho()
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    for i in range(1, curses.COLORS + 1):
        curses.init_pair(i, i - 1, -1)
    window.border(0)

    pitstops = [threading.Lock() for n in range(PITSTOPSAMOUNT)]

    cars = [Car(i, pitstops, LAPS)  # tworzenie filozofów
            for i in range(AMOUNT)]

    scoreboard = []

    random.seed(507129)
    # Car.running = True
    for car in cars:  # rozpoczęcie uczty
        car.running = True
        car.start()
    event = -1
    while True:  # wyścig
        renderWindow(window)
        window.addstr(HEIGHT - 1, COL2, "Kliknij ESC, aby zakończyć")
        event = window.getch()

        if event == 27:  # klawisz ESC - zakończenie wyścigu
            event = -1
            for p in cars:  # zakończenie jazdy poszczególnych samochodów
                p.running = False
            pitstopsfree = False
            while not pitstopsfree:  # oczekiwanie, aż zakończą wyścig
                pitstopsfree = True
                renderWindow(window)
                event = window.getch()
                for f in pitstops:
                    if f.locked():
                        pitstopsfree = False

            break  # zakończenie wyścigu

    curses.nocbreak()
    curses.echo()

    curses.endwin()
