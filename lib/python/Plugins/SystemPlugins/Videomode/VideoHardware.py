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

	#modes["Composite"] = ["PAL", "NTSC"]
	#modes["Component"] = ["480i", "480p", "576i", "576p", "720p", "1080i", "1080p"]
	modes["HDMI"]  = ["480i", "480p", "576i", "576p", "720p", "1080i", "1080p"]
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
#		self.on_hotplug.append(self.createConfig)

		self.readPreferredModes()

		# take over old AVSwitch component :)
		from Components.AVSwitch import AVSwitch
#		config.av.colorformat.notifiers = [ ] 

		config.av.aspectratio.notifiers = [ ]
		config.av.tvsystem.notifiers = [ ]
		config.av.wss.notifiers = [ ]
		AVSwitch.setInput = self.AVSwitchSetInput

		config.av.analogmode = ConfigSelection(choices = {"PAL_BG": _("PAL"), "NTSC_M": _("NTSC")}, default="PAL_BG")
		config.av.componentout = ConfigSelection(choices = {" -scart_en 1 16 1": _("RGB (Scart)"), "": _("YPbPr (RCA)")}, default="")
		config.av.scartasr = ConfigSelection(choices = {"2": _("4:3"), "3": _("16:9")}, default="3")
		config.av.analogtmp = ConfigSelection(choices = {"": _("CVBS & RGB/YPbPr")}, default="")
		config.av.analogtmp1 = ConfigSelection(choices = {"": _(" ")}, default="")

		config.av.hdmipassthrough = ConfigSelection(choices = {" -hdmi_spdif c": _("Off"), " -hdmi_spdif cnd": _("On")}, default=" -hdmi_spdif c")
		config.av.ac3 = ConfigSelection(choices = {"0": _("PCM"), "1": _("RAW")}, default="0")
		config.av.ac3mode = ConfigSelection(choices = {"0": _("Line Out"), "1": _("RF")}, default="0")
		config.av.dts = ConfigSelection(choices = {"0": _("PCM"), "1": _("RAW")}, default="0")
		config.av.aac = ConfigSelection(choices = {"0": _("PCM"), "1": _("RAW")}, default="0")
		config.av.mpeg = ConfigSelection(choices = {"0": _("PCM"), "1": _("RAW")}, default="0")

		config.av.scalmode = ConfigSelection(choices = {"0": _("Full Screen"), "1": _("Pan&Scann"), "2": _("Letterbox"), "3": _("Pillarbox"), "4": _("Vertical Center")}, default="0")
		config.av.scalmodemc = ConfigSelection(choices = {"0": _("Full Screen"), "1": _("Pan&Scann"), "2": _("Letterbox"), "3": _("Pillarbox"), "4": _("Vertical Center")}, default="0")
		config.av.scart_slb = ConfigSelection(choices = {"2": _("4:3"), "3": _("16:9"),}, default="3")

		config.av.sdafd = ConfigSelection(choices = {"none": _("none"), "full": _("full"), "16x9top": _("16x9top"), "14x9top": _("14x9top"), "64x27": _("64x27"), "4x3": _("4x3"), "16x9": _("16x9"), "14x9": _("14x9"), "4x3_14x9": _("4x3_14x9"), "16x9_14x9": _("16x9_14x9"), "16x9_4x3": _("16x9_4x3")}, default="none")
		config.av.sdasp = ConfigSelection(choices = {"4 3": _("4:3"), "14 9": _("14:9"), "16 9": _("16:9"), "16 10": _("16:10")}, default="4 3")
		config.av.hdafd = ConfigSelection(choices = {"none": _("none"), "full": _("full"), "16x9top": _("16x9top"), "14x9top": _("14x9top"), "64x27": _("64x27"), "4x3": _("4x3"), "16x9": _("16x9"), "14x9": _("14x9"), "4x3_14x9": _("4x3_14x9"), "16x9_14x9": _("16x9_14x9"), "16x9_4x3": _("16x9_4x3")}, default="none")
		config.av.hdasp = ConfigSelection(choices = {"4 3": _("4:3"), "14 9": _("14:9"), "16 9": _("16:9"), "16 10": _("16:10")}, default="16 9")
		#config.av.spdif_options = ConfigSelection(choices = {"-SPDIF u": _("PCM"), "-SPDIF c": _("RAW")}, default="-SPDIF u")

		config.av.colorformat_hdmi = ConfigSelection(choices = {"yuv_601": _("YUV"), "yuv_709": _("YUV2"), "rgb_0_255": _("RGB"), "rgb_16_235": _("RGB2")}, default="yuv_601")
		config.av.deinterlace = ConfigSelection(choices = {"0": _("Off"), "1": _("1"), "2": _("2"), "3": _("3")}, default="0")
		config.av.colorformat_yuv = ConfigSelection(choices = {"yuv": _("YUV")}, default="yuv")
#		config.av.hdmi_audio_source = ConfigSelection(choices = {"pcm": _("PCM"), "spdif": _("SPDIF"), "8ch": _("8Ch"), "none": _("None")}, default="pcm")
		config.av.hdmi_audio_source = ConfigSelection(choices = {"pcm": _("PCM"), "spdif": _("SPDIF")}, default="pcm")

		config.av.scart_slb.addNotifier(self.UpdateScartSLB)
		config.av.scalmode.addNotifier(self.updateScalling)

		config.av.ac3.addNotifier(self.updateAudioMode)
		config.av.ac3mode.addNotifier(self.updateAudioMode)
		config.av.dts.addNotifier(self.updateAudioMode)
		config.av.aac.addNotifier(self.updateAudioMode)
		config.av.mpeg.addNotifier(self.updateAudioMode)

#		boxime = HardwareInfo().get_device_name()
#		if boxime != 'elite' and boxime != 'premium' and boxime != 'premium+' and boxime != 'ultra':
#      config.av.colorformat_hdmi.addNotifier(self.setHDMIColor)
#      config.av.colorformat_yuv.addNotifier(self.setYUVColor)
#      config.av.hdmi_audio_source.addNotifier(self.setHDMIAudioSource)
#      config.av.aspect.addNotifier(self.updateAspect)
#      config.av.wss.addNotifier(self.updateAspect)
#      config.av.policy_169.addNotifier(self.updateAspect)
#      config.av.policy_43.addNotifier(self.updateAspect)

		# until we have the hotplug poll socket
#		self.timer = eTimer()
#		self.timer.callback.append(self.readPreferredModes)
#		self.timer.start(1000)

#		config.av.colorformat.addNotifier(self.updateFastblank) 

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
			##telesat, enable this only with new driver
			#port = config.av.videoport.value
			#mode = config.av.videomode[port].value
			#rate = config.av.videorate[mode].value
			
			deinterlace = config.av.deinterlace.value
			analogmode = 'PAL_BG'
			rate_moderate = str(rate)[:-2]
			HDChip = ' '
			if str(rate) == '59Hz' or str(rate) == '60Hz': analogmode = 'NTSC_M'
			if str(rate) == '60Hz': rate_moderate = '59'
			hdmi_moderate = str(mode + rate_moderate)
			boxime = HardwareInfo().get_device_name()
			if boxime == 'elite': HDChip = ' -hdmi_chip SiI9030 0 14 15 100 0'
			if boxime == 'premium': HDChip = ' -hdmi_chip SiI9030 0 14 15 180 15'
			if boxime == 'ultra' or boxime == 'premium+': HDChip = ' -hdmi_chip SiI9134 0 14 15 100 0'
			if config.av.componentout.value == "":
				ScartSwitch = '0 ' + str(config.av.scart_slb.value)
				ComponentString = 'HDMI_' + hdmi_moderate + ' -asp '  + str(config.av.hdasp.value) + ' -afd '  + str(config.av.hdafd.value)
			else:
				ScartSwitch = '1 ' + str(config.av.scart_slb.value)
				ComponentString = str(analogmode) + ' -cav_mode rgb_scart -cs RGB' + ' -asp ' + str(config.av.sdasp.value) + ' -afd '  + str(config.av.sdafd.value)
			if config.av.videoport.value == 'DVI':
				hdmidvi = '0'
				hdmics = 'rgb_0_255'
			else:
				hdmidvi = '1'
				hdmics = 'rgb_16_235'
			VideoString = '-null -digital' + HDChip + ' -f HDMI_' + hdmi_moderate + ' -hdmi ' + hdmidvi + ' -asp '  + str(config.av.hdasp.value) + ' -afd '  + str(config.av.hdafd.value) + ' -cs ' + hdmics + ' -component -f ' + str(ComponentString) +  ' -analog -f ' + str(analogmode) + ' -asp ' + str(config.av.sdasp.value) + ' -afd '  + str(config.av.sdafd.value) + ' -audio_engine 0 -sf 48000' + str(config.av.hdmipassthrough.value)
			os.system('echo "' + str(VideoString) + '" > /etc/.vstring')
			os.system('echo "' + str(ScartSwitch) + '" > /proc/scart')
			print "  ==>>      setVideoMode "
			print str(VideoString)
			print str(ScartSwitch)
			##telesat
		except IOError:
			print "setting videomode failed."

#		self.updateAspect(None)
#		self.updateColor(port)

	def saveMode(self, port, mode, rate):
		print "saveMode", port, mode, rate
		config.av.videoport.value = port
		config.av.videoport.save()
		config.av.videomode[port].value = mode
		config.av.videomode[port].save()
		config.av.videorate[mode].value = rate
		config.av.videorate[mode].save()
#+++>
		import os
		#if mode == "PAL":
		#	com_cube = "/bin/cubefpctl --settvmode 0"
		#else:
		#	if mode == "NTSC":
		#		com_cube = "/bin/cubefpctl --settvmode 1"
		#	else:
		#		if mode == "1080i":
		#			if rate == "50Hz":
		#				com_cube = "/bin/cubefpctl --settvmode 4"
		#			else:
		#				com_cube = "/bin/cubefpctl --settvmode 5"
		#		else:
		#			if mode == "720p":
		#				if rate == "50Hz":
		#					com_cube = "/bin/cubefpctl --settvmode 2"
		#				else:
		#					com_cube = "/bin/cubefpctl --settvmode 3"
		#			else:
		#				com_cube = "/bin/cubefpctl --settvmode 0"
		#try:
		#	os.popen(com_cube)
		#except OSError:
		#	print "no memory"
#+++<

	def isPortAvailable(self, port):
		# fixme
		return True

	def isPortUsed(self, port):
#		if port == "HDMI":
#			self.readPreferredModes()
#			return len(self.modes_preferred) != 0
#		else:
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
		portlist = self.getPortList()

		# create list of available modes
		config.av.videoport = ConfigSelection(choices = [(port, _(port)) for port in portlist])
		config.av.videomode = ConfigSubDict()
		config.av.videorate = ConfigSubDict()

		for port in portlist:
			modes = self.getModeList(port)
			if len(modes):
				config.av.videomode[port] = ConfigSelection(choices = [mode for (mode, rates) in modes])
			for (mode, rates) in modes:
				config.av.videorate[mode] = ConfigSelection(choices = rates)

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
			#open("/etc/.dolbydigital", "w").close()
			print "OK "
		except IOError:
			print "couldn't write available AudioMode."


#	def updateAspect(self, cfgelement):
#		# determine aspect = {any,4:3,16:9,16:10}
#		# determine policy = {bestfit,letterbox,panscan,nonlinear}
#
#		# based on;
#		#   config.av.videoport.value: current video output device
#		#     Composite: 
#		#   config.av.aspect:
#		#     4_3:            use policy_169
#		#     16_9,16_10:     use policy_43
#		#     auto            always "bestfit"
#		#   config.av.policy_169
#		#     letterbox       use letterbox
#		#     panscan         use panscan
#		#     scale           use bestfit
#		#   config.av.policy_43
#		#     pillarbox       use panscan
#		#     panscan         use letterbox  ("panscan" is just a bad term, it's inverse-panscan)
#		#     nonlinear       use nonlinear
#		#     scale           use bestfit
#
#		port = config.av.videoport.value
#		if port not in config.av.videomode:
#			print "current port not available, not setting videomode"
#			return
#		mode = config.av.videomode[port].value
#
#		force_widescreen = self.isWidescreenMode(port, mode)
#
#		is_widescreen = force_widescreen or config.av.aspect.value in ["16_9", "16_10"]
#		is_auto = config.av.aspect.value == "auto"
#
#		if is_widescreen:
#			if force_widescreen:
#				aspect = "16:9"
#			else:
#				aspect = {"16_9": "16:9", "16_10": "16:10"}[config.av.aspect.value]
#			policy = {"pillarbox": "letterbox", "panscan": "panscan", "nonlinear": "nonlinear", "scale": "bestfit"}[config.av.policy_43.value]
#		elif is_auto:
#			aspect = "any"
#			policy = "bestfit"
#		else:
#			aspect = "4:3"
#			policy = {"letterbox": "letterbox", "panscan": "panscan", "scale": "bestfit"}[config.av.policy_169.value]
#
#		if not config.av.wss.value:
#			wss = "auto(4:3_off)"
#		else:
#			wss = "auto"
#
#		#print "-> setting aspect, policy, wss", aspect, policy, wss
#		#open("/proc/stb/video/aspect", "w").write(aspect)
#		#open("/proc/stb/video/policy", "w").write(policy)
#		#open("/proc/stb/denc/0/wss", "w").write(wss)
#		#self.updateSlowblank()
#		#self.updateFastblank()

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
		#open("/proc/stb/avs/0/fb", "w").write(fb)

#	def setHDMIColor(self, configElement):
#		map = {"yuv_601": 0, "yuv_709": 1, "rgb_0_255": 2, "rgb_16_235": 3}
#		open("/proc/stb/avs/0/colorformat", "w").write(configElement.value)

#	def setYUVColor(self, configElement):
#		map = {"yuv": 0}
#		open("/proc/stb/avs/0/colorformat", "w").write(configElement.value)

	def setHDMIAudioSource(self, configElement):
		pass


#	def updateColor(self, port):
#		print "updateColor: ", port
#		if port == "HDMI":
#			self.setHDMIColor(config.av.colorformat_hdmi)
#		elif port == "Component":
#			self.setYUVColor(config.av.colorformat_yuv)
#		elif port == "Composite":
#			map = {"cvbs": 0, "rgb": 1, "svideo": 2, "yuv": 3}
#			from enigma import eAVSwitch
#			eAVSwitch.getInstance().setColorFormat(map[config.av.colorformat.value])


config.av.edid_override = ConfigYesNo(default = False)
video_hw = VideoHardware()
video_hw.setConfiguredMode()
