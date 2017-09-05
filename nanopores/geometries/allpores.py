# (c) 2017 Gregor Mitscha-Baude
"""common interface for all pore geometries

should behave as follows:
    -) defines default parameters for the geometry
    -) provides function that takes geoname, geo params (including dim) plus
       small additional number of non-geo (solver) params
       (h, reconstruct, subs), and returns geo.
    -) optionally, provide functions that returns underlying geometrical object before
       building
    -) allows easy, modular addition of new geometries"""
import numpy as np

def lazy_import():
    global Params, any_params, polygons, MultiPore, Pore, pughpore
    global curved, alphahempoly
    from nanopores.tools.utilities import Params, any_params
    import nanopores.tools.polygons as polygons
    from nanopores.geometries.cylpore import MultiPore, Pore
    import nanopores.geometries.pughpore as pughpore
    import nanopores.geometries.curved as curved
    from nanopores.geometries.alphahempoly import poly as alphahempoly

def get_geo(geoname=None, **params):
    lazy_import()
    geoclass = geometries[geoname]()
    params["geoname"] = geoname
    return geoclass.get_geo(**params)

def get_pore(geoname=None, **params):
    lazy_import()
    geoclass = geometries[geoname]()
    params["geoname"] = geoname
    return geoclass.get_pore(**params)

class BasePore(object):

    def get_geo(self, h=1., reconstruct=False, **params):
        self.params = Params(self.default, **params)
        self.h = h
        self.reconstruct = reconstruct
        return self.build()

    def get_pore(self, **params):
        self.params = Params(self.default, **params)
        pore = self.pore()
        pore.build_polygons()
        pore.build_boundaries()
        return pore

class PughPore(BasePore):

    @property
    def default():
        return dict(pughpore.params,
        geoname = "pugh",
        diamPore = 6., # will override l0,.. if set
        diamDNA = 2.5, # will override l0,.. if diamPore set
        dim = 3,
    )

    def build(self):
        params = self.params
        h = self.h
        if params.diamPore is not None:
            diamPore = params.diamPore # inner (effective) pore diameter
            diamDNA = params.diamDNA # dna diameter of outer dna layers
            l0 = diamPore + 6.*diamDNA
            l1 = diamPore + 4.*diamDNA
            l2 = diamPore + 2.*diamDNA
            l3 = diamPore
            l4 = l1
            params.update(l0=l0, l1=l1, l2=l2, l3=l3, l4=l4)
        if params.dim == 3:
            geo = pughpore.get_geo(h, **params)
            if geo.params["x0"] is not None:
                molec = curved.Sphere(geo.params["rMolecule"],
                                           geo.params["x0"])
                geo.curved = dict(moleculeb = molec.snap)
        elif params.dim == 2:
            geo = pughpore.get_geo_cyl(h, **params)
            if geo.params["x0"] is not None:
                molec = curved.Circle(geo.params["rMolecule"],
                                      geo.params["x0"])
                geo.curved = dict(moleculeb = molec.snap)
        elif params.dim == 1:
            geo = pughpore.get_geo1D(h, **params)
        return geo

class AlphaHem(BasePore):

    default = dict(
        dim = 2,
        Htop = 7.,
        Hbot = 15.,
        R = 10.,
        cs = [-3, -6],
        zmem = -7.625,
        proteincs = [-2.3, -4.6, -7.2],
        subs = None,
    )

    def pore(self):
        return Pore(alphahempoly, porename="alphahem", **self.params)

    def build(self):
        pore = self.pore()
        geo = pore.build(self.h, self.params.subs, self.reconstruct)
        return geo

class WeiPore(BasePore):

    default = dict(
        R = 120.,
        R0 = 100.,
        H = 240.,
        #H0 = 70.,
        x0 = [0, 0, 46],
        rMolecule = 6.,
        dim = 3,
        no_membrane = True,
        dp = 45, # (small) pore radius as used in paper
        angle = 40, # aperture angle in degrees
        lcCenter = 0.3,
        lcMolecule = 0.1,
        h = 10.,
        subs = None,
        reconstruct = False,
        poreregion = True,
        receptor = None, #[40., 0., -30.],
        rReceptor = 1.25,
        reverse = True, # if True, narrow opening is at the top, as in paper
    )

    def polygons(self, params):
        lsin = 50. # SiN membrane thickness (in vertical direction)
        lau = 40. # Au membrane thickness (in vertical direction)
        rlau = 10. # Au thickness in radial direction
        lsam = 3 # SAM layer thickness (in vertical direction)

        l0 = lau + lsin + lsam
        angle2 = params.angle/2. * np.pi/180.
        tan = np.tan(angle2)
        sin = np.sin(angle2)
        cos = np.cos(angle2)
        l = l0/2.
        r0 = params.dp/2. - lsam
        r1 = r0 + l0*tan
        rsam = r0 + lsam/cos
        rsin = r0 + lsam/cos + rlau
        R = params.R
        split = 0.7
        Rsplit = split*R + (1.-split)*r1

        if not params.reverse:
            sam = [[r0, -l], [r1, l], [R, l], [R, l - lsam],
                   [rsam - tan*(lsam - l0), l - lsam], [rsam, -l]]
            au = [sam[5], sam[4], sam[3], [R, -l + lsin],
                  [rsin + tan*lsin, -l + lsin],
                  [rsin, -l]]
            sin = [au[5], au[4], au[3], [R, -l]]
        else:
            l = -l
            sam = [[r0, -l], [r1, l], [R, l], [R, l + lsam],
                   [rsam - tan*(lsam - l0), l + lsam], [rsam, -l]][::-1]
            au = [sam[-6], sam[-5], sam[-4], [R, -l - lsin],
                  [rsin + tan*lsin, -l - lsin],
                  [rsin, -l]][::-1]
            sin = [au[-6], au[-5], au[-4], [R, -l]][::-1]

        return sam, au, sin, Rsplit

    def pore(self):
        params = self.params
        sam, au, sin, Rsplit = self.polygons(params)

        sam, unchargedsam = polygons.Polygon(sam).split(Rsplit)
        au, unchargedau = polygons.Polygon(au).split(Rsplit)
        sin, unchargedsin = polygons.Polygon(sin).split(Rsplit)

        pore = MultiPore(**params)
        pore.add_polygons(chargedsam=sam, chargedau=au, chargedsin=sin,
                       unchargedsam=unchargedsam, unchargedau=unchargedau,
                       unchargedsin=unchargedsin)
        pore.synonymes = dict(
            sam={"chargedsam", "unchargedsam"},
            au={"chargedau", "unchargedau"},
            sin={"chargedsin", "unchargedsin"},)

        if params.receptor is not None:
            receptor = polygons.Ball(params.receptor, params.rReceptor, lc=0.1)
            pore.add_balls(receptor=receptor)
        return pore

    def build(self):
        pore = self.pore()
        geo = pore.build(self.h, self.params.subs, self.reconstruct)
        return geo

geometries = dict(
    wei = WeiPore,
    pugh = PughPore,
    alphahem = AlphaHem,
)

if __name__ == "__main__":
    lazy_import()
    params = any_params(geoname="wei", h=10.)
    geo = get_geo(**params)
    print geo
    #print geo.mesh.coordinates()
    geo.plot_subdomains()
    geo.plot_boundaries(interactive=True)