"""run diffusion equation to determine selectivity"""

"calculate 2D implicit forcefield; clever save/continue depending on params."
from nanopores.models import Howorka
from nanopores.tools import fields
import nanopores

import numpy, dolfin
from matplotlib import pyplot
import nanopores
from nanopores.physics.convdiff import ConvectionDiffusion

nanopores.add_params(
    log = True,
    levels = 1,
    t = 1e-0,
    steps = 100, # timesteps per level for logarithmic time plot
)
   
nanopores.add_params(
    rMolecule = 0.5,
    Qmol = -1.,
    h = 1.,
    Nmax = 2e4,
)

params = dict(
    bV = 0.,
    dnaqsdamp = 0.5,
    rMolecule = rMolecule,
    Qmol = Qmol,
    bulkcon = 3e2,
    Nmax = Nmax,
    h = h,
    Rx = 12.,
    Ry = 12.,
)

# save and load implicit force field
NAME = "force2Dimp"

def save_forcefield_implicit(**params):
    F, Fel, Fdrag = Howorka.F_field_implicit(**params)
    mesh = Howorka.geo.mesh
    uid = fields._unique_id()
    FNAME = NAME + uid
    nanopores.save_functions(FNAME, mesh, meta=params, F=F, Fel=Fel, Fdrag=Fdrag)
    fields.save_entries(NAME, params, FNAME=FNAME)
    fields.update()
    
def load_forcefield_implicit(**params):
    FNAME = fields.get_entry(NAME, "FNAME", **params)
    forces, mesh, params = nanopores.load_vector_functions(str(FNAME))
    return forces["F"], forces["Fel"], forces["Fdrag"], mesh, params
    
def maybe_calculate(**newparams):
    params.update(newparams)

    if fields.exists(NAME, **params):
        print "Existing force field found."
    else:
        print "Calculating force field."
        save_forcefield_implicit(**params)
        
    return load_forcefield_implicit(**params)

if __name__ == "__main__":
    import dolfin
    from plot_forcefield import porestreamlines
    F, Fel, Fdrag, mesh, params = maybe_calculate(**params)
    dolfin.plot(mesh)
    porestreamlines(Howorka.polygon(), 6., 8., F=F)
    nanopores.showplots()
    

# import force field, mesh etc.
from forcefield import geo, phys, Fel, Fdrag, params

# initial condition

#N = 10. # number of molecules to diffuse
#r = 50. # radius of spherical region where molecules start [nm]
#Vol = dolfin.pi*4./3.*r**3 # volume of region [nm**3]
#c0 = N/Vol # concentration [1/nm**3]
#x0 = numpy.array([0., z0]) # position of region 
#u0f = lambda x: (c0 if sum((x-x0)**2) < r**2 else 0.) # function

# concentration in 1/nm**3 (Burns et al.)
c0 = 2*50.*(phys.mol*phys.nm**3) # 50 mM = 50*mol/m**3 (50*6e23*1e-27 = 3e-2)
u0 = geo.pwconst("c0", dict(bulkfluidtop = c0, default=0.))

# total concentration
ctot = dolfin.assemble(u0*dolfin.Expression("2*pi*x[0]")*geo.dx())
print "Total concentration:", ctot, "molecules."

def convect(geo, phys, Fel, Fdrag, u0, t=1e-9, log=False):
    frac = 1./steps
    dt = t/steps
    bc = {} #dict(upperb=dolfin.Constant(0.), lowerb=dolfin.Constant(0.))
    F = dolfin.Constant(1.)*(Fel + dolfin.Constant(3.)*Fdrag) # TODO bad hack
    pde = ConvectionDiffusion(geo, phys, dt=dt, F=F, u0=u0, bc=bc, cyl=True)
    pde.add_functionals([current, selectivity])
    #yield pde
    pde.timerange = nanopores.logtimerange(t, levels=levels, frac=frac,
                                               change_dt=pde.change_dt)
    for t_ in pde.timesteps(t=t):
        pde.record_functionals()
        pde.visualize()
        
    return pde
    
def current(U, geo):
    u, = U
    r2pi = dolfin.Expression("2*pi*x[0]")
    phys = geo.physics
    grad = phys.grad
    D = geo.pwconst("Dtarget")
    kT = dolfin.Constant(phys.kT)
    F = Fel + dolfin.Constant(3.)*Fdrag
    # current density [1/nm**3]*[nm/ns] = [1/(ns*nm**2)]
    j = -D*grad(u) + D/kT*F*u
    #lscale = Constant(phys.lscale)
    L = dolfin.Constant(9.) # pore length
    # current in 1/ns
    J = -j[1]/L *r2pi*geo.dx("pore")
    # current in 1/ms
    J = 1e6*J
    return dict(J=J)
    
def selectivity(U, geo):
    u, = U
    r2pi = dolfin.Expression("2*pi*x[0]")
    # urel = % of total concentration
    urel = u/dolfin.Constant(ctot/100)
    c = urel *r2pi*geo.dx() 
    ctop = urel *r2pi*geo.dx("bulkfluidtop")
    cbottom = urel *r2pi*geo.dx("bulkfluidbottom")
    cpore = urel *r2pi*geo.dx("pore")
    return dict(c=c, ctop=ctop, cbottom=cbottom, cpore=cpore)

# compute
pde = convect(geo, phys, Fel, Fdrag, u0=u0, t=t, log=log)

# save results
NAME = "howorka2D_selectivity_Q%.0f" % (params["Qmol"],)
results = dict(
    time = pde.time,
    release = pde.functionals["cbottom"].values,
    current = pde.functionals["J"].values,
)
nanopores.save_stuff(NAME, results, params)

pde.plot_functionals("plot", ["cbottom"])
pyplot.ylabel("% release")
pde.plot_functionals("semilogx", ["J"])
pyplot.ylabel("current through pore [1/ms]")
#pyplot.show(block=True)
