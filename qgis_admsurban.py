# coding: utf-8
"""
QGis plugin to visualize data and sources of an ADMS-Urban `.upl` file.

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

"""
import os.path
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import QgsGenericProjectionSelector
from qgis.gui import QgsMessageBar
from qgis.utils import iface
import resources_rc
import admsurban


def msg_info(msg, duration=3):
    """Push message."""
    mb = iface.messageBar()
    mb.pushMessage("ADMS-Urban", str(msg), level=QgsMessageBar.INFO,
                   duration=duration)
    
    
def msg_error(msg):
    mb = iface.messageBar()
    mb.pushMessage("ADMS-Urban", str(msg), level=QgsMessageBar.CRITICAL)
    
    
class QGisADMSUrbanViewer:
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value("locale/userLocale")[0:2]
        localepath = os.path.join(
            self.plugin_dir, 'i18n', 'admsurban_{}.qm'.format(locale))

        if os.path.exists(localepath):
            self.translator = QTranslator()
            self.translator.load(localepath)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

    def initGui(self):
        # Add toolbar 
        self.toolbar = self.iface.addToolBar("ADMS-Urban")
        
        # Create action that will start plugin configuration
        self.action_open = QAction(QIcon(":/plugins/admsurban/icon.png"),
                                   u"Open an UPL", self.iface.mainWindow())
        self.action_open.triggered.connect(self.run_open)  # connect with method

        # Add buttons to the toolbar
        self.toolbar.addAction(self.action_open)

    def unload(self):
        # Remove the toolbar
        del self.toolbar

    def run_open(self):
        """ Open an UPL and create temporary layers. """
        
        # Usefull variables
        reg = QgsMapLayerRegistry.instance()
        li = iface.legendInterface()
        
        # Ask for a filename
        fn = QFileDialog.getOpenFileName(None, "Open ADMS-Urban UPL file", "",
                                         "*.upl")
        if not fn:
            return
        
        # Open the UPL file
        upl = admsurban.ADMSUrbanUPL()
        upl.read(fn)
        pols = upl.pollutants
        
        # Projection selector
        projselector = QgsGenericProjectionSelector()
        rc = projselector.exec_()
        if not rc:
            return
        if not int(projselector.selectedCrsId()):
            msg_error("Projection not selected !")
            return
        crs = projselector.selectedAuthId()
        
        # Create group
        gpname = os.path.basename(fn)
        li.addGroup(gpname)
        idxgp = li.groups().index(gpname)  # index of this group

        # __ Point sources __
        if upl.src_points:
            
            # Create temporary layer
            vl_pts = QgsVectorLayer("Point?index=yes&crs=%s" % crs,
                                    "ADMS-Urban point sources", "memory")
            pr_pts = vl_pts.dataProvider()
            pr_pts.addAttributes([QgsField("src_name", QVariant.String), ] +
                                 [QgsField(e, QVariant.Double) for e in pols])
            vl_pts.updateFields()
            
            # Add features
            for src in upl.src_points:
                fet = QgsFeature()
                fet.setGeometry(
                    QgsGeometry.fromPoint(
                        QgsPoint(src.geom.x, src.geom.y)))
                emis = []
                for p in pols:
                    if p in src.srcpol:
                        idx = src.srcpol.index(p)
                        emis.append(src.srcemi[idx])
                    else:
                        emis.append(None)
                fet.setAttributes([src.srcname, ] + emis)
                pr_pts.addFeatures([fet])
                del fet, emis
            
            # Update extent
            vl_pts.setExtent(QgsRectangle(*upl.extent_points))
            
            # Style
            vl_pts.loadNamedStyle(os.path.join(self.plugin_dir, 'style',
                                               'ponct.qml'))
            reg.addMapLayer(vl_pts)
            li.moveLayer(vl_pts, idxgp)

        # __ Road sources __
        if upl.src_roads:
            
            # Create temporary layer
            vl_road = QgsVectorLayer("LineString?index=yes&crs=%s" % crs,
                                     "ADMS-Urban road sources", "memory")
            pr_road = vl_road.dataProvider()
            pr_road.addAttributes([QgsField("src_name", QVariant.String), ] +
                                  [QgsField(e, QVariant.Double) for e in pols])
            vl_road.updateFields()
            
            # Add features
            for src in upl.src_roads:
                fet = QgsFeature()
                fet.setGeometry(QgsGeometry.fromWkt(src.geom.wkt))
                emis = []
                for p in pols:
                    if p in src.srcpol:
                        idx = src.srcpol.index(p)
                        emis.append(src.srcemi[idx])
                    else:
                        emis.append(None)
                fet.setAttributes([src.srcname, ] + emis)
                pr_road.addFeatures([fet])
                del fet, emis
            
            # Update extent
            vl_road.setExtent(QgsRectangle(*upl.extent_roads))
            
            # Style
            vl_road.loadNamedStyle(os.path.join(self.plugin_dir, 'style',
                                                'road.qml'))
            reg.addMapLayer(vl_road)
            li.moveLayer(vl_road, idxgp)

        # __ Area sources __
        if upl.src_surfs:
            
            # Create temporary layer
            vl_area = QgsVectorLayer("Polygon?index=yes&crs=%s" % crs,
                                     "ADMS-Urban area sources", "memory")
            pr_area = vl_area.dataProvider()
            pr_area.addAttributes([QgsField("src_name", QVariant.String), ] +
                                  [QgsField(e, QVariant.Double) for e in pols])
            vl_area.updateFields()
            
            # Add features
            for src in upl.src_surfs:
                fet = QgsFeature()
                fet.setGeometry(QgsGeometry.fromWkt(src.geom.wkt))
                emis = []
                for p in pols:
                    if p in src.srcpol:
                        idx = src.srcpol.index(p)
                        emis.append(src.srcemi[idx])
                    else:
                        emis.append(None)
                fet.setAttributes([src.srcname, ] + emis)
                pr_area.addFeatures([fet])
                del fet, emis
            
            # Update extent
            vl_area.setExtent(QgsRectangle(*upl.extent_surfs))
            
            # Style
            vl_area.loadNamedStyle(os.path.join(self.plugin_dir, 'style',
                                                'area.qml'))
            reg.addMapLayer(vl_area)
            li.moveLayer(vl_area, idxgp)

        # __ Volume sources __
        if upl.src_vols:
            
            # Create temporary layer
            vl_vol = QgsVectorLayer("Polygon?index=yes&crs=%s" % crs,
                                    "ADMS-Urban volume sources", "memory")
            pr_vol = vl_vol.dataProvider()
            pr_vol.addAttributes([QgsField("src_name", QVariant.String), ] +
                                 [QgsField(e, QVariant.Double) for e in pols])
            vl_vol.updateFields()
            
            # Add features
            for src in upl.src_vols:
                fet = QgsFeature()
                fet.setGeometry(QgsGeometry.fromWkt(src.geom.wkt))
                emis = []
                for p in pols:
                    if p in src.srcpol:
                        idx = src.srcpol.index(p)
                        emis.append(src.srcemi[idx])
                    else:
                        emis.append(None)
                fet.setAttributes([src.srcname, ] + emis)
                pr_vol.addFeatures([fet])
                del fet, emis
            
            # Update extent
            vl_vol.setExtent(QgsRectangle(*upl.extent_vols))
            
            # Style
            vl_vol.loadNamedStyle(os.path.join(self.plugin_dir, 'style',
                                               'vol.qml'))
            reg.addMapLayer(vl_vol)
            li.moveLayer(vl_vol, idxgp)

        # __ Cadastre sources __
        if upl.src_cads:
            
            # Create temporary layer
            vl_cad = QgsVectorLayer("Polygon?index=yes&crs=%s" % crs,
                                    "ADMS-Urban cadastre sources", "memory")
            pr_cad = vl_cad.dataProvider()
            pr_cad.addAttributes([QgsField("src_name", QVariant.String), ] +
                                 [QgsField(e, QVariant.Double) for e in pols])
            vl_cad.updateFields()
            
            # Add features
            for src in upl.src_cads:
                fet = QgsFeature()
                fet.setGeometry(QgsGeometry.fromWkt(src.geom.wkt))
                emis = []
                for p in pols:
                    if p in src.srcpol:
                        idx = src.srcpol.index(p)
                        emis.append(src.srcemi[idx])
                    else:
                        emis.append(None)
                fet.setAttributes([src.srcname, ] + emis)
                pr_cad.addFeatures([fet])
                del fet, emis
            
            # Update extent
            vl_cad.setExtent(QgsRectangle(*upl.extent_cads))
            
            # Style
            vl_cad.loadNamedStyle(os.path.join(self.plugin_dir, 'style',
                                               'cad.qml'))
            reg.addMapLayer(vl_cad)
            li.moveLayer(vl_cad, idxgp)

        # End
        msg_info("%s loaded" % os.path.basename(fn), duration=5)
