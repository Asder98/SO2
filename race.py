import threading
import random
import time
import curses

AMOUNT = 10  # ilość aut
PITSTOPSAMOUNT = 5
WIDTH = 60  # szerokość okna programu
HEIGHT = AMOUNT + 3  # wyskość okna programu
COL1 = 0  # kolumna pierwsza
COL2 = 15  # kolumna druga
COL3 = 34  # kolumna trzecia
COL4 = 50
TIMEOUT = 100  # timeout funkcji getch(). Ustala również częstotliwość odświeżania okna

class Car(threading.Thread):  # obiekt filozofa
    running = True

    def __init__(self, xid, pitstops):
        threading.Thread.__init__(self)
        self.id = xid  # id filozofa
        self.pitstops = pitstops
        self.state = "Gotów"    # "stan" filozofa, używany do celu wyświetlenia go w oknie
        self.progress = 0   # progres aktualnej czynności, używany do loading barów w oknie
        self.fuellevel = random.randint(50, 100)

    def run(self):
        while self.running:
            self.state = "Na torze"
            laptime = random.uniform(.25, .35) # ustalenie czasu myślenia(snu), czas snu będzie wynosił 10x pousetime, ze względu na konieczność zmiany warości "progress"
            for i in range(10):
                time.sleep(laptime)
                self.progress += 1
            self.progress = 0
            self.calcFuel()
            self.state = "Chce zjechać"
            self.service() # samochód chce zjechać

    def calcFuel(self):
        self.fuellevel -= random.randint(5, 10)

    def service(self):
        locked = False
        currentpitstop = None
        while self.running:
            for pitstop in pitstops:
                locked = pitstop.acquire(False)
                if locked:
                    currentpitstop = pitstop
                    break # wolny pitstop - zjedź z toru
            break
        else:
            self.state = "Zakończył wyścig"
            return

        if locked:
            self.operation()  # funkcja "jedzenia"
            currentpitstop.release()  # odłóz widelce

    def operation(self):
        self.state = "W pitstopie"
        operationtime = random.uniform(.25, .35)    # ustalanie czasu postoju. postój zajmie 10x operationtime
        for i in range(10):
            time.sleep(operationtime)
            self.progress += 1
        self.progress = 0
        if(self.running == True):
            self.state = "Wyjazd z pitstopu"
        else:
            self.state = "Zakończył wyścig"


def renderWindow(xwindow):  #   generowanie wyświetlanego okna
    xwindow.clear()
    xwindow.border(0)
    xwindow.addstr(1, COL1 + 1, "Auta:", curses.A_DIM)
    xwindow.addstr(1, COL2, "|")
    xwindow.addstr(1, COL2 + 1, "Stan: ", curses.A_DIM)
    xwindow.addstr(1, COL3, "|")
    xwindow.addstr(1, COL3 + 1, "Progress: ", curses.A_DIM)
    xwindow.addstr(1, COL4, "|")
    xwindow.addstr(1, COL4 + 1, "Paliwo: ", curses.A_DIM)

    for i in range(AMOUNT):
        xwindow.addstr(i + 2, COL2, "|")
        xwindow.addstr(i + 2, COL3, "|")
        xwindow.addstr(i + 2, COL4, "|")
        xwindow.addstr(i + 2, COL1 + 1, "Pojazd " + str(i))
        state = cars[i].state
        xwindow.addstr(i + 2, COL2 + 1, str(state))
        xwindow.addstr(i + 2, COL3 + 1, " [")
        xwindow.addstr(i + 2, COL4 - 3, "] ")
        progress = cars[i].progress
        for j in range(progress):
            xwindow.addstr(i + 2, COL3 + 3 + j, "#")
        fuel = cars[i].fuellevel
        xwindow.addstr(i + 2, COL4 + 1, str(fuel))



if __name__ == '__main__':
    curses.initscr()
    window = curses.newwin(HEIGHT, WIDTH, 0, 0)
    window.timeout(TIMEOUT)
    window.keypad(1)
    curses.noecho()
    curses.curs_set(0)
    window.border(0)

    pitstops = [threading.Lock() for n in range(PITSTOPSAMOUNT)]

    cars = [Car(i, pitstops)  # tworzenie filozofów
            for i in range(AMOUNT)]

    random.seed(507129)
    # Philosopher.running = True
    for p in cars:  #rozpoczęcie uczty
        p.running = True
        p.start()
    event = -1
    while True: # ucznta
        renderWindow(window)
        window.addstr(HEIGHT - 1, COL2, "Kliknij ESC, aby zakończyć")
        event = window.getch()

        if event == 27: # klawisz ESC - zakończenie wyścigu
            event = -1
            for p in cars: # zakończenie jazdy poszczególnych samochodów
                p.running = False
            pitstopsfree = False
            while not pitstopsfree:    # oczekiwanie, aż zakończą wyścig
                pitstopsfree = True
                renderWindow(window)
                event = window.getch()
                for f in pitstops:
                    if f.locked():
                        pitstopsfree = False

            break   # zakończenie wyścigu

    curses.nocbreak()
    curses.echo()

    curses.endwin()
