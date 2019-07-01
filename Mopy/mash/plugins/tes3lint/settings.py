# -*- coding: utf-8 -*-

# Wrye Mash Polemos fork GPL License and Copyright Notice ==============================
#
# Wrye Mash 2018 Polemos fork Copyright (C) 2017-2019 Polemos
# * based on code by Yacoby copyright (C) 2011-2016 Wrye Mash Fork Python version
# * based on code by Melchor copyright (C) 2009-2011 Wrye Mash WMSA
# * based on code by Wrye copyright (C) 2005-2009 Wrye Mash
# License: http://www.gnu.org/licenses/gpl.html GPL version 2 or higher
#
#  Copyright on the original code 2005-2009 Wrye
#  Copyright on any non trivial modifications or substantial additions 2009-2011 Melchor
#  Copyright on any non trivial modifications or substantial additions 2011-2016 Yacoby
#  Copyright on any non trivial modifications or substantial additions 2017-2019 Polemos
#
# =======================================================================================

# Tes3Lint plugin for Wrye Mash Polemos fork ================================================
#
# Tes3Lint plugin, Copyright (C) 2018-, Polemos
#
# License: http://www.gnu.org/licenses/gpl.html GPL version 2 or higher.
#
# ===========================================================================================

import wx, os
from ...mosh import _
from ... import conf


dPos = wx.DefaultPosition
dSize = wx.DefaultSize
Size = wx.Size
space = ((0,0),1,wx.EXPAND,5)


class TES3lint_Settings(wx.Dialog):  # Polemos: a new settings window for TES3lint (Maybe I should also create a standalone program out of this).
    """Class for the TES3lint settings window."""

    def __init__(self, parent, pos):
        """The settings mini window."""
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=_(u'TES3lint Settings'), pos=pos, size=(331, 494), style=wx.DEFAULT_DIALOG_STYLE)

        if True:  # Box Sizers
            perl_sizer = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, _(u'Perl Executable:')), wx.HORIZONTAL)
            tesl3int_sizer = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, _(u'TES3lint Script Location:')), wx.HORIZONTAL)
            custom_flags_teslint_sizer = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, _(u'Custom Flags:')), wx.VERTICAL)
            extras_teslint_sizer = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, _(u'Extra Options (May cause freezes):')), wx.VERTICAL)
            result_sizer = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, _(u'Final Command:')), wx.HORIZONTAL)

        if True:  # Content
            # Perl Field/Button:
            self.perl_field = wx.TextCtrl(perl_sizer.GetStaticBox(), wx.ID_ANY, u'', dPos, dSize, wx.TE_NO_VSCROLL)
            self.browse_perl_btn = wx.Button(perl_sizer.GetStaticBox(), wx.ID_ANY, u'...', dPos, dSize, 0)
            # TES3lint Field/Button:
            self.tes3lint_field = wx.TextCtrl(tesl3int_sizer.GetStaticBox(), wx.ID_ANY, u'', dPos, dSize, wx.TE_NO_VSCROLL)
            self.browse_teslint_btn = wx.Button(tesl3int_sizer.GetStaticBox(), wx.ID_ANY, u'...', dPos, dSize, 0)
            # Recommended Flags:
            flags_radio_boxChoices = [_(u'-n  "normal" output flags on (fastest)'),
                                      _(u' -r  "recommended" output flags on (slow)'),
                                      _(u'-a  all output flags on. (slowest)'),
                                      _(u' -f "flags" specify flags below (separated by comma):')]
            self.flags_radio_box = wx.RadioBox(self, wx.ID_ANY, u'Recommended Lists of Flags:', dPos, dSize, flags_radio_boxChoices, 1, 0)
            self.flags_radio_box.SetSelection(0)
            # Custom Flags:
            self.custom_flags_text = wx.TextCtrl(custom_flags_teslint_sizer.GetStaticBox(), wx.ID_ANY, u'', dPos, dSize, 0)
            # Extra Options:
            self.debug_checkBox = wx.CheckBox(extras_teslint_sizer.GetStaticBox(), wx.ID_ANY, _(u'-D  "debug" output (vast)'), dPos, dSize, 0)
            self.verbose_checkBox = wx.CheckBox(extras_teslint_sizer.GetStaticBox(), wx.ID_ANY, _(u' -v  "verbose" (possibly more output)'), dPos, dSize, 0)
            # TES3lint result:
            self.final_static = wx.StaticText(result_sizer.GetStaticBox(), wx.ID_ANY, u'', dPos, dSize, 0)
            self.final_static.Wrap(-1)
            # Buttons
            self.ok_btn = wx.Button(self, wx.ID_OK, _(u'OK'), dPos, dSize, 0)
            self.cancel_btn = wx.Button(self, wx.ID_CANCEL, _(u'Cancel'), dPos, dSize, 0)

        if True:  # Theming
            self.perl_field.SetForegroundColour(wx.Colour(0, 0, 0))
            self.perl_field.SetBackgroundColour(wx.Colour(255, 255, 255))
            self.tes3lint_field.SetForegroundColour(wx.Colour(0, 0, 0))
            self.tes3lint_field.SetBackgroundColour(wx.Colour(255, 255, 255))
            self.custom_flags_text.SetForegroundColour(wx.Colour(0, 0, 0))
            self.custom_flags_text.SetBackgroundColour(wx.Colour(255, 255, 255))
            self.final_static.SetForegroundColour(wx.BLUE)
            self.final_static.SetBackgroundColour(wx.Colour(240, 240, 240))

        if True:  # Layout
            perl_sizer.AddMany([(self.perl_field,1,wx.ALL,5),(self.browse_perl_btn,0,wx.ALL,5)])
            tesl3int_sizer.AddMany([(self.tes3lint_field,1,wx.ALL,5),(self.browse_teslint_btn,0,wx.ALL,5)])
            custom_flags_teslint_sizer.Add(self.custom_flags_text, 0, wx.ALL|wx.EXPAND, 5)
            extras_teslint_sizer.AddMany([(self.debug_checkBox,0,wx.ALL,5),(self.verbose_checkBox,0,wx.ALL,5)])
            result_sizer.Add(self.final_static, 0, wx.ALL|wx.EXPAND, 5)
            buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
            buttons_sizer.AddMany([(self.ok_btn,0,wx.ALL,5),space,(self.cancel_btn,0,wx.ALL,5)])
            main_sizer = wx.BoxSizer(wx.VERTICAL)
            main_sizer.AddMany([(perl_sizer,0,wx.EXPAND,5),(tesl3int_sizer,0,wx.EXPAND,5),(self.flags_radio_box,0,wx.ALL|wx.EXPAND,5),
                        (custom_flags_teslint_sizer,0,wx.EXPAND, 5),(extras_teslint_sizer,0,wx.EXPAND,5),(result_sizer,0,wx.EXPAND,5),(buttons_sizer,0,wx.EXPAND,5)])
            self.SetSizer(main_sizer)

        if True:  # Events
            self.timer_po()
            self.Bind(wx.EVT_CLOSE, self.OnClose)
            self.ok_btn.Bind(wx.EVT_BUTTON, self.OnOK)
            self.cancel_btn.Bind(wx.EVT_BUTTON, self.OnClose)
            self.browse_perl_btn.Bind(wx.EVT_BUTTON, self.perl_dir)
            self.browse_teslint_btn.Bind(wx.EVT_BUTTON, self.tes3lint_dir)
            self.flags_radio_box.Bind(wx.EVT_RADIOBOX, self.refresh)
            self.Bind(wx.EVT_CHECKBOX, self.refresh)
            self.custom_flags_text.Bind(wx.EVT_TEXT, self.refresh)
            self.tes3lint_field.Bind(wx.EVT_TEXT, self.refresh)

        self.Layout()
        self.import_settings()
        self.ShowModal()

    def refresh(self, event):
        """Refresh command example on dialog."""
        conf.settings['tes3lint.refresh'] = True

    def timer_po(self):
        """A simple timer."""
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onUpdate, self.timer)
        self.timer.Start(1)

    def import_settings(self):
        """Import settings from conf."""
        self.perl_field.SetValue(conf.settings['tes3lint.perl'])
        self.tes3lint_field.SetValue(conf.settings['tes3lint.location'])
        settings = conf.settings['tes3lint.last']
        self.flags_radio_box.SetSelection(settings[0])
        self.custom_flags_text.SetValue((','.join((unicode(x) for x in settings[1]))).strip('[ ]'))
        self.debug_checkBox.SetValue(settings[2])
        self.verbose_checkBox.SetValue(settings[3])

    def export_settings(self):
        """Export settings to conf."""
        conf.settings['tes3lint.perl'] = self.perl_field.GetValue()
        conf.settings['tes3lint.location'] = self.tes3lint_field.GetValue()
        conf.settings['tes3lint.command.result'] = self.final_static.GetLabelText()
        conf.settings['tes3lint.last'] = [self.flags_radio_box.GetSelection(),
                                          self.getFlags(),
                                          self.debug_checkBox.GetValue(),
                                          self.verbose_checkBox.GetValue()]

    def pos_save(self):
        """Saves the TES3lint Settings pos."""
        conf.settings['tes3lint.pos'] = self.GetPosition()

    def getFlags(self):
        """For better readability in export_settings."""
        return [x.strip() for x in self.custom_flags_text.GetValue().strip().split(u',')]

    def cmd_factory(self):
        """Construct the command status text."""
        conf.settings['tes3lint.refresh'] = False
        radio_box = [u'-n', u'-r', u'-a']
        path = os.path.basename(self.tes3lint_field.GetValue())
        if not path: path = u'tes3lint'
        if self.flags_radio_box.GetSelection() != 3: flags = u'%s' % radio_box[self.flags_radio_box.GetSelection()]
        else: flags = u'-f %s' %  u', '.join(self.getFlags())
        if self.debug_checkBox.GetValue(): extra0 = u'-D'
        else: extra0 = u''
        if self.verbose_checkBox.GetValue(): extra1 = u'-v'
        else: extra1 = u''
        return u' '.join([path, flags, extra0, extra1])

    def switch(self, state):
        """Color switch for flags field (ON/OFF)."""
        self.custom_flags_text.SetEditable(state)
        if not state: color = wx.Colour(240, 240, 240)
        else: color = wx.Colour(255, 255, 255)
        self.custom_flags_text.SetBackgroundColour(color)

    def onUpdate(self, event):
        """Safety check for settings."""
        if self.flags_radio_box.GetSelection() == 3: self.switch(True)
        else: self.switch(False)
        if conf.settings['tes3lint.refresh']: self.final_static.SetLabelText(u'%s %s' % (self.cmd_factory(), _(u'"target_file"')))

    def perl_dir(self, event):
        """..."""
        self.perl_field.SetValue(self.FileDialog(u'Perl', u'Executable files (*.exe)|*.exe', 'perl.exe'))

    def tes3lint_dir(self, event):
        """..."""
        self.tes3lint_field.SetValue(self.FileDialog(u'TES3lint', u'All files (*.*)|*.*', 'tes3lint'))

    def FileDialog(self, name, wildcard, defaultfile):
        """Filepaths for Perl and TES3lint."""
        message = _(u"%s directory selection") % name
        dialog = wx.FileDialog(self, message, '', defaultfile, wildcard, style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
        if dialog.ShowModal() != wx.ID_OK:
            dialog.Destroy()
            return u''
        else:
            path = dialog.GetPath()
            dialog.Destroy()
            return path

    def OnClose(self, event):
        """Cancel/Close button handler."""
        self.pos_save()
        self.timer.Stop()
        conf.settings['tes3lint.refresh'] = True
        wx.Dialog.Destroy(self)

    def OnOK(self, event):
        """Ok button handler."""
        self.export_settings()
        self.OnClose('the door')