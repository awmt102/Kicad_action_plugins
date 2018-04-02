#  action_archive_schematics.py
#
# Copyright (C) 2018 Mitja Nemec
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

import wx
import pcbnew
import archive_project



SCALE = 1000000.0


class ArchiveProjectDialog (wx.Dialog):

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=u"Archive project", pos=wx.DefaultPosition,
                           size=wx.Size(224, 159), style=wx.DEFAULT_DIALOG_STYLE)

        bSizer4 = wx.BoxSizer(wx.VERTICAL)

        self.m_staticText2 = wx.StaticText(self, wx.ID_ANY, u"Archive project:", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText2.Wrap(-1)
        bSizer4.Add(self.m_staticText2, 0, wx.ALL, 5)

        self.chkbox_sch = wx.CheckBox(self, wx.ID_ANY, u"Archive Schematics", wx.DefaultPosition, wx.DefaultSize, 0)
        self.chkbox_sch.SetValue(True)
        bSizer4.Add(self.chkbox_sch, 0, wx.ALL, 5)

        self.chkbox_3D = wx.CheckBox(self, wx.ID_ANY, u"Archive 3D models", wx.DefaultPosition, wx.DefaultSize, 0)
        self.chkbox_3D.SetValue(True)
        bSizer4.Add(self.chkbox_3D, 0, wx.ALL, 5)

        bSizer5 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_button3 = wx.Button(self, wx.ID_OK, u"OK", wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer5.Add(self.m_button3, 0, wx.ALL, 5)

        self.m_button4 = wx.Button(self, wx.ID_CANCEL, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer5.Add(self.m_button4, 0, wx.ALL, 5)

        bSizer4.Add(bSizer5, 1, wx.EXPAND, 5)

        self.SetSizer(bSizer4)
        self.Layout()

        self.Centre(wx.BOTH)


class ArchiveProject(pcbnew.ActionPlugin):
    """
    A script to delete selection
    How to use:
    - move to GAL
    - call the plugin
    """

    def defaults(self):
        self.name = "Archive project"
        self.category = "Archive project"
        self.description = "Archive schematics symbols and 3D models"

    def Run(self):
        _pcbnew_frame = \
            filter(lambda w: w.GetTitle().startswith('Pcbnew'),
                   wx.GetTopLevelWindows()
                   )[0]

        # only testing if keypress simulation works
        key_simulator = wx.UIActionSimulator()

        board = pcbnew.GetBoard()

        # show GUI
        # show dialog
        main_dialog = ArchiveProjectDialog(_pcbnew_frame)
        main_res = main_dialog.ShowModal()

        if main_res == wx.ID_OK:
            # warn about backing up project before proceeding
            caption = 'Archive project'
            message = "The project should be backed-up before proceeding"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_QUESTION)
            dlg.ShowModal()
            dlg.Destroy()
        # exit the plugin
        else:
            return

        # if user clicked OK
        if main_res == wx.ID_OK:
            if main_dialog.chkbox_sch.GetValue():
                # show the dialog informing the user that eeschema should be closed
                caption = 'Archive project'
                message = "Is eeschema closed?"
                dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
                res = dlg.ShowModal()
                dlg.Destroy()

                if res == wx.ID_NO:
                    caption = 'Archive project'
                    message = "You need to close eeschema and then run the plugin again!"
                    dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
                    dlg.ShowModal()
                    dlg.Destroy()
                    return

                # archive schematics
                try:
                    archive_project.archive_symbols(board, alt_files=False)
                except ValueError or IOError or LookupError as error:
                    caption = 'Archive project'
                    message = error
                    dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_EXCLAMATION)
                    dlg.ShowModal()
                    dlg.Destroy()

            if main_dialog.chkbox_3D.GetValue():
                caption = 'Archive project'
                message = "Current layout will be saved and when the plugin finishes, pcbnew will be closed." \
                          "This is normal behaviour.\n" \
                          "You should back up the project before proceeding any further\n" \
                          "\nProceed?"
                dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
                res = dlg.ShowModal()
                dlg.Destroy()

                if res == wx.ID_NO:
                    return

                # simulate Ctrl+S (save layout)
                key_simulator.KeyDown(wx.WXK_CONTROL_S, wx.MOD_CONTROL)
                key_simulator.KeyUp(wx.WXK_CONTROL_S, wx.MOD_CONTROL)

                try:
                    archive_project.archive_3D_models(board, allow_missing_models=False, alt_files=False)
                except IOError as error:
                    caption = 'Archive project'
                    message = str(error) + "\nContinue?"
                    dlg = wx.MessageDialog(_pcbnew_frame, message, caption,  wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
                    res = dlg.ShowModal()
                    dlg.Destroy()

                    if res == wx.ID_YES:
                        # simulate Ctrl+S (save layout)
                        key_simulator.KeyDown(wx.WXK_CONTROL_S, wx.MOD_CONTROL)
                        key_simulator.KeyUp(wx.WXK_CONTROL_S, wx.MOD_CONTROL)

                        archive_project.archive_3D_models(board, allow_missing_models=True, alt_files=False)
                    else:
                        return

                # exit pcbnew to avoid issues with concurent editing of .kicad_pcb file
                # simulate Alt+F (File) and e twice (Exit) and Enter
                key_simulator.KeyDown(ord('f'), wx.MOD_ALT)
                key_simulator.KeyUp(ord('f'), wx.MOD_ALT)

                key_simulator.KeyDown(ord('e'))
                key_simulator.KeyUp(ord('e'))

                key_simulator.KeyDown(ord('e'))
                key_simulator.KeyUp(ord('e'))

                key_simulator.KeyDown(wx.WXK_RETURN)
                key_simulator.KeyUp(wx.WXK_RETURN)

        main_dialog.Destroy()