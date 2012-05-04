from Screens.Screen import Screen
from Plugins.Plugin import PluginDescriptor
from Components.SystemInfo import SystemInfo
from Components.ConfigList import ConfigListScreen
from Components.config import getConfigListEntry, config, ConfigBoolean, ConfigNothing, ConfigSlider
from Components.Sources.StaticText import StaticText

from VideoHardware import video_hw
from Tools.HardwareInfo import HardwareInfo

config.misc.videowizardenabled = ConfigBoolean(default = True)

class VideoSetup(Screen, ConfigListScreen):

	def __init__(self, session, hw):
		Screen.__init__(self, session)
		# for the skin: first try VideoSetup, then Setup, this allows individual skinning
		self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
		self.skinName = ["VideoSetup", "Setup" ]
		self.setup_title = _("A/V Settings")
		self.hw = hw
		self.onChangedEntry = [ ]

		# handle hotplug by re-creating setup
		self.onShow.append(self.startHotplug)
		self.onHide.append(self.stopHotplug)

		self.list = [ ]
		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changedEntry)

		from Components.ActionMap import ActionMap
		self["actions"] = ActionMap(["SetupActions"], 
			{
				"cancel": self.keyCancel,
				"save": self.apply,
			}, -2)

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))

		self.createSetup()
		self.grabLastGoodMode()
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(self.setup_title)

	def startHotplug(self):
		self.hw.on_hotplug.append(self.createSetup)

	def stopHotplug(self):
		self.hw.on_hotplug.remove(self.createSetup)

	def createSetup(self):
		level = config.usage.setup_level.index

		self.list = [
			getConfigListEntry(_("Digital Video Output"), config.av.videoport)
		]

		# if we have modes for this port:
		if config.av.videoport.value in config.av.videomode:
			# add mode- and rate-selection:
			self.list.append(getConfigListEntry(_(" Mode"), config.av.videomode[config.av.videoport.value]))
			if config.av.videomode[config.av.videoport.value].value == 'PC':
				self.list.append(getConfigListEntry(_("Resolution"), config.av.videorate[config.av.videomode[config.av.videoport.value].value]))
			else:
				self.list.append(getConfigListEntry(_(" Refresh Rate (Analog out: 50Hz = PAL , 60Hz = NTSC)"), config.av.videorate[config.av.videomode[config.av.videoport.value].value]))

		port = config.av.videoport.value
		if port not in config.av.videomode:
			mode = None
		else:
			mode = config.av.videomode[port].value

		# some modes (720p, 1080i) are always widescreen. Don't let the user select something here, "auto" is not what he wants.
		force_wide = self.hw.isWidescreenMode(port, mode)

    # test
		self.list.append(getConfigListEntry(_(" AFD (Digital Out)"), config.av.hdafd))
		self.list.append(getConfigListEntry(_(" Aspect Ratio (Digital Out)"), config.av.hdasp))
		self.list.append(getConfigListEntry(_(" "), config.av.analogtmp1))
		self.list.append(getConfigListEntry(_("Analog Video Output: Composite & Component"), config.av.analogtmp))
		self.list.append(getConfigListEntry(_(" Component Out"), config.av.componentout))
		self.list.append(getConfigListEntry(_(" AFD (Analog Output)"), config.av.sdafd))
		self.list.append(getConfigListEntry(_(" Aspect Ratio (Analog Output)"), config.av.sdasp))
		boxime = HardwareInfo().get_device_name()
		self.list.append(getConfigListEntry(_(" SCART SLB (Slow Blanking)"), config.av.scart_slb))
		self.list.append(getConfigListEntry(_(" "), config.av.analogtmp1))

		self.list.append(getConfigListEntry(_(" input video scan mode"), config.av.input_video_scan_mod))
		self.list.append(getConfigListEntry(_(" interlaced progressive algo."), config.av.interlaced_prog_algo))
		self.list.append(getConfigListEntry(_(" "), config.av.analogtmp1))

		self.list.append(getConfigListEntry(_("Scaling Mode"), config.av.scalmode))
		self.list.append(getConfigListEntry(_("Scaling Mode MediaCenter"), config.av.scalmodemc))
		#self.list.append(getConfigListEntry(_("Deinterlace"), config.av.deinterlace))
		self.list.append(getConfigListEntry(_(" "), config.av.analogtmp1))

		#self.list.append(getConfigListEntry(_("SPDIF conf. option"), config.av.spdif_options))
		self.list.append(getConfigListEntry(_("HDMI passthrough"), config.av.hdmipassthrough))
		self.list.append(getConfigListEntry(_("AC3"), config.av.ac3))
		self.list.append(getConfigListEntry(_("AC3 mode"), config.av.ac3mode))
		self.list.append(getConfigListEntry(_("DTS"), config.av.dts))
		self.list.append(getConfigListEntry(_("AAC"), config.av.aac))
		self.list.append(getConfigListEntry(_("MPEG"), config.av.mpeg))




		if level >= 1:
			if SystemInfo["CanDownmixAC3"]:
				self.list.append(getConfigListEntry(_("AC3 downmix"), config.av.downmix_ac3))

		if SystemInfo["CanChangeOsdAlpha"]:
			self.list.append(getConfigListEntry(_("OSD visibility"), config.av.osd_alpha))

		if not isinstance(config.av.scaler_sharpness, ConfigNothing):
			self.list.append(getConfigListEntry(_("Scaler sharpness"), config.av.scaler_sharpness))

		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.createSetup()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.createSetup()

		
		
	def confirm(self, confirmed):
		if not confirmed:
			config.av.videoport.value = self.last_good[0]
			config.av.videomode[self.last_good[0]].value = self.last_good[1]
			config.av.videorate[self.last_good[1]].value = self.last_good[2]
			self.session.nav.playService(None)
			self.hw.setMode(*self.last_good)
			self.session.nav.playService(self.oldService)
			config.av.analogmode.value = self.last_good1[0]
			config.av.componentout.value = self.last_good1[1]
			config.av.scartasr.value = self.last_good1[2]
			config.av.deinterlace.value = self.last_good1[3]
			config.av.hdmipassthrough.value = self.last_good1[4]
			config.av.sdafd.value = self.last_good2[0]
			config.av.sdasp.value = self.last_good2[1]
			config.av.hdafd.value = self.last_good2[2]
			config.av.hdasp.value = self.last_good2[3]
		else:
			self.keySave()			

	def grabLastGoodMode(self):
		port = config.av.videoport.value
		mode = config.av.videomode[port].value
		rate = config.av.videorate[mode].value
		analogmode = config.av.analogmode.value
		componentout = config.av.componentout.value
		scartasr = config.av.scartasr.value
		deinterlace = config.av.deinterlace.value
		sdafd = config.av.sdafd.value
		sdasp = config.av.sdasp.value
		hdafd = config.av.hdafd.value
		hdasp = config.av.hdasp.value
		hdmipassthrough = config.av.hdmipassthrough.value
		self.last_good = (port, mode, rate)
		self.last_good1 = (analogmode, componentout, scartasr, deinterlace, hdmipassthrough)
		self.last_good2 = (sdafd, sdasp, hdafd, hdasp)

	def apply(self):
		port = config.av.videoport.value
		mode = config.av.videomode[port].value
		rate = config.av.videorate[mode].value
		analogmode = config.av.analogmode.value
		componentout = config.av.componentout.value
		scartasr = config.av.scartasr.value
		deinterlace = config.av.deinterlace.value
		hdmipassthrough = config.av.hdmipassthrough.value
		sdafd = config.av.sdafd.value
		sdasp = config.av.sdasp.value
		hdafd = config.av.hdafd.value
		hdasp = config.av.hdasp.value
		#if (port, mode, rate) != self.last_good:
		if ((port, mode, rate) != self.last_good) or ((analogmode, componentout, scartasr, deinterlace, hdmipassthrough) != self.last_good1) or ((sdafd, sdasp, hdafd, hdasp) != self.last_good2):
			self.session.nav.playService(None)
			self.hw.setMode(port, mode, rate)
			self.session.nav.playService(self.oldService)
			from Screens.MessageBox import MessageBox
			self.session.openWithCallback(self.confirm, MessageBox, _("Is this videomode ok?"), MessageBox.TYPE_YESNO, timeout = 20, default = False)
		else:
			self.keySave()

	# for summary:
	def changedEntry(self):
		for x in self.onChangedEntry:
			x()

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		from Screens.Setup import SetupSummary
		return SetupSummary

class VideomodeHotplug:
	def __init__(self, hw):
		self.hw = hw

	def start(self):
		self.hw.on_hotplug.append(self.hotplug)

	def stop(self):
		self.hw.on_hotplug.remove(self.hotplug)

	def hotplug(self, what):
		print "hotplug detected on port '%s'" % (what)
		port = config.av.videoport.value
		mode = config.av.videomode[port].value
		rate = config.av.videorate[mode].value

		if not self.hw.isModeAvailable(port, mode, rate):
			print "mode %s/%s/%s went away!" % (port, mode, rate)
			modelist = self.hw.getModeList(port)
			if not len(modelist):
				print "sorry, no other mode is available (unplug?). Doing nothing."
				return
			mode = modelist[0][0]
			rate = modelist[0][1]
			print "setting %s/%s/%s" % (port, mode, rate)
			self.session.nav.playService(None)
			self.hw.setMode(port, mode, rate)
			self.session.nav.playService(self.oldService)

hotplug = None

def startHotplug():
	global hotplug, video_hw
	hotplug = VideomodeHotplug(video_hw)
	hotplug.start()

def stopHotplug():
	global hotplug
	hotplug.stop()


def autostart(reason, session = None, **kwargs):
	if session is not None:
		global my_global_session
		my_global_session = session
		return

	if reason == 0:
		startHotplug()
	elif reason == 1:
		stopHotplug()

def videoSetupMain(session, **kwargs):
	session.open(VideoSetup, video_hw)

def startSetup(menuid):
	if menuid != "system": 
		return [ ]

	return [(_("A/V Settings"), videoSetupMain, "av_setup", 40)]

def VideoWizard(*args, **kwargs):
	from VideoWizard import VideoWizard
	return VideoWizard(*args, **kwargs)

def Plugins(**kwargs):
	list = [
#		PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc = autostart),
		PluginDescriptor(name=_("Video Setup"), description=_("Advanced Video Setup"), where = PluginDescriptor.WHERE_MENU, fnc=startSetup) 
	]
	if config.misc.videowizardenabled.value:
		list.append(PluginDescriptor(name=_("Video Wizard"), where = PluginDescriptor.WHERE_WIZARD, fnc=(0, VideoWizard)))
	return list
