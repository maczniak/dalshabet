import time
from collections import OrderedDict
from operator import methodcaller

class socket:
	def __init__(self, w):
		self.proto = w[0]
		self.recvq = int(w[1])
		self.sendq = int(w[2])
		self.local_addr = w[3]
		self.foreign_addr = w[4]
		self.state = w[5]
		self.timer1 = w[6]
		self.timer2 = [int(float(x)) for x in w[7][1:-1].split('/')]
		self.new_time = time.time()
		self.update_time = time.time()
		self.gone_time = None
		self.updated = []
	
	def port_addr_order(self):
		if self.state == 'LISTEN':
			idx = self.local_addr.find(':')
			return (int(self.local_addr[idx + 1:]) - 100000, '')
		idx = self.foreign_addr.find(':')
		return (int(self.foreign_addr[idx + 1:]), self.foreign_addr[:idx])

	def update(self, sock):
		self.updated = []
		if self.recvq != sock.recvq:
			self.recvq = sock.recvq
			self.updated.append('recvq')
		if self.sendq != sock.sendq:
			self.sendq = sock.sendq
			self.updated.append('sendq')
		if self.state != sock.state:
			self.state = sock.state
			self.updated.append('state')
		if self.timer1 != sock.timer1:
			self.timer1 = sock.timer1
			self.updated.append('timer1')
		if self.timer2[0] != sock.timer2[0]:
			self.timer2[0] = sock.timer2[0]
			self.updated.append('timer2[0]')
		if self.timer2[1] != sock.timer2[1]:
			self.timer2[1] = sock.timer2[1]
			self.updated.append('timer2[1]')
		if self.timer2[2] != sock.timer2[2]:
			self.timer2[2] = sock.timer2[2]
			self.updated.append('timer2[2]')
		if self.updated:
			self.update_time = time.time()

class socket_collection:
	def __init__(self):
		self.all = OrderedDict(sorted({}, key=methodcaller('port_addr_order')))

	def update(self, sock):
		key = socket_collection.key(sock)
		if not key in self.all:
			self.all[key] = sock
		else:
			self.all[key].update(sock)

	def remove(self, sock):
		if not sock.gone_time:
			sock.gone_time = time.time()

	def visit_reset(self):
		self.clone = dict(self.all)

	def visit(self, sock):
		key = socket_collection.key(sock)
		if key in self.clone:
			self.clone[key] = None

	def unvisited(self):
		# TODO: thread-safe, iterator
		return [v for k,v in self.clone.items() if v is not None]

	def is_new(self, sock, config):
		if time.time() - sock.new_time <= config.HIGHLIGHT_DURATION:
			return True
		return False

	def is_gone(self, sock, config):
		if not sock.gone_time:
			return False, False
		if time.time() - sock.gone_time <= config.HIGHLIGHT_DURATION:
			return True, False
		del self.all[socket_collection.key(sock)]
		return True, True

	@staticmethod
	def key(sock):
		if sock.foreign_addr == '0.0.0.0:*':
			return sock.local_addr
		return sock.foreign_addr

