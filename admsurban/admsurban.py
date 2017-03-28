# coding: utf-8

"""Read ADMS-Urban namelist.

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


import sys
import re
from shapely.geometry import Point, Polygon, LineString


def listfromstr(s):
    """Return list of elements from "'xxx' 'xxx' 'xxx'" string."""
    l = s.strip().split("'")
    if len(l) % 2 != 1:
        return None  # cannot find elements...
    else:
        return l[1:-1:2]


class ADMSUrbanSource:
    """ADMS-Urban source."""
    
    def __init__(self, srcname, srctyp, srcpol, srcemi, geom):
        self.srcname = srcname
        self.srctyp = srctyp
        self.srcpol = srcpol
        self.srcemi = srcemi
        self.geom = geom
    
    def __repr__(self):
        return "<ADMSUrbanSource(type={})>".format(self.srctyp)
    
    def __str__(self):
        return ("ADMSUrbanSource(\n  name = {}\n  type = {}\n   pol = {}\n   "
                "emi = {}\n  geom = {}\n)").format(
            self.srcname, self.srctyp, self.srcpol, self.srcemi, self.geom)


class ADMSUrbanUPL:
    """ADMS-Urban UPL."""
    
    def __init__(self):
        self._srcnames = ['src_roads', 'src_surfs', 'src_vols', 'src_points',
                          'src_cads']  # list of variables
        self.src_roads = []
        self.src_surfs = []
        self.src_vols = []
        self.src_points = []
        self.src_cads = []

    def __repr__(self):
        return "<{}>".format(self)

    def __str__(self):
        return ("ADMSUrbanUPL({} roads, {} points, {} vols, {} surfs, "
                "{} cads)").format(
            len(self.src_roads), len(self.src_points), len(self.src_vols),
            len(self.src_surfs), len(self.src_cads))

    def read(self, fn):
        """Read a UPL ADMS-Urban file."""
        
        # Read file
        with open(fn, 'r') as f:
            lines = f.readlines()

        # Read source details and source vertex blocks
        src_re = re.compile(r'&ADMS_SOURCE_DETAILS([^&/]+)/', re.DOTALL)
        src_blocks = re.findall(src_re, "".join(lines))
        
        vtx_re = re.compile(r'&ADMS_SOURCE_VERTEX([^&/]+)/', re.DOTALL)
        vtx_blocks = re.findall(vtx_re, "".join(lines))
        
        # Read vertices informations
        vertices = []
        for vtx_block in vtx_blocks:
        
            # X and Y
            vtxx_re = re.compile(r'SourceVertexX\s+=\s+([0-9eE+-.]+)\s')
            vtxx = float(re.findall(vtxx_re, vtx_block)[0])

            vtxy_re = re.compile(r'SourceVertexY\s+=\s+([0-9eE+-.]+)\s')
            vtxy = float(re.findall(vtxy_re, vtx_block)[0])
            
            vertices.append((vtxx, vtxy))
        
        # Read source informations
        for src_block in src_blocks:
            
            # Source name
            srcnam_re = re.compile(r"SrcName\s+=\s+'(.*)'")
            srcnam = re.findall(srcnam_re, src_block)[0]
            
            # Source type
            srctyp_re = re.compile(r'SrcSourceType\s+=\s+(.*)\s')
            srctyp = int(re.findall(srctyp_re, src_block)[0])
            
            # List of pollutants
            srcpol_re = re.compile(r"SrcPollutants\s+=\s+('.*')\s", re.DOTALL)
            srcpol = [e.strip()
                      for e in listfromstr(re.findall(srcpol_re, src_block)[0])]
            
            # Emission rate of pollutants
            srcemi_re = re.compile(r"SrcPolEmissionRate\s+=\s+([^Src]+)",
                                   re.DOTALL)
            srcemi = [float(e)
                      for e
                      in re.findall(srcemi_re, src_block)[0].strip().split(' ')
                      if e]
            
            # Number of vertices
            srcnvx_re = re.compile(r'SrcNumVertices\s+=\s+([0-9]+)\s')
            srcnvx = int(re.findall(srcnvx_re, src_block)[0])
            
            # X and Y
            srcx_re = re.compile(r'SrcX1\s+=\s+([0-9eE+-.]+)\s')
            srcx = float(re.findall(srcx_re, src_block)[0])
            srcy_re = re.compile(r'SrcY1\s+=\s+([0-9eE+-.]+)\s')
            srcy = float(re.findall(srcy_re, src_block)[0])
            
            # Geometry
            if srctyp == 0:  # point source
                geom = Point(srcx, srcy)
                self.src_points.append(ADMSUrbanSource(srcnam, srctyp, srcpol,
                                                       srcemi, geom))
                del geom

            elif srctyp == 1:  # surface source
                coo = []
                for i in range(srcnvx):
                    coo.append(vertices.pop(0))
                coo.append(coo[0])  # close polygon
                geom = Polygon(coo)
                self.src_surfs.append(ADMSUrbanSource(srcnam, srctyp, srcpol,
                                                      srcemi, geom))
                del coo, geom
            
            elif srctyp == 2:  # volume source
                coo = []
                for i in range(srcnvx):
                    coo.append(vertices.pop(0))
                coo.append(coo[0])  # close polygon
                geom = Polygon(coo)
                self.src_vols.append(ADMSUrbanSource(srcnam, srctyp, srcpol,
                                                     srcemi, geom))
                del coo, geom
            
            elif srctyp == 4:  # road source
                coo = []
                for i in range(srcnvx):
                    coo.append(vertices.pop(0))
                geom = LineString(coo)
                self.src_roads.append(ADMSUrbanSource(srcnam, srctyp, srcpol,
                                                      srcemi, geom))
                del coo, geom
            
            elif srctyp == 5:  # cadastre
                coo = []
                for i in range(srcnvx):
                    coo.append(vertices.pop(0))
                coo.append(coo[0])  # close polygon
                geom = Polygon(coo)
                self.src_cads.append(ADMSUrbanSource(srcnam, srctyp, srcpol,
                                                     srcemi, geom))
                del coo, geom
            
            else:
                raise ValueError(
                    "cannot understand srctype = {}".format(srctyp))

    @property
    def sources(self):
        """Generator of all sources."""
        for srcname in self._srcnames:
            for src in self.__dict__[srcname]:
                yield src

    def __iter__(self):
        """Itenator of all sources."""
        return self.sources

    def __len__(self):
        """Numbers of sources."""
        return len(list(self.sources))

    @staticmethod
    def _extent(srcs):
        """Geographic extent of specific sources."""
        if not srcs:
            return None, None, None, None

        bounds = [e.geom.bounds for e in srcs]  # xmin, ymin, xmax, ymax
        xmin = min([e[0] for e in bounds])
        ymin = min([e[1] for e in bounds])
        xmax = max([e[2] for e in bounds])
        ymax = max([e[3] for e in bounds])
        return xmin, ymin, xmax, ymax

    @property
    def extent(self):
        """Geographic extent of all sources."""
        return self._extent(self.sources)

    @property
    def extent_roads(self):
        """Geographic extent of road sources."""
        return self._extent(self.src_roads)

    @property
    def extent_surfs(self):
        """Geographic extent of surface sources."""
        return self._extent(self.src_surfs)

    @property
    def extent_vols(self):
        """Geographic extent of volumes sources."""
        return self._extent(self.src_vols)

    @property
    def extent_points(self):
        """Geographic extent of points sources."""
        return self._extent(self.src_points)

    @property
    def extent_cads(self):
        """Geographic extent of cadastre sources."""
        return self._extent(self.src_cads)
        
    @property
    def pollutants(self):
        """List of pollutants from all sources."""
        if not len(self):
            return []
        pols = set([pol for e in self.sources for pol in e.srcpol])
        return list(pols)
    
    def to_csv(self, fn):
        """Export data into CSV file."""
        with open(fn, 'w') as f:
            f.write('src_name,src_type,' + ','.join(self.pollutants) + '\n')
            for src in self.sources:
                emis = []
                for p in self.pollutants:
                    if p not in src.srcpol:
                        emis.append("")
                    else:
                        idxp = src.srcpol.index(p)
                        emis.append(str(src.srcemi[idxp]))
                f.write('{srcname},{srctype},{emis}\n'.format(
                    srcname=src.srcname,
                    srctype=src.srctyp,
                    emis=",".join(emis)))


if __name__ == '__main__':

    # Testing...
    fnupl = sys.argv[1]
    upl = ADMSUrbanUPL()
    upl.read(fnupl)

    print(upl)
    print(upl.pollutants)
    print(len(upl))
    print(upl.src_roads[5])
    print(upl.src_points[10])
    print(upl.extent)

    upl.to_csv('/tmp/output.csv')
