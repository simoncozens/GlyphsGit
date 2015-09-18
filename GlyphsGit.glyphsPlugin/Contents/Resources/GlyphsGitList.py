#MenuTitle: View revision history
# -*- coding: utf-8 -*-
__doc__="""
Allows you to navigate the git history of your font, visiting older or newer versions.
"""
from vanilla import *
from distutils import spawn
import sys, os, re
import subprocess
from GlyphsApp import Glyphs

class GitList(object):
  def __init__(self):
    self.oldCwd = os.getcwd()
    p = Glyphs.font.filepath
    try:
      os.chdir(os.path.dirname(p))
      if not os.path.isdir("./git"):
        self._runGit(["init"])
      self._runGit(["checkout", "master"])
      process = subprocess.Popen(["git", "log", "--pretty=format:%h,%cr,%s","--abbrev-commit"], stdout=subprocess.PIPE)
      result = process.communicate()[0]
      lines = []
      for x in result.split("\n"):
        line = x.split(",")
        lines.append({"Revision": line[0], "Date": line[1], "Changes": line[2]})
      self.lines = lines
      os.chdir(self.oldCwd)
      self.w = Window((400, 400))
      self.w.myList = List((0, 0, -0, -0), lines,
        columnDescriptions=[{"title": "Revision", "width": 70}, {"title": "Date", "width": 100}, {"title": "Changes", "width": 228}],
        allowsMultipleSelection=False,
                   doubleClickCallback=self.selectionCallback)
      self.w.open()
      # TODO: Better error reprorting, especially if the file is not under verison control
    except:
      import traceback
      print traceback.format_exc()

  def _runGit (self, args):
    gitPath = spawn.find_executable("git")
    if not gitPath:
      self.alert("Could not find git executable", "Did you install git?", ["Dismiss"])
    args.insert(0, gitPath)
    spawn.spawn(args)

  def selectionCallback(self, sender):
    try:
      rev = self.lines[sender.getSelection()[0]]["Revision"]
      self.oldCwd = os.getcwd()
      p = Glyphs.font.filepath
      os.chdir(os.path.dirname(p))
      Font = Glyphs.font # frontmost font
      Font.disableUpdateInterface()
      self._runGit(["checkout", rev])
      Font.parent.revertToContentsOfURL_ofType_error_(
        NSURL.fileURLWithPath_(p),
        "com.schriftgestaltung.glyphs",
        None)
      Font.enableUpdateInterface()
      os.chdir(self.oldCwd)
      # Glyphs.redraw() broken?
      NSNotificationCenter.defaultCenter().postNotificationName_object_("GSRedrawEditView", None)
    except Exception as e:
      print( e )

