#!/usr/bin/env python3

import curses
import logging
import os
import re
import time
from socket import socket, socket_collection

class screen:
	def __init__(self, stdscr, sockets, config):
		self.scr = stdscr
		self.sockets = sockets
		self.config = config

	def refresh(self):
		self.scr.clear()
		i = 1
		for sock in self.sockets.all.values():
			is_gone, is_deleted = self.sockets.is_gone(sock, self.config)
			if is_deleted: continue
			self.draw_socket(0, i, sock,
					self.sockets.is_new(sock, self.config), is_gone)
			i += 1
		self.scr.refresh()

	def draw_socket(self, x, y, sock, is_new, is_gone):
		local_addr = sock.local_addr
		for name, addr in devices.items():
			if local_addr[:len(addr)] == addr:
				local_addr = name + local_addr[len(addr):]
				break
		state = sock.state
		if state == 'ESTABLISHED': state = 'EST'
		elif state == 'TIME_WAIT': state = 'TIW'
		elif state == 'FIN_WAIT1': state = 'FW1'
		elif state == 'FIN_WAIT2': state = 'FW2'
		elif state == 'CLOSE_WAIT': state = 'CLW'
		elif state == 'LISTEN': state = 'LSN'
		elif state == 'SYN_SENT': state = 'SYS'
		elif state == 'SYN_RECV': state = 'SYR'
		elif state == 'LAST_ACK': state = 'ACK'
		elif state == 'CLOSING': state = 'CLO'
		elif state == 'UNKNOWN': state = 'UNK'
		# "CLOSE"
		timer1 = sock.timer1
		if timer1 == 'on': timer1 = 'r'
		elif timer1 == 'off': timer1 = '.'
		elif timer1 == 'keepalive': timer1 = 'k'
		elif timer1 == 'timewait': timer1 = 'w'

		text = '%21s %10s ' % (
			sock.foreign_addr + screen._padding(sock.foreign_addr, 5),
			local_addr + screen._padding(local_addr, 5)
		)
		self.scr.addstr(y, x, text,
			screen._attribute(sock.updated, '', is_new, is_gone))
		x += len(text)

		text = '%5d ' % sock.recvq
		self.scr.addstr(y, x, text,
			screen._attribute(sock.updated, 'recvq', is_new, is_gone))
		x += len(text)
		
		text = '%5d ' % sock.sendq
		self.scr.addstr(y, x, text,
			screen._attribute(sock.updated, 'sendq', is_new, is_gone))
		x += len(text)

		text = '%3s ' % state
		self.scr.addstr(y, x, text,
			screen._attribute(sock.updated, 'state', is_new, is_gone))
		x += len(text)

		text = '%s ' % timer1
		self.scr.addstr(y, x, text,
			screen._attribute(sock.updated, 'timer1', is_new, is_gone))
		x += len(text)

		text = '%5d ' % sock.timer2[0]
		self.scr.addstr(y, x, text,
			screen._attribute(sock.updated, 'timer2[0]', is_new, is_gone))
		x += len(text)

		text = '%2d ' % sock.timer2[1]
		self.scr.addstr(y, x, text,
			screen._attribute(sock.updated, 'timer2[1]', is_new, is_gone))
		x += len(text)

		text = '%1d ' % sock.timer2[2]
		self.scr.addstr(y, x, text,
			screen._attribute(sock.updated, 'timer2[2]', is_new, is_gone))
		x += len(text)

	@staticmethod
	def _padding(str, max_width):
		idx = str.index(':')
		return ' ' * (max_width - (len(str) - idx - 1))

	@staticmethod
	def _attribute(lst, val, is_new, is_gone):
		if is_gone: return curses.color_pair(1) #A_BLINK #A_DIM
		elif is_new: return curses.color_pair(3)
		elif val in lst: return curses.color_pair(3) #A_BOLD
		return curses.A_NORMAL #color_pair(7) # curses.A_NORMAL

def get_network_devices():
	with os.popen("/sbin/ifconfig") as out:
		devices = {'': '0.0.0.0'}
		result = out.read()
		pattern = re.compile('^([a-z0-9]+).*\n *inet addr:([0-9.]+)',
				re.MULTILINE)
		for match in pattern.finditer(result):
			devices[match.group(1)] = match.group(2)
		return devices

def update():
	global i
	with os.popen("netstat -ano") as out:
		sockets.visit_reset()
		while True:
			line = out.readline()
			if not line:
				break
			words = line.split()
			if words[0] == 'Active' or words[0] == 'Proto' or words[0] == 'unix':
				continue
			if words[0] == 'tcp6' or words[0] == 'udp' or words[0] == 'udp6':
				# TODO: handle these sockets, too
				continue
			sock = socket(words)
			sockets.update(sock)
			sockets.visit(sock)
		for sock in sockets.unvisited():
			sockets.remove(sock)

def handle_input(stdscr):
	key = stdscr.getch()
	if key == ord('q'):
		return True
	return False
	
def main(stdscr):
	curses.use_default_colors()
	for i in range(0, curses.COLORS):
		curses.init_pair(i, i, -1)
	curses.curs_set(0)
	term = screen(stdscr, sockets, config)
	while True:
		start = time.time()
		update()
		term.refresh()
		elapsed = time.time() - start
		curses.halfdelay(int(10 * (config.UPDATE_INTERVAL - elapsed)))
		if handle_input(stdscr): break


logging.basicConfig(filename='debug.log', level=logging.DEBUG)

class Config:
	pass
config = Config()
config.HIGHLIGHT_DURATION = 5
config.UPDATE_INTERVAL = 2

sockets = socket_collection()
devices = get_network_devices()
curses.wrapper(main)

