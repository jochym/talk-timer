#!/usr/bin/env python
#
# Started and havy modified from Acire snippets
# [SNIPPET_AUTHOR: Jurjen Stellingwerff <jurjen@stwerff.xs4all.nl>]
# [SNIPPET_LICENSE: GPL]
# (L) 2010 Pawel T. Jochym

import pygtk
pygtk.require('2.0')
import gtk, gobject
import pygst
pygst.require("0.10")
import gst
import math
import cairo
import sys
import time

# number of ticks (redraws) per second
ticks=10

# Number of seconds between alerts in overtime
alerts=20

# Second length in ticks (temporary measure)

oneSecond=990

#Specify your alert file bellow 
#It can be any audio supported by gstreamer
file = "/home/jochym/Desktop/devel/timer/bell.wav"

#Create a player

class Player:
	def __init__(self, file):
		#Element playbin automatic plays any file
		self.player = gst.element_factory_make("playbin", "player")
		#Set the uri to the file
		self.player.set_property("uri", "file://" + file)

		#Enable message bus to check for errors in the pipeline
		bus = self.player.get_bus()
		bus.add_signal_watch()
		bus.connect("message", self.on_message)

	
	def run(self):
		self.player.set_state(gst.STATE_PLAYING)

	def on_message(self, bus, message):
		t = message.type
		if t == gst.MESSAGE_EOS:
			#file ended, stop
			self.player.set_state(gst.STATE_NULL)
			#loop.quit()
		elif t == gst.MESSAGE_ERROR:
			#Error ocurred, print and stop
			self.player.set_state(gst.STATE_NULL)
			err, debug = message.parse_error()
			print "Error: %s" % err, debug
			#loop.quit()


class PresentationTimer:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_title("Presentation Timer")
        window.connect("destroy", lambda w: gtk.main_quit())
        self.area = gtk.DrawingArea()
        self.area.set_size_request(480, 480)
        vbox=gtk.VBox()
        vbox.pack_start(self.area,True,True)
        hbox=gtk.HBox(True)
        vbox.pack_end(hbox,False,False)
        window.add(vbox)
        self.area.connect("expose-event", self.expose)
        self.area.show()

        self.timer=None
        self.Talert=None
        
        #self.clock=gobject.timeout_add(oneSecond, self.updateClock)
        self.clock=None

        adj1 = gtk.Adjustment(15, 1, 120, 1, 5)
        spinner1 = gtk.SpinButton(adj1, 0, 0)
        adj2 = gtk.Adjustment(5, 1, 45, 1, 5)
        spinner2 = gtk.SpinButton(adj2, 0, 0)

        adj1.connect("value_changed", self.setupChanged, spinner1, spinner2)
        adj2.connect("value_changed", self.setupChanged, spinner1, spinner2)

        self.setupClock(spinner1, spinner2)
        self.counter = 0
        self.overtime=False
        
        button = gtk.Button("Start")
        button.connect("clicked", self.startClock, spinner1, spinner2)
        hbox.pack_start(button, False, False)

        button = gtk.Button("Pause")
        button.connect("clicked", self.pauseClock, spinner1, spinner2)
        hbox.pack_start(button, False, False)

        button = gtk.Button("Stop")
        button.connect("clicked", self.stopClock, "Stop button")
        hbox.pack_start(button, False, False)

        hbox1=gtk.HBox(False)
        hbox.pack_end(hbox1, False, False)

        label=gtk.Label("Talk:")
        hbox1.pack_start(label,False,False)
        hbox1.pack_start(spinner1,False,False)
        
        label=gtk.Label("Discussion:")
        hbox1.pack_start(label,False,False)
        hbox1.pack_start(spinner2,False,False)


        window.show_all()
        
        #self.clock=gobject.timeout_add(1000, self.updateClock)


    def setupClock(self, spinTalk, spinDisc):
        self.talk = 60*spinTalk.get_value_as_int()
        self.discuss = 60*spinDisc.get_value_as_int()
        self.total = self.talk+self.discuss
        

    def setupChanged(self, wdg, spinTalk, spinDisc):
        self.setupClock(spinTalk, spinDisc)
        self.area.queue_draw()

    def startClock(self, wdg, spinTalk, spinDisc):
        self.setupClock(spinTalk, spinDisc)
        self.counter = 0
        self.overtime=False
        #print "Starting clock: %dm talk, %dm total" % (self.talk/60, self.total/60) 
        if self.timer :
            gobject.source_remove(self.timer)
        self.timer=gobject.timeout_add(oneSecond/ticks, self.countdown)
        self.countdown()

    def stopClock(self,wdg,data=None):
        #self.counter=0
        self.overtime=False
        if self.Talert :
            gobject.source_remove(self.Talert)
            self.Talert=None
        if self.timer :
            gobject.source_remove(self.timer)
            self.timer=None
        self.area.queue_draw()
        
    def pauseClock(self,wdg, spinTalk, spinDisc):
        if self.timer :
            gobject.source_remove(self.timer)
            self.timer=None
        else :
            self.timer=gobject.timeout_add(oneSecond/ticks, self.countdown)
            self.countdown()
        if self.Talert :
            gobject.source_remove(self.Talert)
            self.Talert=None
        else :
            self.Talert=gobject.timeout_add(oneSecond*alerts, self.alert)

    def updateClock(self):
        self.area.queue_draw()
        return True

    def expose(self, area, event):
        self.context = area.window.cairo_create()
        self.draw_clock(event.area.width/2, event.area.height/2)
        return False

    def alert(self):
        player=Player(file)
        player.run()
        return True

    def countdown(self):
        if self.counter==ticks*self.talk:
            player=Player(file)
            player.run()
        if self.counter < self.total*ticks:
            self.counter += 1
            self.area.queue_draw()
            return True
        else:
            self.area.queue_draw()
            player=Player(file)
            self.overtime=True
            player.run()
            self.Talert=gobject.timeout_add(oneSecond*alerts, self.alert)
            return False


    def draw_clock(self, x, y):
        self.context.save()
        cx=self.context
        cx.set_line_width(1)
        t=1.0*self.counter/(self.total*ticks)
        c=int(self.counter/ticks)
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
        cx.select_font_face("Courier", 
            cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cx.set_font_size(r/3)
        cx.move_to(x-r/2,y+r/2)
        cx.set_source_rgb(1, 0.3, 0.3)
        cx.show_text("%2d:%02d" % (c/60, (c)%(60)))
        if self.overtime :
            cx.select_font_face("Arial", 
                cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cx.set_font_size(r/4)
            cx.move_to(x-r/1.5,y-r/5)
            cx.set_source_rgb(1, 0, 0)
            cx.show_text("OVERTIME!")

        cx.select_font_face("Courier", 
            cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cx.set_font_size(r/8)
        cx.move_to(0,r/10)
        cx.set_source_rgb(0.3, 0.3, 1)
        tm=time.localtime()
        cx.show_text("%2d:%02d" % (tm.tm_hour, tm.tm_min))
        self.context.restore()
        return

def main():
    gtk.main()
    return 0

if __name__ == "__main__":
    PresentationTimer()
    main()


