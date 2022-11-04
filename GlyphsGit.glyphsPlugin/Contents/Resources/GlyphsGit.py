#!/usr/bin/env python
# encoding: utf-8

from __future__ import print_function
import objc
import traceback
from AppKit import NSBundle, NSApp, NSNotificationCenter, NSMenuItem, NSLog
import sys, os, re
from distutils import spawn
import random
import GlyphsGitList


MainBundle = NSBundle.mainBundle()
path = MainBundle.bundlePath() + "/Contents/Scripts"
if not path in sys.path:
	sys.path.append(path)

import GlyphsApp
from GlyphsApp.plugins import GeneralPlugin

Glyphs = GlyphsApp.Glyphs
GlyphsPluginProtocol = objc.protocolNamed("GlyphsPlugin")

class Alert(object):
	def __init__(self, messageText):
		super(Alert, self).__init__()
		self.messageText = messageText
		self.informativeText = ""
		self.buttons = []

	def displayAlert(self):
		NSApp.activateIgnoringOtherApps_(True)
		self.buttonPressed = alert.runModal()

class glyphsGit (GeneralPlugin):
	sheetLabel = objc.IBOutlet()
	_view = objc.IBOutlet()
	sheetTextarea = objc.IBOutlet()
	sheetButton = objc.IBOutlet()
	_sheetPanel = objc.IBOutlet()
	sheetPanel = objc.ivar()
	objc.synthesize("sheetPanel")
	oldCwd = ""

	def loadPlugin(self):
		"""
		You can add an observer like in the example.
		Do all initializing here.
		"""
		try:
			NSBundle.loadNibNamed_owner_("GlyphsGitDialog", self)
			selector = objc.selector(self.documentWasSaved_, signature=b"v@:@")
			NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(self, selector, "GSDocumentWasSavedSuccessfully", None)

			mainMenu = NSApp.mainMenu()
			s = objc.selector(self.showRevisions_, signature=b'v@:')
			self.revisionMenuItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("View revision history", s, "")
			self.revisionMenuItem.setTarget_(self)
			index = 0
			numberOfSeperators = 0
			for menuItem in mainMenu.itemAtIndex_(1).submenu().itemArray():
				if menuItem.isSeparatorItem():
					numberOfSeperators += 1
				if numberOfSeperators == 2:
					break
				index += 1;
			mainMenu.itemAtIndex_(1).submenu().insertItem_atIndex_(self.revisionMenuItem, index)
			return None
		except Exception as err:
			self.logToConsole("init: %s" % traceback.format_exc())

	def __del__(self):
		"""
		Remove all observers you added in init().
		"""
		try:
			NSNotificationCenter.defaultCenter().removeObserver_(self)
		except Exception as e:
			self.logToConsole("__del__: %s" % str(e))

	def interfaceVersion(self):
		"""
		Distinguishes the API version the plugin was built for. 
		Return 1.
		"""
		try:
			return 1
		except Exception as e:
			self.logToConsole("interfaceVersion: %s" % str(e))

	def documentWasSaved_(self, sender):
		"""
		Called when the font is saved
		assuming GSDocumentWasSavedSuccessfully was added to the observer
		"""
		try:
			self.oldCwd = os.getcwd()
			p = Glyphs.font.filepath
			os.chdir(os.path.dirname(p))
			if not os.path.isdir("./git"):
				self._runGit(["init"])
			try:
				self._runGit(["checkout", "master"]) # ???
			except Exception as e:
				print(e) # It doesn't matter if this fails
			self._runGit(["add", os.path.basename(p) ])
			self.setupStupidMessage()
			NSApp.beginSheet_modalForWindow_modalDelegate_didEndSelector_contextInfo_(
				self.sheetPanel(),
				NSApp.mainWindow(),
				self,
				self.alertDidEnd_returnCode_contextInfo_,
				None
			)
		except Exception as e:
			self.logToConsole("documentWasSaved: %s" % str(e))

	def setupStupidMessage(self):
		stupidMessages = [
			"Pushed some points around.",
			"Reticulated splines.",
			"Moved some points; stared at them a bit; moved them back."
			]
		self.sheetTextarea.setStringValue_(random.choice(stupidMessages))

	@objc.IBAction
	def commitPushed_ (self, sender):
		try:
			self._runGit(["commit", "-m", self.sheetTextarea.stringValue() ])
			os.chdir(self.oldCwd)
		except Exception as e:
			self.logToConsole("Git failed (probably no change since last commit): %s" % str(e))
		try:
			NSApp.endSheet_(self.sheetPanel())
			self.sheetPanel().orderOut_(self)
		except Exception as e:
			self.logToConsole("buttonPushed_: %s" % str(e))

	@objc.IBAction
	def canelPushed_ (self, sender):
		try:
			NSApp.endSheet_(self.sheetPanel())
			self.sheetPanel().orderOut_(self)
		except Exception as e:
			self.logToConsole("buttonPushed_: %s" % str(e))

	@objc.python_method
	def alert(self, message="Default Message", info_text="", buttons=["OK"]):
		alert = NSAlert.alloc().init()
		alert.setMessageText_(message)
		alert.setInformativeText_(info_text)
		alert.setAlertStyle_(NSInformationalAlertStyle)
		for button in buttons:
				alert.addButtonWithTitle_(button)
		self.logToConsole(self.sheetPanel)
		alert.beginSheetModalForWindow_modalDelegate_didEndSelector_contextInfo_(NSApp.mainWindow(),
			self,
			'alertDidEnd:returnCode:contextInfo:',
			None)
		return alert

	@objc.python_method
	def _runGit(self, args):
		gitPath = spawn.find_executable("git")
		if not gitPath:
			self.alert("Could not find git executable", "Did you install git?", ["Dismiss"])
		args.insert(0, gitPath)
		#print(args)
		spawn.spawn(args)

	@objc.signature(b'v@:@ii')
	def alertDidEnd_returnCode_contextInfo_(self, sheet, returnCode, info):
		return

	def validateMenuItem_(self, item):
		#print("__validateMenuItem_1")
		if self.revisionMenuItem == item:
			# check if current font is under version control
			# if not, return False
			#print("__validateMenuItem_2")
			pass
		return True

	def showRevisions_(self, sender):
		GlyphsGitList.GitList()

	@objc.python_method
	def logToConsole(self, message):
		"""
		The variable 'message' will be passed to Console.app.
		Use self.logToConsole("bla bla") for debugging.
		"""
		myLog = "%s:\n%s" % (self.__class__.__name__, message)
		NSLog(myLog)

