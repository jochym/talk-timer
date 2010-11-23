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
ticks=5
talk=15
discuss=5

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

#Execution starts here

#Specify your file bellow 
#It can be any video/audio supported by gstreamer
file = "/usr/share/sounds/gnome/default/alerts/bark.ogg"

#player = Player(file)
#player.run()
#loop = gobject.MainLoop()
#loop.run()



class PresentationTimer:
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_title("Presentation Timer")
        window.connect("destroy", lambda w: gtk.main_quit())
        self.area = gtk.DrawingArea()
        self.area.set_size_request(480, 480)
        window.add(self.area)
        self.area.connect("expose-event", self.expose)
        self.area.show()
        if len(sys.argv)>2 :
            self.talk = int(sys.argv[1])
            self.discuss = int(sys.argv[2])
        else :
            self.talk = talk
            self.discuss = discuss
        self.total = 60*ticks*(self.talk+self.discuss)
        self.talk = 60*ticks*self.talk
        self.counter = self.total
        gobject.timeout_add(1000/ticks, self.countdown)
        self.countdown()
        window.show()

    def expose(self, area, event):
        self.context = area.window.cairo_create()
        self.draw_clock(event.area.width/2, event.area.height/2)
        return False

    def countdown(self):
        if self.counter==self.talk :
            player=Player(file)
            player.run()
        if self.counter > 0:
            self.counter -= 1
            self.area.queue_draw()
            return True
        else:
            self.area.queue_draw()
            player=Player(file)
            player.run()
            return False


    def draw_clock(self, x, y):
        self.context.save()
        cx=self.context
        cx.set_line_width(1)
        t=1.0-1.0*self.counter/self.total
        c=int(self.total-self.counter)
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
        cx.show_text("%2d:%02d" % (c/(60*ticks), (c/ticks)%(60)))
        self.context.restore()
        return

def main():
    gtk.main()
    return 0

if __name__ == "__main__":
    PresentationTimer()
    main()


