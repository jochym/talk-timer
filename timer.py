#!/usr/bin/env python
#
# Started and havy modified from Acire snippets
# [SNIPPET_AUTHOR: Jurjen Stellingwerff <jurjen@stwerff.xs4all.nl>]
# [SNIPPET_LICENSE: GPL]
# (L) 2010 Pawel T. Jochym
# The code below is licensed under GPLv3 or later

import gi
gi.require_version('Gst', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import GObject, Gst, Gtk

import math
import cairo
import sys
import time

#TODO: All the params should be configurable in the dialog box. This is a goal for the next release after fixing the timing issue.
#TODO: Implement pause functionality

# number of ticks (redraws) per second
ticks=10

# Number of seconds between alerts in overtime
alerts=30

# Obvious but usefull for debugging

# Second length in ms
oneSecond=1000

# Minute length in seconds
oneMinute=60

#Specify your alert file bellow 
#It can be any audio supported by gstreamer
file = "/usr/share/sounds/gnome/default/alerts/glass.ogg"
file = "/usr/share/sounds/gnome/default/alerts/drip.ogg"

#Create a player

Gst.init(None)

class Player:
    def __init__(self, file):
        #Element playbin automatic plays any file
        self.player = Gst.ElementFactory.make("playbin", "player")
        #Set the uri to the file
        self.player.set_property("uri", "file://" + file)

        #Enable message bus to check for errors in the pipeline
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)


    def run(self):
        self.player.set_state(Gst.State.PLAYING)

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            #file ended, stop
            self.player.set_state(Gst.State.NULL)
        elif t == Gst.MessageType.ERROR:
            #Error ocurred, print and stop
            self.player.set_state(Gst.State.NULL)
            err, debug = message.parse_error()
            print "Error: %s" % err, debug


class PresentationTimer:
    def __init__(self):

#TODO The GUI setup should be moved to the glade definition file.

        window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        window.set_title("Presentation Timer")
        window.connect("destroy", lambda w: Gtk.main_quit())
        self.area = Gtk.DrawingArea()
        self.width=480
        self.height=480
        self.area.set_size_request(self.width, self.height )
        vbox=Gtk.VBox()
        vbox.pack_start(self.area,True,True,0)
        hbox=Gtk.HBox(True)
        vbox.pack_end(hbox,False,False,0)
        window.add(vbox)
        self.area.connect("draw", self.expose)
        self.area.connect("size-allocate", self.on_size_allocate)
        self.area.show()

        self.timer=None
        self.Talert=None
        
        self.clock=None
        self.Tstart=time.time()
        self.now = self.Tstart
        self.running = False

        adj1 = Gtk.Adjustment(15, 1, 120, 1, 5)
        spinner1 = Gtk.SpinButton()
	spinner1.set_adjustment(adj1)
        adj2 = Gtk.Adjustment(5, 1, 45, 1, 5)
        spinner2 = Gtk.SpinButton()
	spinner2.set_adjustment(adj2)

        adj1.connect("value_changed", self.setupChanged, spinner1, spinner2)
        adj2.connect("value_changed", self.setupChanged, spinner1, spinner2)

        self.setupClock(spinner1, spinner2)
        self.counter = 0
        self.overtime = False
        self.ringed = False
        
        button = Gtk.Button("Start")
        button.connect("clicked", self.startClock, spinner1, spinner2)
        hbox.pack_start(button, False, False, 0)

#TODO No pausing for now
#        button = Gtk.Button("Pause")
#        button.connect("clicked", self.pauseClock, spinner1, spinner2)
#        hbox.pack_start(button, False, False)

        button = Gtk.Button("Stop")
        button.connect("clicked", self.stopClock, "Stop button")
        hbox.pack_start(button, False, False, 0)

        hbox1=Gtk.HBox(False)
        hbox.pack_end(hbox1, False, False, 0)

        label=Gtk.Label("Talk:")
        hbox1.pack_start(label,False,False, 0)
        hbox1.pack_start(spinner1,False,False, 0)
        
        label=Gtk.Label("Discussion:")
        hbox1.pack_start(label,False,False,0)
        hbox1.pack_start(spinner2,False,False,0)

        window.show_all()
        
        # Start the display update clock (ticks/second)
        self.clock=GObject.timeout_add(oneSecond/ticks, self.updateClock)


    def setupClock(self, spinTalk, spinDisc):
        self.talk = oneMinute*spinTalk.get_value_as_int()
        self.discuss = oneMinute*spinDisc.get_value_as_int()
        self.total = self.talk+self.discuss
        

    def setupChanged(self, wdg, spinTalk, spinDisc):
        self.setupClock(spinTalk, spinDisc)
        self.area.queue_draw()

    def startClock(self, wdg, spinTalk, spinDisc):
        self.setupClock(spinTalk, spinDisc)
        if self.Talert :
            GObject.source_remove(self.Talert)
            self.Talert=None
        self.Tstart = time.time()
        self.now = self.Tstart
        self.overtime = False
        self.running = True
        self.ringed = False
        #print "Starting clock: %dm talk, %dm total" % (self.talk/60, self.total/60) 

    def stopClock(self,wdg,data=None):
        self.overtime=False
        if self.Talert :
            GObject.source_remove(self.Talert)
            self.Talert=None
        self.running = False
        self.ringed = False
        self.overtime = False
        self.Tstart = self.now
        self.area.queue_draw()
        
#TODO Pausing not implemented yet
    def pauseClock(self,wdg, spinTalk, spinDisc):
        if self.Talert :
            GObject.source_remove(self.Talert)
            self.Talert=None
        self.running = False
        self.pause = True
        self.area.queue_draw()

    def updateClock(self):
        # We are first time over talk length
        if (self.running and 
            (time.time() > (self.Tstart + self.talk)) and 
            not self.ringed) :
                self.ringed = True
                self.alert()
        # The time has been added after overtime => reset overtime
        if (self.overtime and 
            (time.time() < (self.Tstart + self.total))):
            self.overtime = False
            self.running = True
        # We are first time over total length
        if (self.running and 
            (time.time() > (self.Tstart + self.total)) and 
            not self.overtime):
                self.overtime = True
                self.running = False
                self.alert()
                if not self.Talert :
                    self.Talert=GObject.timeout_add(oneSecond*alerts, self.alert)
        self.area.queue_draw()
        return True

    def on_size_allocate(self, _unused, allocation):
        self.width = allocation.width
        self.height = allocation.height

    def expose(self, area, event):
        self.context = area.get_property('window').cairo_create()
        self.draw_clock(self.width/2, self.height/2)
        return False

    def alert(self):
        player=Player(file)
        player.run()
        return True


    def draw_clock(self, x, y):
        self.context.save()
        cx=self.context
        cx.set_line_width(1)
        if self.running :
            self.now=time.time()
        if self.overtime :
            self.now = self.Tstart + self.total
        dT=self.now-self.Tstart
        c=int(self.total-self.discuss-dT)
        if c<0 :
            c=int(self.total-dT)
        t=dT/self.total
        tover=self.total-c
        a=-math.pi/2
        
        r=min(x,y)-10
        cx.move_to(x,y)
        cx.arc(x,y,r,a,a+2*math.pi*self.talk/self.total)
        cx.line_to(x,y)
        cx.close_path()
        cx.set_source_rgb(1, 1, 0.5)
        cx.fill()
        cx.arc(x,y,r,a+2*math.pi*self.talk/self.total,a)
        cx.line_to(x,y)
        cx.close_path()
        cx.set_source_rgb(0.5, 0.4, 1)
        cx.fill()
        cx.arc(x,y,r,0,2*math.pi)
        cx.set_source_rgb(0.5, 0.1, 0.1)
        cx.stroke()
        cx.arc(x,y,r-1,a,a+2*math.pi*t)
        cx.line_to(x,y)
        cx.close_path()
        cx.set_source_rgba(0.2, 1, 0.2,0.6)
        cx.fill()
        cx.arc(x,y,r-1,a+2*math.pi*t,a+2*math.pi*t)
        cx.line_to(x,y)
        cx.set_source_rgb(0,0,0)
        cx.stroke()
        cx.select_font_face("Monospace", 
            cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cx.set_font_size(r/3)
        cx.move_to(x-r/2,y+r/2)
        cx.set_source_rgb(1, 0.3, 0.3)
        
        if self.overtime:
            tover=int(time.time())-self.now
            if tover > 0 : cx.show_text("%2d:%02d" % (tover/60, (tover)%(60)))
            if (int(time.time())%2)==0 :
                cx.select_font_face("Arial", 
                    cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
                cx.set_font_size(r/4)
                cx.move_to(x-r/1.5,y-r/5)
                cx.set_source_rgb(1, 0, 0)
                cx.show_text("OVERTIME!")
        else :
            cx.show_text("%2d:%02d" % (c/60, (c)%(60)))
            
        cx.select_font_face("Monospace", 
            cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cx.set_font_size(r/8)
        cx.move_to(0,r/10)
        cx.set_source_rgb(0.3, 0.3, 1)
        tm=time.localtime()
        cx.show_text("%2d:%02d:%02d" % (tm.tm_hour, tm.tm_min, tm.tm_sec))
        self.context.restore()
        return

def main():
    Gtk.main()
    return 0

if __name__ == "__main__":
    import sys
    
    if len(sys.argv)>1 :
        file=sys.argv[1].strip()
    PresentationTimer()
    main()


