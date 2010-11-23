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

#number of ticks per second
ticks=25
talk=20
discuss=10

alerts=5

#Specify your alert file bellow 
#It can be any video/audio supported by gstreamer
file = "/usr/share/sounds/gnome/default/alerts/glass.ogg"

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

        adj1 = gtk.Adjustment(15, 1, 120, 1, 5)
        spinner1 = gtk.SpinButton(adj1, 0, 0)
        adj2 = gtk.Adjustment(5, 1, 45, 1, 5)
        spinner2 = gtk.SpinButton(adj2, 0, 0)

#        adj1.connect("value_changed", self.setupChanged, spinner1, spinner2)
#        adj2.connect("value_changed", self.setupChanged, spinner1, spinner2)

        self.setupClock(spinner1, spinner2)
        self.counter = ticks*self.total
        self.overtime=False
        
        button = gtk.Button("Start")
        button.connect("clicked", self.startClock, spinner1, spinner2)
        hbox.pack_start(button, False, False)

        hbox1=gtk.HBox(False)
        hbox.pack_start(hbox1, False, False)

        label=gtk.Label("Talk:")
        hbox1.pack_start(label,False,False)
        hbox1.pack_start(spinner1,False,False)
        
        hbox1=gtk.HBox(False)
        hbox.pack_start(hbox1, False, False)

        label=gtk.Label("Discussion:")
        hbox1.pack_start(label,False,False)
        hbox1.pack_start(spinner2,False,False)

        button = gtk.Button("Stop")
        button.connect("clicked", self.stopClock, "Stop button")
        hbox.pack_end(button, False, False)

        window.show_all()

    def setupClock(self, spinTalk, spinDisc):
        self.talk = 60*spinTalk.get_value_as_int()
        self.discuss = 60*spinDisc.get_value_as_int()
        self.total = self.talk+self.discuss
        

    def setupChanged(self, wdg, spinTalk, spinDisc):
        self.setupClock(spinTalk, spinDisc)
        self.area.queue_draw()

    def startClock(self, wdg, spinTalk, spinDisc):
        self.setupClock(spinTalk, spinDisc)
        self.counter = ticks*self.total
        self.overtime=False
        print "Starting clock: %dm talk, %dm total" % (self.talk/60, self.total/60) 
        self.timer=gobject.timeout_add(1000/ticks, self.countdown)
        self.countdown()

    def stopClock(self,wdg,data=None):
        self.counter=ticks*self.total
        self.overtime=False
        gobject.source_remove(self.timer)
        self.area.queue_draw()

    def expose(self, area, event):
        self.context = area.window.cairo_create()
        self.draw_clock(event.area.width/2, event.area.height/2)
        return False

    def alert(self):
        player=Player(file)
        player.run()
        return True

    def countdown(self):
        if self.counter==ticks*self.discuss :
            player=Player(file)
            player.run()
        if self.counter > 0:
            self.counter -= 1
            self.area.queue_draw()
            return True
        else:
            self.area.queue_draw()
            player=Player(file)
            self.overtime=True
            player.run()
            self.timer=gobject.timeout_add(1000*alerts, self.alert)
            return False


    def draw_clock(self, x, y):
        self.context.save()
        cx=self.context
        cx.set_line_width(1)
        t=1.0-1.0*self.counter/(self.total*ticks)
        c=int(self.total-self.counter/ticks)
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
        cx.set_source_rgb(0, 1, 0)
        cx.stroke()
        cx.arc(x,y,r,a,a+2*math.pi*t)
        cx.line_to(x,y)
        cx.close_path()
        cx.set_source_rgba(0.2, 1, 0.2,0.6)
        cx.fill()
        cx.arc(x,y,r,a+2*math.pi*t,a+2*math.pi*t)
        cx.line_to(x,y)
        cx.set_source_rgb(0,0,0)
        cx.stroke()
        cx.select_font_face("Courier", 
            cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cx.set_font_size(r/5)
        cx.move_to(x-r/3.3,y+r/2)
        cx.set_source_rgb(1, 0.3, 0.3)
        cx.show_text("%2d:%02d" % (c/60, (c)%(60)))
        if self.overtime :
            cx.select_font_face("Arial", 
                cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cx.set_font_size(r/4)
            cx.move_to(x-r/1.5,y-r/5)
            cx.set_source_rgb(1, 0, 0)
            cx.show_text("OVERTIME!")
        self.context.restore()
        return

def main():
    gtk.main()
    return 0

if __name__ == "__main__":
    PresentationTimer()
    main()


