# coding: utf-8

"""
QGis plugin to visualize data and sources of an ADMS-Urban `.upl` file.

Copyright : (c) 2014 by Jonathan VIRGA (jonathan.virga@gmail.com)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

This script initializes the plugin, making it known to QGIS.
"""


def classFactory(iface):
    # load Shortcut class from file Shortcut
    from qgis_admsurban import QGisADMSUrbanViewer
    return QGisADMSUrbanViewer(iface)
