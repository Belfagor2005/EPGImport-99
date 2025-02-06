#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This file no longer has a direct link to Enigma2, allowing its use anywhere
# you can supply a similar interface. See plugin.py and OfflineImport.py for
# the contract.

from __future__ import print_function
# from . import log

from Components.config import config
from datetime import datetime
from os import statvfs, symlink, unlink
from os.path import exists, getsize, join, split, splitext, isdir, ismount
from sys import version_info
from twisted.internet import reactor, ssl, threads
from twisted.web.client import downloadPage
import gzip
import random
import six
import time
import twisted.python.runtime


try:
	pythonVer = version_info.major
except:
	pythonVer = 2


if pythonVer == 2:
	from httplib import HTTPException
	from urllib2 import build_opener, HTTPError, URLError
else:  # python3
	from http.client import HTTPException
	from urllib.error import HTTPError, URLError
	from urllib.request import build_opener


try:
    from urlparse import urlparse
except:
    from urllib.parse import urlparse


# Used to check server validity
HDD_EPG_DAT = '/hdd/epg.dat'
date_format = "%Y-%m-%d"
now = datetime.now()
alloweddelta = 2
CheckFile = "LastUpdate.txt"
ServerStatusList = {}
PARSERS = {'xmltv': 'gen_xmltv', 'genxmltv': 'gen_xmltv'}
sslverify = False
try:
	from twisted.internet._sslverify import ClientTLSOptions
	# from twisted.internet import ssl
	sslverify = True
except:
	sslverify = False

if sslverify:

	class SNIFactory(ssl.ClientContextFactory):
		def __init__(self, hostname=None):
			self.hostname = hostname
			# self.hostname = urlparse(hostname).hostname

		def getContext(self):
			ctx = self._contextFactory(self.method)
			if self.hostname:
				ClientTLSOptions(self.hostname, ctx)
			return ctx


def getMountPoints():
	mount_points = []
	try:
		from os import access, W_OK
		mounts = open('/proc/mounts', 'rb').readlines()
		mount_point = [x.split(' ', 2)[1] for x in mounts]
		if ismount(mount_point) and access(mount_point, W_OK):
			mount_points.append(mount_point)
	except Exception as e:
		print("[EPGImport]Error reading /proc/mounts:", str(e))
	return mount_points


mount_point = None
mount_points = getMountPoints()
for mp in mount_points:
	epg_path = join(mp, 'epg.dat')
	if exists(epg_path):
		mount_point = epg_path
		break


if config.misc.epgcache_filename.value:
	HDD_EPG_DAT = config.misc.epgcache_filename.value
else:
	config.misc.epgcache_filename.setValue(HDD_EPG_DAT)


def relImport(name):
	fullname = __name__.split('.')
	fullname[-1] = name
	mod = __import__('.'.join(fullname))
	for n in fullname[1:]:
		mod = getattr(mod, n)

	return mod


def getParser(name):
	module = PARSERS.get(name, name)
	mod = relImport(module)
	return mod.new()


def getTimeFromHourAndMinutes(hour, minute):
	# Check if the hour and minute are within valid ranges
	if not (0 <= hour < 24):
		raise ValueError("Hour must be between 0 and 23")
	if not (0 <= minute < 60):
		raise ValueError("Minute must be between 0 and 59")

	# Get the current local time
	now = time.localtime()

	# Calculate the timestamp for the specified time (today with the given hour and minute)
	begin = int(time.mktime((
		now.tm_year,     # Current year
		now.tm_mon,      # Current month
		now.tm_mday,     # Current day
		hour,            # Specified hour
		minute,          # Specified minute
		0,               # Seconds (set to 0)
		now.tm_wday,     # Day of the week
		now.tm_yday,     # Day of the year
		now.tm_isdst     # Daylight saving time (DST)
	)))
	return begin


def bigStorage(minFree, default, *candidates):
	try:
		diskstat = statvfs(default)
		free = diskstat.f_bfree * diskstat.f_bsize
		if (free > minFree) and (free > 50000000):
			return default
	except Exception as e:
		print("[EPGImport][bigStorage] Failed to stat %s:" % default, str(e))

	# mountpoints = getMountPoints()
	with open('/proc/mounts', 'rb') as f:
		# format: device mountpoint fstype options #
		mountpoints = [x.decode().split(' ', 2)[1] for x in f.readlines()]

	for candidate in candidates:
		if candidate in mountpoints:
			try:
				diskstat = statvfs(candidate)
				free = diskstat.f_bfree * diskstat.f_bsize
				if free > minFree:
					return candidate
			except Exception as e:
				print("[EPGImport][bigStorage] Failed to stat", str(e))
				continue
	return default


class OudeisImporter:
	"""Wrapper to convert original patch to new one that accepts multiple services"""

	def __init__(self, epgcache):
		self.epgcache = epgcache

	# difference with old patch is that services is a list or tuple, this
	# wrapper works around it.

	def importEvents(self, services, events):
		for service in services:
			try:
				self.epgcache.importEvent(service, events)
			except Exception as e:
				import traceback
				traceback.print_exc()
				print("[EPGImport][OudeisImporter][importEvents] ### importEvents exception:", str(e))


def unlink_if_exists(filename):
	try:
		unlink(filename)
	except Exception as e:
		print("[EPGImport] warning: Could not remove '%s' intermediate" % filename, repr(e))


class EPGImport:
	"""Simple Class to import EPGData"""

	def __init__(self, epgcache, channelFilter):
		self.eventCount = None
		self.epgcache = None
		self.storage = None
		self.sources = []
		self.source = None
		self.epgsource = None
		self.fd = None
		self.iterator = None
		self.onDone = None
		self.epgcache = epgcache
		self.channelFilter = channelFilter
		return

	def checkValidServer(self, serverurl):
		print("[EPGImport][checkValidServer]serverurl %s" % serverurl)
		dirname, filename = split(serverurl)
		if six.PY3:
			dirname = dirname.decode()
		FullString = dirname + '/' + CheckFile
		req = build_opener()
		req.addheaders = [('User-Agent', 'Twisted Client')]
		dlderror = 0
		if dirname in ServerStatusList:
			# If server is know return its status immediately
			return ServerStatusList[dirname]
		else:
			# Server not in the list so checking it
			try:
				response = req.open(FullString)
			except HTTPError as e:
				print('[EPGImport][checkValidServer] HTTPError in checkValidServer= ' + str(e.code))
				dlderror = 1
			except URLError as e:
				print('[EPGImport][checkValidServer] URLError in checkValidServer= ' + str(e.reason))
				dlderror = 1
			except HTTPException as e:
				print('[EPGImport][checkValidServer] HTTPException in checkValidServer', str(e))
				dlderror = 1
			except Exception:
				print('[EPGImport][checkValidServer] Generic exception in checkValidServer')
				dlderror = 1

		if not dlderror:
			LastTime = response.read().strip('\n')
			"""
			if isinstance(LastTime, bytes):  # Verifica se è un oggetto bytes
				LastTime = LastTime.decode("utf-8", "ignore").strip('\n')  # Decodifica i bytes in stringa
			"""
			if six.PY3:
				LastTime = response.read().decode().strip('\n')
			else:
				LastTime = response.read().strip('\n')
			try:
				FileDate = datetime.strptime(LastTime, date_format)
			except ValueError:
				print("[EPGImport] checkValidServer wrong date format in file rejecting server %s" % dirname)
				ServerStatusList[dirname] = 0
				response.close()
				return ServerStatusList[dirname]

			delta = (now - FileDate).days
			if delta <= alloweddelta:
				# OK the delta is in the foreseen windows
				ServerStatusList[dirname] = 1
			else:
				# Sorry the delta is higher removing this site
				print("[EPGImport] checkValidServer rejected server delta days too high: %s" % dirname)
				ServerStatusList[dirname] = 0
				response.close()
				return ServerStatusList[dirname]
		else:
			# We need to exclude this server
			print("[EPGImport] checkValidServer rejected server download error for: %s" % dirname)
			ServerStatusList[dirname] = 0
		return ServerStatusList[dirname]

	def beginImport(self, longDescUntil=None):
		"""Starts importing using Enigma reactor. Set self.sources before calling this."""
		if hasattr(self.epgcache, 'importEvents'):
			print('[EPGImport][beginImport] using importEvents.')
			self.storage = self.epgcache
		elif hasattr(self.epgcache, 'importEvent'):
			print('[EPGImport][beginImport] using importEvent(Oudis).')
			self.storage = OudeisImporter(self.epgcache)
		else:
			print("[EPGImport][beginImport] oudeis patch not detected, using using epgdat_importer.epgdatclass/epg.dat instead.")
			from . import epgdat_importer
			self.storage = epgdat_importer.epgdatclass()
		self.eventCount = 0
		if longDescUntil is None:
			# default to 7 days ahead
			self.longDescUntil = time.time() + 24 * 3600 * 7
		else:
			self.longDescUntil = longDescUntil
		self.nextImport()
		return

	def nextImport(self):
		self.closeReader()
		if not self.sources:
			self.closeImport()
			return
		self.source = self.sources.pop()
		# print("[EPGImport][nextImport], source =", self.source.description)
		self.fetchUrl(self.source.url)

	def fetchUrl(self, filename):
		if isinstance(filename, list):
			if len(filename) > 0:
				filename = filename[0]
			else:
				self.downloadFail("Empty list of alternative URLs", None)
				return

		if filename.startswith('http:') or filename.startswith('https:') or filename.startswith('ftp:'):
			self.urlDownload(filename, self.afterDownload, self.downloadFail)
		else:
			self.afterDownload(None, filename, deleteFile=False)
		return

	def urlDownload(self, sourcefile, afterDownload, downloadFail):
		path = bigStorage(9000000, '/media/hdd', *mount_points)
		if not path or not isdir(path):
			print("[EPGImport] Invalid path, using '/tmp'")
			path = '/tmp'  # Use fallback /tmp if invalid path, using.
		if "meia" in path:  # mistake ("media != meia)
			path = path.replace("meia", "media")
		filename = join(path, 'epgimport')
		ext = splitext(sourcefile)[1]
		# Keep sensible extension, in particular the compression type
		if ext and len(ext) < 6:
			# filename += ext
			filename += ext.decode("utf-8", "ignore") if isinstance(ext, bytes) else ext
		sourcefile = sourcefile.encode('utf-8')
		sslcf = SNIFactory(sourcefile) if sourcefile.decode().startswith('https:') else None
		print("[EPGImport][urlDownload] Downloading: " + sourcefile.decode() + " to local path: " + filename)
		print("[DEBUG] Type of sourcefile before downloadPage: %s" % type(sourcefile))
		print("[DEBUG] Type of filename before downloadPage: %s" % type(filename))
		if self.source.nocheck == 1:
			print("[EPGImport][urlDownload] Not checking the server since nocheck is set for it: " + sourcefile.decode())
			downloadPage(sourcefile, filename, timeout=90, contextFactory=sslcf).addCallbacks(afterDownload, downloadFail, callbackArgs=(filename, True))
		else:
			if self.checkValidServer(sourcefile) == 1:
				downloadPage(sourcefile, filename, timeout=90, contextFactory=sslcf).addCallbacks(afterDownload, downloadFail, callbackArgs=(filename, True))
			else:
				self.downloadFail("checkValidServer rejected the server")
		return filename

	def afterDownload(self, result, filename, deleteFile=False):
		print("[EPGImport][afterDownload]filename", filename)
		if not exists(filename):
			self.downloadFail("File not exists")
			return
		try:
			if not getsize(filename):
				raise Exception("[EPGImport][afterDownload] File is empty")
		except Exception as e:
			# print("[EPGImport][afterDownload] Exception filename 0", filename)
			self.downloadFail(e)
			return

		if self.source.parser == 'epg.dat':
			if twisted.python.runtime.platform.supportsThreads():
				print("[EPGImport][afterDownload] Using twisted thread for DAT file")
				threads.deferToThread(self.readEpgDatFile, filename, deleteFile).addCallback(lambda ignore: self.nextImport())
			else:
				self.readEpgDatFile(filename, deleteFile)
				return

		if filename.endswith('.gz'):
			self.fd = gzip.open(filename, 'rb')
			try:
				self.fd.read(10)
				self.fd.seek(0, 0)
			except gzip.BadGzipFile as e:
				print("[EPGImport][afterDownload] File downloaded is not a valid gzip file", filename)
				self.downloadFail(e)
				return

		elif filename.endswith('.xz') or filename.endswith('.lzma'):
			try:
				import lzma
			except ImportError:
				from backports import lzma
			self.fd = lzma.open(filename, 'rb')
			try:
				self.fd.read(10)
				self.fd.seek(0, 0)
			except lzma.LZMAError as e:
				print("[EPGImport][afterDownload] File downloaded is not a valid xz file", filename)
				try:
					print("[EPGImport][afterDownload] unlink", filename)
					unlink(filename)
				except Exception as e:
					print("[EPGImport][afterDownload] warning: Could not remove '%s' intermediate" % filename, e)
				self.downloadFail(e)
				return

		else:
			self.fd = open(filename, 'rb')

		if deleteFile and self.source.parser != 'epg.dat':
			try:
				print("[EPGImport][afterDownload] unlink", filename)
				unlink(filename)
			except Exception as e:
				print("[EPGImport][afterDownload] warning: Could not remove '%s' intermediate" % filename, e)

		self.channelFiles = self.source.channels.downloadables()
		if not self.channelFiles:
			self.afterChannelDownload(None, None)
		else:
			filename = random.choice(self.channelFiles)
			self.channelFiles.remove(filename)
			self.urlDownload(filename, self.afterChannelDownload, self.channelDownloadFail)
		return

	def downloadFail(self, failure):
		print("[EPGImport][downloadFail] download failed:", failure)
		self.source.urls.remove(self.source.url)

		if self.source.urls:
			print("[EPGImport][downloadFail] Attempting alternative URL")
			self.source.url = random.choice(self.source.urls)
			print("[EPGImport][downloadFail] try alternative download url", self.source.url)
			self.fetchUrl(self.source.url)
		else:
			self.nextImport()

	def afterChannelDownload(self, result, filename, deleteFile=True):
		print("[EPGImport][afterChannelDownload] filename", filename)
		if filename:
			try:
				if not getsize(filename):
					raise Exception("File is empty")
			except Exception as e:
				print("[EPGImport][afterChannelDownload] Exception filename", filename)
				self.channelDownloadFail(e)
				return

		if twisted.python.runtime.platform.supportsThreads():
			print("[EPGImport][afterChannelDownload] Using twisted thread")
			threads.deferToThread(self.doThreadRead, filename).addCallback(lambda ignore: self.nextImport())
			deleteFile = False  # Thread will delete it
		else:
			self.iterator = self.createIterator(filename)
			reactor.addReader(self)

		if deleteFile and filename:
			try:
				unlink(filename)
			except Exception as e:
				print("[EPGImport][afterChannelDownload] warning: Could not remove '%s' intermediate" % filename, e)

	def channelDownloadFail(self, failure):
		print("[EPGImport][channelDownloadFail]download channel failed:", failure)
		if self.channelFiles:
			filename = random.choice(self.channelFiles)
			if filename in self.channelFiles:
				self.channelFiles.remove(filename)
			print("[EPGImport][channelDownloadFail] File not in list, skipping remove:", filename)
			self.urlDownload(filename, self.afterChannelDownload, self.channelDownloadFail)
		else:
			print("[EPGImport][channelDownloadFail]no more alternatives for channels")
			self.nextImport()

	def createIterator(self, filename):
		self.source.channels.update(self.channelFilter, filename)
		return getParser(self.source.parser).iterator(self.fd, self.source.channels.items, self.source.offset)

	def readEpgDatFile(self, filename, deleteFile=False):
		if not hasattr(self.epgcache, 'load'):
			print("[EPGImport][readEpgDatFile]Cannot load EPG.DAT files on unpatched enigma. Need CrossEPG patch.")
			return

		unlink_if_exists(HDD_EPG_DAT)

		try:
			if filename.endswith('.gz'):
				print("[EPGImport][readEpgDatFile] Uncompressing", filename)
				import shutil
				fd = gzip.open(filename, 'rb')
				epgdat = open(HDD_EPG_DAT, 'wb')
				shutil.copyfileobj(fd, epgdat)
				del fd
				epgdat.close()
				del epgdat

			elif filename != HDD_EPG_DAT:
				symlink(filename, HDD_EPG_DAT)

			print("[EPGImport][readEpgDatFile] Importing", HDD_EPG_DAT)
			self.epgcache.load()

			if deleteFile:
				unlink_if_exists(filename)
		except Exception as e:
			print("[EPGImport][readEpgDatFile] Failed to import %s:" % filename, e)

	def fileno(self):
		if self.fd is not None:
			return self.fd.fileno()
		else:
			return

	def doThreadRead(self, filename):
		"""This is used on PLi with threading"""
		for data in self.createIterator(filename):
			if data is not None:
				self.eventCount += 1
				r, d = data
				if d[0] > self.longDescUntil:
					# Remove long description (save RAM memory)
					d = d[:4] + ('',) + d[5:]
				try:
					self.storage.importEvents(r, (d,))
				except Exception as e:
					print("[EPGImport][doThreadRead] ### importEvents exception:", e)

		print("[EPGImport][doThreadRead] ### thread is ready ### Events:", self.eventCount)
		if filename:
			try:
				unlink(filename)
			except Exception as e:
				print("[EPGImport][doThreadRead] warning: Could not remove '%s' intermediate" % filename, e)

		return

	def doRead(self):
		"""called from reactor to read some data"""
		try:
			data = next(self.iterator)
			if data is not None:
				self.eventCount += 1
				try:
					r, d = data
					if d[0] > self.longDescUntil:
						# Remove long description (save RAM memory)
						d = d[:4] + ('',) + d[5:]
					self.storage.importEvents(r, (d,))
				except Exception as e:
					print("[EPGImport][doRead] importEvents exception:", e)

		except StopIteration:
			self.nextImport()

		return

	def connectionLost(self, failure):
		"""called from reactor on lost connection"""
		# This happens because enigma calls us after removeReader
		print("[EPGImport][connectionLost]", failure)

	def closeReader(self):
		if self.fd is not None:
			reactor.removeReader(self)
			self.fd.close()
			self.fd = None
			self.iterator = None
		return

	def closeImport(self):
		self.closeReader()
		self.iterator = None
		self.source = None
		if hasattr(self.storage, 'epgfile'):
			needLoad = self.storage.epgfile
		else:
			needLoad = None

		self.storage = None

		if self.eventCount is not None:
			print("[EPGImport] imported %d events" % self.eventCount)
			reboot = False
			if self.eventCount:
				if needLoad:
					print("[EPGImport] no Oudeis patch, load(%s) required" % needLoad)
					reboot = True
					try:
						if hasattr(self.epgcache, 'load'):
							print("[EPGImport] attempt load() patch")
							if needLoad != HDD_EPG_DAT:
								symlink(needLoad, HDD_EPG_DAT)
							self.epgcache.load()
							reboot = False
							unlink_if_exists(needLoad)
					except Exception as e:
						print("[EPGImport] load() failed:", e)

				elif hasattr(self.epgcache, 'save'):
					self.epgcache.save()
			elif hasattr(self.epgcache, 'timeUpdated'):
				self.epgcache.timeUpdated()

			if self.onDone:
				self.onDone(reboot=reboot, epgfile=needLoad)

		self.eventCount = None
		print("[EPGImport] #### Finished ####")
		return

	def isImportRunning(self):
		return self.source is not None
