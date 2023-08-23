import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pynput import keyboard
import time
import sys
from tkinter import simpledialog
from tkinter import messagebox

from constants import *
from utils import *
from strongholds import Strongholds
import random

"""
THINGS TO SET BACK TO NORMAL AFTER TESTING
next button disabled
qs file reading
first 8 strongholds list
delete print statements
2 read path qs file tests

THINGS TO FIX
make pathfind from coords work
subprocess.run for running concord and adding concord to exe (dank)
comment code :D
fix readme
redo pathfinding at last 8th ring sh if no empty sector yet
fix graph for repathfind (impossible)
fix different monitory res (test)
fix x on qs file messageboxes
place/grid in silly
do colours in unscuffed way
"""

class AllPortals:
    def __init__(self):
        self.strongholds = Strongholds()

        self.next_stronghold_hotkey = ""
        self.purple = False #true if the last stronghold is where your spawn should be
        self.done = False #true if you are done filling portals
        self.pathfind_pressed = False

    def start(self):
        """actually start the window and program"""
        self.update_count()
        self.create_image()
        self.build_window()
        self.create_inital_widgets()
        self.root.mainloop()

    def build_window(self):
        """creates the base starting window for the program"""
        self.root = tk.Tk()
        self.root.config(bg=peach)
        self.root.title("Find Portals")
        self.root.wm_attributes("-topmost", 0) #changes to 1 when the 'always on top' box is checked
        self.root.protocol("WM_DELETE_WINDOW", lambda: [print('destroy me...'), sys.exit(0)]) #for some reason the program doesnt stop when you close tkinter unless u have this thing

    def create_image(self):
        """create the image showing portals path and completed portals"""
        img = plt.imread("rings.png")
        plt.imshow(img, aspect="equal", extent=[-24320, 24320, -24320, 24320])
        plt.axis("off")

    def update_count(self):
        """tell the program and user how many portals are filled"""
        if (
            self.strongholds.get_completed_count() > 0
            and self.strongholds.get_completed_count()
            == self.strongholds.get_empty_sh_index()
        ):
            return

        with open("sh_count.txt", "w+") as count_file:
            count_file.write(str(self.strongholds.get_completed_count()) + "/128\n")

        with open("fun_facts.txt", "w+") as facts_file:
            if self.strongholds.get_completed_count() == 69:
                facts_file.writelines(["nice.\n"])
            if self.strongholds.get_completed_count() == 71:
                facts_file.writelines(["BRA7-1L\n"])
            if self.strongholds.get_completed_count() == 128:
                facts_file.writelines(["DONE!\n"])
            if is_prime(self.strongholds.get_completed_count()):
                facts_file.writelines(["(prime)\n"])

    def complete_sh(self, sh, empty=False):
        """add stronghold to completed shs array and update count"""
        self.strongholds.complete_sh(sh, empty)
        self.update_count()

    def lock_entry(
        self, ring: int, entry: object, button: object, next_button: object
    ) -> None:
        """when user presses lock, check if coords are in correct ring and in the right format, add them to first strongholds array"""
        try:
            sh = tuple(parse_input(entry.get()))
            if len(sh) != 2:
                raise Exception
        except Exception as e:
            print(e)
            tk.messagebox.showerror(
                message="Something went wrong. Make sure you only input your x and z coordinate separated by a space, or copy paste the f3+c command"
            )
            return

        if get_stronghold_ring(sh) == 0:
            if not tk.messagebox.askyesno(
                message="Are you sure this is in the right ring? This stronghold does not appear to be in any ring."
                + "\nThis is possible to occur with biome snapping, but quite rare. If you are sure then click 'yes', otherwise hit 'no' and enter coords again"
            ):
                return
        elif ring != get_stronghold_ring(sh):
            if not tk.messagebox.askyesno(
                message="Are you sure this is in the right ring? Looks like this is a stronghold in ring "
                + str(get_stronghold_ring(sh))
                + ".\nIf you are completely sure this is in the right ring and my program is stupid then click 'yes', otherwise hit 'no' and enter coords again"
            ):
                return

        self.complete_sh(sh)
        self.strongholds.set_current_location(sh)
        self.update_image()
        plt.draw()
        # plt.savefig("output.png", bbox_inches="tight", transparent=True)

        entry.config(state="disabled", cursor="heart") # <3
        button.config(state="disabled", cursor="heart")


        if self.strongholds.get_completed_count() == 8:
            next_button.config(state="normal") # allow user to press next

    def check_next(self, next_button):
        """checks each sh location is locked before changing window setup and predicts other sh locations"""

        next_button.config(
            state="disabled"
        )  # very silly things happen if you press the next button twice...

        backup_strongholds(self.strongholds.completed)

        self.strongholds.estimate_sh_locations()

        write_nodes_qs_file(
            self.strongholds.get_last_sh_coords(), self.strongholds.estimations
        )

        path = read_path_qs_file()

        if path=="stop":
            next_button.config(
                state="normal"
            )
            self.strongholds.estimations=[]
            return

        self.strongholds.sort_estimations_order_by_path(path)

        # get rid of all widgets from the first-strongholds part
        for lock in self.locks:
            lock.destroy()
        for sh in self.sh_labels:
            sh.destroy()
        for entry in self.entries:
            entry.destroy()
        self.lock_order_label.destroy()

        print(
            *zip(
                *(
                    tuple(round(coord / 16) for coord in sh)
                    for sh in self.strongholds.estimations
                )
            )
        )
        plt.scatter(
            *zip(*self.strongholds.estimations),
            c="gray",
            s=20,
        ) # puts fun little dots on the graph
        plt.draw()

        self.setspawn_button.destroy()
        self.setup_next()
        next_button.destroy()
        self.display_next_sh()
        self.update_image()

    def create_inital_widgets(self):
        """create the window for entering your first 8 sh locations"""
        # toggles window always on top or not
        self.toggle_frame = tk.Frame(self.root, width=150, height=20, bg=peach)
        self.toggle_frame.grid(row=1, column=6, rowspan=2)
        always_on_top = tk.IntVar(self.root)
        self.topmost_toggle = tk.Checkbutton(
            self.toggle_frame,
            bg=peach,
            activebackground=peach,
            text="Always On Top",
            variable=always_on_top,
            onvalue=1,
            offvalue=0,
            command=lambda: self.root.wm_attributes("-topmost", always_on_top.get()),
        )
        #self.topmost_toggle.place(relx=0.5, rely=0.5, anchor="center")
        self.topmost_toggle.pack(anchor="center")

        # labels for the entry boxes and locks to save each coord into a list of first strongholds
        self.sh_labels = [
            tk.Label(self.root, bg=peach, text=f"sh {i}:") for i in range(1, 9)
        ]
        [self.sh_labels[i].grid(row=i, column=1) for i in range(0, 8)]

        self.entries = [
            tk.Entry(
                self.root,
                width=40,
                borderwidth=5,
                bg=lightpeach,
            )
            for i in range(0, 8)
        ]
        [self.entries[i].grid(row=i, column=2, columnspan=3) for i in range(0, 8)]

        # goes to next stage, only works once all 8 locations have been locked
        # IF TESTING U CAN SET THE STATE TO "normal" SO U CAN EASILY USE THE TEST SH LOCATIONS IN STRONGHOLDS.PY
        next_button = tk.Button(
            self.root,
            state="normal",
            text="next",
            command=lambda: self.check_next(next_button),
            bg=darkpeach,
            activebackground=lightpeach,
        )

        self.setspawn_button = tk.Button(
            self.root,
            text="Give Spawnpoint",
            command=self.set_spawn,
            bg=darkpeach,
            activebackground=lightpeach,
        )

        self.locks = [
            tk.Button(
                self.root,
                text="lock",
                borderwidth=3,
                bg=darkpeach,
                activebackground=lightpeach,
            )
            for i in range(0, 8)
        ]
        for i in range(0, 8):
            self.locks[i].config(
                command=lambda i=i: self.lock_entry(
                    i + 1, self.entries[i], self.locks[i], next_button
                )
            )
        [self.locks[i].grid(row=i, column=5) for i in range(0, 8)]

        # label telling user to lock in order so that the image updates accurately
        self.lock_order_label = tk.Label(
            self.root,
            text="Please make sure you\nlock strongholds in the\norder you found them",
            bg=peach,
        )
        self.lock_order_label.grid(row=3, column=6, rowspan=3)

        self.setspawn_button.grid(row=7, column=6)
        next_button.grid(row=9, column=6)

    def setup_next(self):
        """changes entire window setup to just display sh coords and some options"""
        self.c2 = False
        self.noGraph = False # i still have no idea what either of these do

        self.root.config(bg=lightblue)
        self.toggle_frame.config(height=70, width=200, bg="green")
        self.topmost_toggle.config(bg=lightblue, activebackground=pressblue)

        # puts some nice lil frames in the gui and then the buttons go in the frames and its 10000x easier to have everything where you want it to go
        self.sh_frame = tk.Frame(self.root, height=70, width=280, bg="pink")
        self.bt_frame = tk.Frame(self.root, height=40, width=280, bg="purple")
        self.new_buttons_frame = tk.Frame(self.root, height=120, width=200, bg="blue")
        self.inst_frame = tk.Frame(self.root, height=70, width=280, bg="red")

        #frames inside frame for next/empty buttons
        self.newnext_button_frame = tk.Frame(self.bt_frame, height=40, width=140, bg="yellow")
        self.empty_button_frame = tk.Frame(self.bt_frame, height=40, width=140, bg="orange")
        #put button frames into bt_frame
        self.newnext_button_frame.grid(row=1, column=1)
        self.empty_button_frame.grid(row=1, column=2)

        #make sure frames dont shrink to fit widget sizes
        self.toggle_frame.pack_propagate("false")
        self.sh_frame.pack_propagate("false")
        self.inst_frame.pack_propagate("false")
        self.newnext_button_frame.pack_propagate("false")
        self.empty_button_frame.pack_propagate("false")
        #grid propogate cause the stuff in them uses grid not pack
        self.bt_frame.grid_propagate("false")
        self.new_buttons_frame.grid_propagate("false")

        #labels for sh location and when to set spawn/not set spawn/find empty sector
        self.sh_label = tk.Label(self.sh_frame, text="", bg=lightblue)
        self.inst_label = tk.Label(self.inst_frame, text="", bg=lightblue)

        #buttons that go in bt_frame
        #next button to display next sh
        self.newnext_button = tk.Button(
            self.newnext_button_frame,
            text="next",
            command=self.next_sh,
            height=1,
            width=5,
            borderwidth=3,
            bg=buttonblue,
            activebackground=pressblue,
        )
        #press when found empty sector
        self.empty_button = tk.Button(
            self.empty_button_frame,
            text="empty",
            command=self.empty,
            height=1,
            width=5,
            borderwidth=3,
            bg=buttonblue,
            activebackground=pressblue,
        )

        #buttons that go in new_buttons_frame
        #set hotkey that displays next sh
        self.set_hotkey_button = tk.Button(
            self.new_buttons_frame,
            text="Next SH Hotkey",
            command=self.set_next_hotkey,
            borderwidth=3,
            bg=buttonblue,
            activebackground=pressblue,
        )
        #button for repathfinding probably shouldve found a better name than 'got lost' oh well
        self.got_lost = tk.Button(
            self.new_buttons_frame,
            text="Pathfind from coords",
            command=self.find_from_coords,
            borderwidth=3,
            bg=buttonblue,
            activebackground=pressblue,
        )
        #give program your spawnpoint for more accurate optimizations
        self.setspawn_button = tk.Button(
            self.new_buttons_frame,
            text="Give Spawnpoint",
            command=self.set_spawn,
            borderwidth=3,
            bg=buttonblue,
            activebackground=pressblue
        )
        if self.strongholds.spawn != (0, 0):
            self.setspawn_button.config(text=f"Spawnpoint: {self.strongholds.spawn}")

        #put the stuff into the frames
        self.sh_label.pack(fill="both")
        self.inst_label.pack(fill="both")
        self.set_hotkey_button.grid(row=1)
        self.setspawn_button.grid(row=2)
        self.got_lost.grid(row=3)
        self.newnext_button.pack()
        self.empty_button.pack()

        #place all the frames
        self.toggle_frame.grid(row=1, column=2, rowspan=1)
        self.sh_frame.grid(row=1, column=1)
        self.bt_frame.grid(row=2, column=1)
        self.inst_frame.grid(row=3, column=1)
        self.new_buttons_frame.grid(row=2, rowspan=2, column=2)

        # make a new tkinter window for the graph, has to be toplevel not a whole new tkinter thingy cause it cant multithread or something
        image=tk.Toplevel()
        image.title("Portals Graph")
        image.config(bg=lightblue)
        
        #make sure user can't accidentally close the image window cause there's no way to get it back
        #pressing q will close the window though for some reason i give up trying to fix
        def on_closing(): messagebox.showinfo("no", "You must close the main program to close this window.")
        image.protocol("WM_DELETE_WINDOW", on_closing)

        #using meaningful and descriptive variable names is a fundamental aspect of writing clean, maintainable, and understandable code. It's a practice that not only benefits you but also anyone who interacts with your code, now or in the future.
        aasdfae = plt.gcf()
        aasdfae.set_facecolor(lightblue)
        thang = FigureCanvasTkAgg(figure=aasdfae, master=image)
        thang.draw()
        thang.get_tk_widget().pack()

    def set_spawn(self):
        spawn = self.strongholds.set_spawn()
        self.setspawn_button.config(text=f"Spawnpoint: {spawn}")

    def update_image(self, empty: bool = False):
        """add stronghold to graph with the right colours"""
        # graph path from last stronghold as green
        color = "green"
        try:
            last_path = self.strongholds.get_last_path()
            print(last_path)
            match last_path:
                case 0:
                    color = "green"
                case 1:
                    color = "green"
                case 2:
                    color = "yellow"

            if self.strongholds.get_leave_spawn(-1):
                color = "purple"
        except IndexError:
            pass

        if self.strongholds.get_current_location() == self.strongholds.spawn:
            color = "yellow"

        self.graph_point(self.strongholds.get_last_sh_coords(), color)

        if self.strongholds.get_current_location() == self.strongholds.spawn:
            self.graph_line(
                self.strongholds.get_last_sh_coords(-2),
                self.strongholds.get_last_location(),
                "green",
            )
        else:
            self.graph_line(
                self.strongholds.get_current_location(),
                self.strongholds.get_last_location(),
                "green",
            )

        color = "blue"

        try:
            if self.strongholds.get_leave_spawn():
                color = "purple"
            else:
                color = "blue"
        except IndexError:
            pass

        # graph path to next stronghold as blue
        try:
            self.graph_point(self.strongholds.get_next_sh_coords(), color)
            self.graph_line(
                self.strongholds.get_current_location(),
                self.strongholds.get_next_sh_coords(),
                "blue",
            )
        except IndexError as e:
            pass
        plt.draw()

    def graph_point(self, coords, color):
        plt.scatter(coords[0], coords[1], c=color, s=30)
        plt.draw()

    def graph_line(self, start, end, color):
        plt.arrow(
            start[0],
            start[1],
            (end[0] - start[0]),
            (end[1] - start[1]),
            color=color,
            width=0.0001,
            head_width=0,
            head_length=0,
            length_includes_head=True,
        )
        plt.draw()

    def create_empty_widgets(self):
        """new options for when next stronghold is in 8th ring"""

        #dont show options if its not an 8th ring sh cause for some reason this function is called on every stronghold wow i coded this badly
        if get_stronghold_ring(self.strongholds.get_next_sh_coords()) != 8:
            return
    
        #means empty sector has already been found and returns before showing the empty sh options
        if self.strongholds.get_empty_sh_index() != 0:
            print("eighth ring stronghold\n")
            return
        
        self.empty_button.config(state="normal") # allow user to select empty sector, only shows up if they havent found it yet

        self.strongholds.add_completed_8th_ring() #increments even when its empty, not sure if it causes a bug tho
        print(self.strongholds.get_completed_in_ring(8))

        if (
            self.strongholds.get_completed_in_ring(8) >= 9
            and self.strongholds.get_empty_sh_index() == 0
        ):
            print("skipping last 8th ring sh")
            self.skip_empty()  # dont make user check last 8th ring sh when you already know its empty
            return


        print("prompting empty check")
        self.inst_label.config(
            text="8th ring, there could be\nno stronghold",
            bg=lightblue,
        )

    def show_spawn(self):
        """edits gui to tell user when to set spawn/not set spawn"""
        #i know this code could be way more optimized leave me alone

        if self.strongholds.get_leave_spawn():
            self.inst_label.config(
                text="LEAVE YOUR SPAWN AT THE NEXT STRONGHOLD.\nDO NOT BREAK BED AFTER FILLING PORTAL.",
                bg=spawnpurple,
            )
        elif self.strongholds.get_dont_set_spawn_colours() or self.purple: #you should never set spawn after purple gui, but get_dont_set_spawn doesnt know that
            self.inst_label.config(
                text="DO NOT SET YOUR SPAWN\nAT THE NEXT STRONGHOLD",
                bg=spawngreen,
            )
            self.purple = False


    def set_bg_colours(self):
        """colour codes the spawn point things so people dont forget surely they wont forget right suuuuurely"""
        if self.strongholds.get_leave_spawn():
            try:
                self.inst_label.config(text="")
            except:
                pass
            frame = spawnpurple
            press = presspurple
            button = buttonpurple
            self.purple = True
        elif self.strongholds.get_dont_set_spawn_colours() or self.purple:
            try:
                self.inst_label.config(text="")
            except:
                pass
            frame = spawngreen
            press = pressgreen
            button = buttongreen
        else:
            frame = lightblue
            press = pressblue
            button = buttonblue
        
        #bg=colour
        self.root.config(bg=frame)
        self.bt_frame.config(bg=frame)
        self.toggle_frame.config(bg=frame)
        self.sh_frame.config(bg=frame)
        self.new_buttons_frame.config(bg=frame)
        self.topmost_toggle.config(bg=frame, activebackground=press)
        self.newnext_button.config(bg=button, activebackground=press)
        self.set_hotkey_button.config(bg=button, activebackground=press)
        self.got_lost.config(bg=button, activebackground=press)
        self.sh_label.config(bg=frame)
        self.setspawn_button.config(bg=button, activebackground=press)
        self.inst_frame.config(bg=frame)
        self.inst_label.config(bg=frame)
        self.empty_button.config(bg=button, activebackground=press)
        self.newnext_button_frame.config(bg=frame)
        self.empty_button_frame.config(bg=frame)


    def display_next_sh(self):
        """edit gui to show new coords and angle"""
        sh_data = self.strongholds.get_next_sh()
        print(
            "Stronghold {0}:\n{1} at angle {2}".format(
                sh_data[0], sh_data[1], sh_data[3]
            )
        )  # print in case user needs to see previous locations
        self.sh_label.config(
            text="Stronghold {0}:\n{1} at angle {2}".format(
                sh_data[0], sh_data[1], sh_data[3]
            ),
            font=("Cambria", 14),
        )
        print("NEXT SH DISPLAYED")

    def next_sh(self, last_empty: bool = False):
        """completes the last stronghold and finds coords of next one and checks all the 8th ring stuff and optimizations and if its the last sh and whatever, last_empty is true if it is the empty sector"""
        print("PRESSED NEXT SH")
        self.inst_label.config(text="")
        self.empty_button.config(state="disabled")

        """ stuff for 8th ring optimization
        if self.strongholds.completed_8th_ring == 10 and not self.strongholds.empty_index:
            self.strongholds.empty_index == 1
            self.complete_sh()
        """
        # very important, fix place/grid stuff later
        if self.done:
            try:
                self.sh_label.config(text=silly_list[self.silly_count])
                self.silly_count += 1
            except IndexError:
                self.new_buttons_frame.destroy()
                self.toggle_frame.destroy()
                self.sh_frame.destroy()
                self.inst_frame.destroy()
                self.bt_frame.place(x=0, y=0, anchor="nw")
                self.bt_frame.config(height=110, width=280)
                self.bt_frame.lift()
                self.newnext_button.config(command=self.movebutton)
                pass

        elif self.strongholds.get_finished(): # means the user is done filling portals and gives the graph a pretty little star :D
            try:
                if (
                    self.strongholds.estimations.index(
                        self.strongholds.get_next_sh_coords()
                    )
                    != self.strongholds.get_completed_count()
                    + len(self.strongholds.estimations)
                    - 129
                ):
                    print("done!")
                    return
                self.complete_sh(self.strongholds.get_next_sh_coords(), last_empty)
                self.strongholds.set_current_location(
                    self.strongholds.get_last_sh_coords()
                )
                plt.scatter(
                    self.strongholds.get_last_sh_coords()[0],
                    self.strongholds.get_last_sh_coords()[1],
                    c="green",
                    s=200,
                    marker="*",
                )
                self.graph_line(
                    self.strongholds.get_current_location(),
                    self.strongholds.get_last_location(),
                    "green",
                )
                plt.draw()
            except IndexError:
                pass
            print("done!")
            self.done = True
            self.silly_count = 0

        else:
            print(f"COMPLETED SH {self.strongholds.get_next_sh_coords()}")
            self.complete_sh(self.strongholds.get_next_sh_coords(), last_empty) # puts empty sector into empty_index in completed array if last_empty==true
            self.create_empty_widgets()
            try:
                self.optimize_next_3_nodes()
            except IndexError:
                pass #has to be try/except cause this thing gives an error in the gui colour updates idk why man but then if u dont pass the error it makes the second last line blue in the graph
            self.update_image(last_empty)
            try:
                print("leave your spawn behind?", self.strongholds.get_leave_spawn()) # mostly correct but says true when on the sh before last 8th ring when its an empty sector cause at this point it still thinks ur going there
                print(
                    "don't set your spawn at all?", self.strongholds.get_dont_set_spawn() #this is always false here for some reason but its correct in optimize_next_3_nodes
                )
            except IndexError:
                pass
            self.display_next_sh()

    def optimize_next_3_nodes(self):
        """sets your current location at your current location, which is complicated when you spawn at previous shs or 0 0"""
        self.strongholds.set_current_location(self.strongholds.get_last_sh_coords())
        self.set_bg_colours()
        self.show_spawn() # bg colours and show spawn have to be here cause of the weird errors with get_leave_spawn and get_dont_set_spawn please dont move these
        if self.pathfind_pressed:
            self.strongholds.set_current_location(self.pos)
            self.pathfind_pressed=False
            return
        if self.strongholds.get_last_path() == 2: # spawn was left behind
            self.strongholds.set_current_location(
                self.strongholds.get_last_sh_coords(-2) #sets location at 2nd last sh coords which is where your spawn was left i think
            )
        if self.strongholds.get_dont_set_spawn():
            self.strongholds.set_current_location(self.strongholds.spawn) # sets location at spawn when it was optimal
            print("leave ur spawn behind at the next portal")
        print(get_nether_coords(self.strongholds.get_current_location()))

    def empty(self):
        """tells the program you have found the empty sector, runs when empty button is pressed. graphs empty sector as red"""
        print("empty sector\n")
        self.empty_button.config(state="disabled")
        self.inst_label.config(text="")

        self.next_sh(True)
        # plot empty sh point
        try:
            self.point = plt.scatter(
                self.strongholds.get_last_sh_coords()[0],
                self.strongholds.get_last_sh_coords()[1],
                c="red",
                s=50,
            )
            plt.draw()
        except Exception as e:
            print("photo broken", e)
            pass

    def skip_empty(self):
        """skips empty sector in the rare case you find all 9 and this is the last place to check but you already know its empty. graphs empty sector as red"""
        print("empty sector\n")
        self.empty_button.config(state="disabled")
        self.inst_label.config(text="")

        # plot empty sh point
        try:
            self.point = plt.scatter(
                *self.strongholds.get_next_sh_coords(),
                c="red",
                s=50,
            )
            plt.draw()
        except Exception as e:
            print("photo broken", e) # this was from some weird thing i edited in mimes code i couldnt figure out why this would ever raise an exception or what it means if it does
            pass

        #self.complete_sh(self.strongholds.get_next_sh_coords(), True)

        
        # add empty sector to estimations??? for some reason??? also why cant it just use append
        # nevermind it breaks without this
        self.strongholds.estimations.insert(
            len(self.strongholds.estimations), self.strongholds.get_next_sh_coords()
        )
    

    def find_from_coords(self):
        """redoes pathfinding from specific coords if user gets lost or something idk"""
        # has to find out if sh listed has been completed or not and maybe adds it to completed array
        msg = tk.messagebox.askyesno(
            message="Have you filled in the portal at the stronghold currently listed?"
        )
        if msg:
            self.complete_sh(self.strongholds.get_next_sh_coords(), False) #setting this to 'False' could theoretically cause a bug if the user does this on the empty 8th ring sh before pressing 'empty'... but that wouldnt happen probably... surely...
            self.update_image()

        new_coords = tk.simpledialog.askstring(
            "",
            "Type out your x and z coordinates you want to start pathfinding from (OW):",
        )
        try:
            new_pos = tuple(parse_input(new_coords))
        except:
            tk.messagebox.showerror(
                message="Something went wrong. Make sure you only input your x and z coordinate separated by a space, or copy paste the f3+c command"
            )
            return

        if not new_pos:
            tk.messagebox.showerror(
                message="Something went wrong. Make sure you only input your x and z coordinate separated by a space, or copy paste the f3+c command"
            )
            return
        else:
            self.pos = new_pos
            self.get_new_path()
            self.pathfind_pressed = True


    def get_new_path(self):
        """redoes pathfinding with only the strongholds left and a new current location"""
        print("GET NEW PATH")
        self.empty_button.config(state="disabled")
        self.inst_label.config(text="")

        reverse_ests = self.strongholds.estimations[self.strongholds.get_completed_count()-8:]
        unfinished_ests = reverse_ests[::-1]
        print(unfinished_ests)
        copied_estimations = self.strongholds.estimations.copy()

        #get new path
        write_nodes_qs_file(
            self.pos, unfinished_ests
        )
        #CHANGE AFTER TESTING
        sorted_estimations = sort_estimations_order_by_path(read_path_qs_file(), unfinished_ests) #THIS GOES TO THE SORT_ESTIMATIONS IN UTILS ITS CONFUSING I KNOW IM SORRY
        #ok that thing returns the sorted and optimized path for just the strongholds we havent been to yet
        #now we gotta put them back into strongholds.estimations by overwriting whats already there
        j=0
        print("LENGTHS")
        print(self.strongholds.get_completed_count())
        print(len(self.strongholds.estimations))
        print(len(sorted_estimations))
        for i in range(self.strongholds.get_completed_count()-8, len(self.strongholds.estimations)):
            self.strongholds.estimations[i] = sorted_estimations[j]
            j += 1

        print("\n\n\nEQUAL LENGTH???")
        print(len(self.strongholds.estimations)==len(copied_estimations))
        for i in range(len(self.strongholds.estimations)):
            print(copied_estimations[i], self.strongholds.estimations[i], copied_estimations[i]==self.strongholds.estimations[i])
        print("\n\n\n")

        self.create_empty_widgets()
        try:
            self.optimize_next_3_nodes()
        except IndexError:
            pass
        self.update_image()
        self.display_next_sh()
        print("DONE GET NEW PATH")

    def set_next_hotkey(self):
        """sets hotkey to go to the next stronghold when you press the set hotkey button"""
        colour = self.set_hotkey_button.cget("background")
        try:
            self.listener.stop()
        except:
            pass
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.next_stronghold_hotkey = simpledialog.askstring("Input", "Enter a hotkey:")
        if self.next_stronghold_hotkey == "":
            self.set_hotkey_button.config(text="Next SH Hotkey", bg=colour)
        #if the graph is your active window and you press Q it closes it, and K and L will mess it up. Still happens if they arent your hotkey but hopefully this helps prevent it
        elif self.next_stronghold_hotkey == "k" or self.next_stronghold_hotkey == "l" or self.next_stronghold_hotkey == "q":
            tk.messagebox.showerror("no", "You cannont make this your hotkey.")
            self.set_hotkey_button.config(text="Next SH Hotkey", bg=colour)
            self.next_stronghold_hotkey = ""
        else:
            print("set hotkey to " + self.next_stronghold_hotkey)
            self.set_hotkey_button.config(text=f"Next SH Hotkey: {self.next_stronghold_hotkey}", bg=colour)
            self.listener.start()

    def on_press(self, key):
        """runs every time any key is pressed and checks if it's the next sh hotkey"""
        if get_key_string(key) == self.next_stronghold_hotkey:
            self.newnext_button.invoke()
            return

    def movebutton(self):
        """moves the next button around like an aim trainer hehehehe"""
        x=random.uniform(0.1,0.9)
        y=random.uniform(0.1,0.9)
        self.newnext_button.place(relx=x, rely=y)
        self.newnext_button.lift()
