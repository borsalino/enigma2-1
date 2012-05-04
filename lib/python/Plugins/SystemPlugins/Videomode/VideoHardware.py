from enigma import eTimer
from Components.config import config, ConfigSelection, ConfigSubDict, ConfigYesNo, ConfigSelectionNumber

from Tools.CList import CList
from Tools.HardwareInfo import HardwareInfo

# The "VideoHardware" is the interface to /proc/stb/video.
# It generates hotplug events, and gives you the list of 
# available and preferred modes, as well as handling the currently
# selected mode. No other strict checking is done.
class VideoHardware:
	rates = { } # high-level, use selectable modes.

	modes = { }  # a list of (high-level) modes for a certain port.
	modesw = { }  # a list of (high-level) modes for a certain port.

	rates["PAL"] =			{ "50Hz":	{ 50: "PAL_BG" } }

	rates["NTSC"] =			{ "60Hz": 	{ 60: "NTSC_M" } }

	rates["480i"] =			{ "60Hz": 	{ 59: "480i59" } }

	rates["480p"] =			{ "60Hz": 	{ 59: "480p59" } }
	
	rates["576i"] =			{ "50Hz": 	{ 50: "576i50" } }
 
	rates["576p"] =			{ "50Hz": 	{ 50: "576p50" } }

	rates["720p"] =			{ "50Hz": 	{ 50: "720p50" },
					  "60Hz": 	{ 59: "720p59" } }

	rates["1080i"] =		{ "50Hz":		{ 50: "1080i50" },
					  "60Hz":		{ 59: "1080i59" } }

	rates["1080p"] =		{ "50Hz":		{ 50: "1080p50" },
					  "60Hz":		{ 59: "1080p59" } }

	boxime = HardwareInfo().get_device_name()
	modes["HDMI"]  = ["480i", "480p", "576i", "576p", "720p", "1080i", "1080p"]
	if boxime == 'premium':
		modes["DVI"]  = ["480i", "480p", "576i", "576p", "720p", "1080i", "1080p"]

	widescreen_modes = set(["480i", "480p", "576i", "576p", "720p", "1080i", "1080p"])

	def __init__(self):
		self.last_modes_preferred =  [ ]
		self.on_hotplug = CList()
		self.standby = False
		self.current_mode = None
		self.current_port = None

		self.readAvailableModes()

		self.createConfig()

		self.readPreferredModes()

		# take over old AVSwitch component :)
		from Components.AVSwitch import AVSwitch

		config.av.aspectratio.notifiers = [ ]
		config.av.tvsystem.notifiers = [ ]
		config.av.wss.notifiers = [ ]
		AVSwitch.setInput = self.AVSwitchSetInput

		config.av.analogmode = ConfigSelection(choices = {"PAL_BG": _("PAL"), "NTSC_M": _("NTSC")}, default="PAL_BG")
		config.av.componentout = ConfigSelection(choices = {" -scart_en 1 16 1": _("RGB (Scart)"), "": _("YPbPr (RCA)")}, default="")
		config.av.scartasr = ConfigSelection(choices = {"2": _("4:3"), "3": _("16:9")}, default="3")
		config.av.analogtmp = ConfigSelection(choices = {"": _("CVBS & RGB/YPbPr")}, default="")
		config.av.analogtmp1 = ConfigSelection(choices = {"": _(" ")}, default="")

		config.av.hdmipassthrough = ConfigSelection(choices = {"-hdmi_spdif c": _("Off"), "-hdmi_spdif cnd": _("On")}, default="-hdmi_spdif c")
		config.av.ac3 = ConfigSelection(choices = {"0": _("PCM"), "1": _("RAW")}, default="0")
		config.av.ac3mode = ConfigSelection(choices = {"0": _("Line Out"), "1": _("RF")}, default="0")
		config.av.dts = ConfigSelection(choices = {"0": _("PCM"), "1": _("RAW")}, default="0")
		config.av.aac = ConfigSelection(choices = {"0": _("PCM"), "1": _("RAW")}, default="0")
		config.av.mpeg = ConfigSelection(choices = {"0": _("PCM"), "1": _("RAW")}, default="0")

		config.av.scalmode = ConfigSelection(choices = {"0": _("Full Screen"), "1": _("Pan&Scann"), "2": _("Letterbox"), "3": _("Pillarbox"), "4": _("Vertical Center")}, default="0")
		config.av.scalmodemc = ConfigSelection(choices = {"0": _("Full Screen"), "1": _("Pan&Scann"), "2": _("Letterbox"), "3": _("Pillarbox"), "4": _("Vertical Center")}, default="0")
		config.av.scart_slb = ConfigSelection(choices = {"2": _("4:3"), "3": _("16:9"),}, default="3")
		config.av.input_video_scan_mod = ConfigSelection(choices = {"1": _("default (EMhwlibScanMode_Source)"), "2": _("frame (EMhwlibScanMode_Progressive)"), "3": _("top (EMhwlibScanMode_Interlaced_TopFieldFirst)"), "4": _("bot (EMhwlibScanMode_Interlaced_BotFieldFirst)")}, default="1")
		config.av.interlaced_prog_algo = ConfigSelection(choices = {"1": _("default (Algorithm_Using_Decoder_Specification)"), "2": _("mpeg2_prog_seq (Algorithm_Using_MPEG2_Progressive_Seq)"), "3": _("mpeg2_menu_prog (Algorithm_Using_MPEG2_Menu_Progressive)")}, default="1")

		config.av.sdafd = ConfigSelection(choices = {"none": _("none"), "full": _("full"), "16x9top": _("16x9top"), "14x9top": _("14x9top"), "64x27": _("64x27"), "4x3": _("4x3"), "16x9": _("16x9"), "14x9": _("14x9"), "4x3_14x9": _("4x3_14x9"), "16x9_14x9": _("16x9_14x9"), "16x9_4x3": _("16x9_4x3")}, default="none")
		config.av.sdasp = ConfigSelection(choices = {"4 3": _("4:3"), "14 9": _("14:9"), "16 9": _("16:9"), "16 10": _("16:10")}, default="4 3")
		config.av.hdafd = ConfigSelection(choices = {"none": _("none"), "full": _("full"), "16x9top": _("16x9top"), "14x9top": _("14x9top"), "64x27": _("64x27"), "4x3": _("4x3"), "16x9": _("16x9"), "14x9": _("14x9"), "4x3_14x9": _("4x3_14x9"), "16x9_14x9": _("16x9_14x9"), "16x9_4x3": _("16x9_4x3")}, default="none")
		config.av.hdasp = ConfigSelection(choices = {"4 3": _("4:3"), "14 9": _("14:9"), "16 9": _("16:9"), "16 10": _("16:10")}, default="16 9")

		config.av.colorformat_hdmi = ConfigSelection(choices = {"yuv_601": _("YUV"), "yuv_709": _("YUV2"), "rgb_0_255": _("RGB"), "rgb_16_235": _("RGB2")}, default="yuv_601")
		config.av.deinterlace = ConfigSelection(choices = {"0": _("Off"), "1": _("1"), "2": _("2"), "3": _("3")}, default="0")
		config.av.colorformat_yuv = ConfigSelection(choices = {"yuv": _("YUV")}, default="yuv")
		config.av.hdmi_audio_source = ConfigSelection(choices = {"pcm": _("PCM"), "spdif": _("SPDIF")}, default="pcm")

		config.av.scart_slb.addNotifier(self.UpdateScartSLB)
		config.av.scalmode.addNotifier(self.updateScalling)
		config.av.input_video_scan_mod.addNotifier(self.updateIvsm)
		config.av.interlaced_prog_algo.addNotifier(self.updateIpa)

		config.av.ac3.addNotifier(self.updateAudioMode)
		config.av.ac3mode.addNotifier(self.updateAudioMode)
		config.av.dts.addNotifier(self.updateAudioMode)
		config.av.aac.addNotifier(self.updateAudioMode)
		config.av.mpeg.addNotifier(self.updateAudioMode)

	def AVSwitchSetInput(self, mode):
		self.standby = mode == "Composite"
		self.updateStandby()

	def readAvailableModes(self):
		self.modes_available = [ ] 
		print self.modes_available

	def readPreferredModes(self):
		self.modes_preferred = []

		if self.modes_preferred != self.last_modes_preferred:
			self.last_modes_preferred = self.modes_preferred
			print "hotplug on hdmi"
			self.on_hotplug("HDMI") # must be DVI

	# check if a high-level mode with a given rate is available.
	def isModeAvailable(self, port, mode, rate):
		rate = self.rates[mode][rate]
		for mode in rate.values():
			pass
		return True

	def isWidescreenMode(self, port, mode):
		return mode in self.widescreen_modes

	def setMode(self, port, mode, rate, force = None):
		print "setMode - port:", port, "mode:", mode, "rate:", rate
		# we can ignore "port"
		self.current_mode = mode
		self.current_port = port
		modes = self.rates[mode][rate]
		import os

		try:
			deinterlace = config.av.deinterlace.value
			analogmode = 'PAL_BG'
			rate_moderate = str(rate)[:-2]
			if str(rate) == '59Hz' or str(rate) == '60Hz': analogmode = 'NTSC_M'
			if str(rate) == '60Hz': rate_moderate = '59'
			hdmi_moderate = str(mode + rate_moderate)
			if config.av.componentout.value == "":
				ScartSwitch = '0 ' + str(config.av.scart_slb.value)
				comp_moderate = hdmi_moderate
				if hdmi_moderate == '576i50': comp_moderate = 'PAL_BG'
				if hdmi_moderate == '480i59': comp_moderate = 'NTSC_M'
				ComponentString = comp_moderate + ' -asp '  + str(config.av.hdasp.value) + ' -afd '  + str(config.av.hdafd.value)
			else:
				ScartSwitch = '1 ' + str(config.av.scart_slb.value)
				ComponentString = str(analogmode) + ' -cav_mode rgb_scart -cs RGB' + ' -asp ' + str(config.av.sdasp.value) + ' -afd '  + str(config.av.sdafd.value)
			if config.av.videoport.value == 'DVI':
				hdmidvi = '0'
				hdmics = 'rgb_0_255'
			else:
				hdmidvi = '1'
				hdmics = 'rgb_16_235'
			
			boxime = HardwareInfo().get_device_name()
			tmp_model = ''
			if boxime == 'me': tmp_model = ' &'
			
			VideoString = '-f HDMI_' + hdmi_moderate + ' -cs ' + str(hdmics) + ' -asp '  + str(config.av.hdasp.value) + ' -afd '  + str(config.av.hdafd.value) + ' -component -f ' + str(ComponentString) +  ' -analog -f ' + str(analogmode) + ' -asp ' + str(config.av.sdasp.value) + ' -afd '  + str(config.av.sdafd.value) + ' -audio_engine 0 -sf 48000 ' + str(config.av.hdmipassthrough.value) + tmp_model
			os.system('echo "' + str(VideoString) + '" > /etc/.vstring')
			
			hdmidvistr = ''
			if boxime == 'premium': hdmidvistr = ' -hdmi ' + hdmidvi
			VideoStringold = '-null -digital -f HDMI_' + hdmi_moderate + hdmidvistr + ' -cs ' + hdmics + ' -asp '  + str(config.av.hdasp.value) + ' -afd '  + str(config.av.hdafd.value) + ' -component -f ' + str(ComponentString) +  ' -analog -f ' + str(analogmode) + ' -asp ' + str(config.av.sdasp.value) + ' -afd '  + str(config.av.sdafd.value) + ' -audio_engine 0 -sf 48000 ' + str(config.av.hdmipassthrough.value)
			os.system('echo "' + str(VideoStringold) + '" > /etc/.vstring2')
			os.system('echo "' + str(ScartSwitch) + '" > /proc/scart')
			print "  ==>>      setVideoMode "
			print str(VideoString)
			print str(ScartSwitch)
		except IOError:
			print "setting videomode failed."

	def saveMode(self, port, mode, rate):
		print "saveMode", port, mode, rate
		config.av.videoport.value = port
		config.av.videoport.save()
		config.av.videomode[port].value = mode
		config.av.videomode[port].save()
		config.av.videorate[mode].value = rate
		config.av.videorate[mode].save()

	def isPortAvailable(self, port):
		# fixme
		return True

	def isPortUsed(self, port):
		return True

	def getPortList(self):
		return [port for port in self.modes if self.isPortAvailable(port)]

	# get a list with all modes, with all rates, for a given port.
	def getModeList(self, port):
		print "getModeList for port", port
		res = [ ]
		for mode in self.modes[port]:
			# list all rates which are completely valid
			rates = [ ]
			for rate in self.rates[mode]:
				if self.isModeAvailable(port, mode, rate):
					rates.append(rate)
					rates.sort()

			# if at least one rate is ok, add this mode
			if len(rates):
				res.append( (mode, rates) )
		return res

	def createConfig(self, *args):
		# create list of output ports
		print "DOING THIS"
		portlist = self.getPortList()

		# create list of available modes
		config.av.videoport = ConfigSelection(choices = [(port, _(port)) for port in portlist], default="HDMI")
		config.av.videomode = ConfigSubDict()
		config.av.videorate = ConfigSubDict()

		for port in portlist:
			modes = self.getModeList(port)
			if len(modes):
				config.av.videomode[port] = ConfigSelection(choices = [mode for (mode, rates) in modes], default="720p")
			for (mode, rates) in modes:
				config.av.videorate[mode] = ConfigSelection(choices = rates, default="50Hz")

	def setConfiguredMode(self):
		port = config.av.videoport.value
		if port not in config.av.videomode:
			print "current port not available, not setting videomode"
			return

		mode = config.av.videomode[port].value

		if mode not in config.av.videorate:
			print "current mode not available, not setting videomode"
			return

		rate = config.av.videorate[mode].value
		self.setMode(port, mode, rate)
	
	def UpdateScartSLB(self, cfgelement):
		if config.av.componentout.value == "":
			ScartSwitch = '0 ' + str(config.av.scart_slb.value)
		else:
			ScartSwitch = '1 ' + str(config.av.scart_slb.value)
		print "  ==>>      Update SCART Slow Blanking "
		print str(config.av.scart_slb.value)
		try:
			open("/proc/scart", "w").write(str(ScartSwitch))
			open("/proc/scart", "w").close()
		except IOError:
			print "couldn't write available SCART Slow Blanking."
	
	def updateScalling(self, cfgelement):
		SString = str(config.av.scalmode.value)
		print "  ==>>      updateScalling "
		print str(SString)
		try:
			open("/proc/scalingmode", "w").write(str(SString))
			open("/proc/scalingmode", "w").close()
		except IOError:
			print "couldn't write available Scalling."
	
	def updateAudioMode(self, cfgelement):
		print "  ==>>      updateAudioMode "
		try:
			open("/proc/codecs/ac3", "w").write(str(config.av.ac3.value))
			open("/proc/codecs/ac3mode", "w").write(str(config.av.ac3mode.value))
			open("/proc/codecs/dts", "w").write(str(config.av.dts.value))
			open("/proc/codecs/aac", "w").write(str(config.av.aac.value))
			open("/proc/codecs/mpeg", "w").write(str(config.av.mpeg.value))
			print "OK "
		except IOError:
			print "couldn't write available AudioMode."
	
	def updateIvsm(self, cfgelement):
		print "  ==>>      input video scan mode "
		print str(config.av.input_video_scan_mod.value)
		try:
			open("/proc/input_scan_mode", "w").write(str(config.av.input_video_scan_mod.value))
		except IOError:
			print "couldn't write input video scan mode."
	
	def updateIpa(self, cfgelement):
		print "  ==>>      interlaced progressive algorithm "
		print str(config.av.interlaced_prog_algo.value)
		try:
			open("/proc/interlaced_algo", "w").write(str(config.av.interlaced_prog_algo.value))
		except IOError:
			print "couldn't write interlaced progressive algorithm."
	
	def updateSlowblank(self):
		if self.standby:
			from Components.SystemInfo import SystemInfo
			if SystemInfo["ScartSwitch"]:
				input = "Composite"
				sb = "vcr"
			else:
				input = "off"
				sb = "0"
		else:
			input = "encoder"
			sb = "auto"

		open("/proc/stb/avs/0/sb", "w").write(sb)
		open("/proc/stb/avs/0/input", "w").write(input)

	def updateStandby(self):
		self.updateSlowblank()
		#self.updateFastblank()

	def updateFastblank(self, *args):
		if self.standby:
			from Components.SystemInfo import SystemInfo
			if SystemInfo["ScartSwitch"]:
				fb = "vcr"
			else:
				fb = "low"
		else:
			if self.current_port == "Composite" and config.av.colorformat.value == "rgb":
				fb = "high"
			else:
				fb = "low"
	
	def setHDMIAudioSource(self, configElement):
		pass

config.av.edid_override = ConfigYesNo(default = False)
video_hw = VideoHardware()
video_hw.setConfiguredMode()
