# (c) 2017 Gregor Mitscha-Baude
import numpy as np
import matplotlib.pyplot as  plt
import nanopores
import nanopores.models.randomwalk as randomwalk
from nanopores.tools import fields
fields.set_dir_mega()

from nonlinear_least_squares import NLS
# TODO: fit bond rupture length to wei data

params = nanopores.user_params(
    # general params
    geoname = "wei",
    dim = 2,
    rMolecule = 1.25, # 6.
    h = 5.,
    Nmax = 1e5,
    Qmol = 2., #15.,
    bV = -0.2,
    dp = 26.,
    geop = dict(dp = 26.),
    posDTarget = True,

    # random walk params
    N = 100000, # number of (simultaneous) random walks
    dt = .5, # time step [ns]
    walldist = 2., # in multiples of radius, should be >= 1
    margtop = 60.,
    margbot = 0.,
    #zstart = 46.5, # 46.5
    #xstart = 0., # 42.
    rstart = 30,
    initial = "sphere",

    # receptor params
    tbind = 40e9, # = 1/kd = 1/(25e-3)s [ns]
    ka = 1.5e5,
    zreceptor = .95, # receptor location relative to pore length (1 = top)
)
##### what to do
NAME = "rw_wei_"
print_calculations = False
run_test = False
plot_distribution = False
plot_cdf = False
voltage_dependence = False

##### constants
rrec = 0.5 # receptor radius
distrec = 4. - params.rMolecule - rrec # distance of rec. center from wall
ra = distrec #params.rMolecule*(params.walldist - 1.) - rrec
dx = 1.

def receptor_params(params):
    dx0 = params["dx"] if "dx" in params else dx
    return dict(
    exclusion = False,
    walldist = 1.,
    #minsize = 0.01, # accuracy when performing reflection

    binding = True,
    t = params["tbind"], # mean of exponentially distributed binding duration [ns]
    ka = params["ka"], # (bulk) association rate constant [1/Ms]
    ra = ra, # radius of the association zone [nm]
    bind_type = "zone",
    collect_stats_mode = True,

    use_force = True, # if True, t_mean = t*exp(-|F|*dx/kT)
    dx = dx0, # width of bond energy barrier [nm]
    )

if print_calculations:
    phys = nanopores.Physics()
    # calculate binding probability with data from (Wei 2012)
    kon = 20.9e6 # association rate constant [1/Ms] = binding events per second
    c = 180e-9 # concentration [M = mol/l = 1000 mol/m**3]
    cmol = c * 1e3 * phys.mol # concentration [1/m**3]
    ckon = c*kon
    
    print "Average time between events (tau_on): %.2f s (from experimental data)" % (1./ckon)
    print "Number of bindings per second: %.1f (inverse of mean tau_on)" % ckon # 3.8
    
    # Smoluchowski rate equation gives number of arrivals at pore entrance per sec
    D = phys.kT / (6. * phys.pi * phys.eta * params.rMolecule * 1e-9) # [m**2/s]
    r = 6e-9 # effective radius for proteins at pore entrance [m]
    karr = 2.*phys.pi * r * D * cmol # arrival rate
    b = c * kon / karr # bindings per event
    
    print "Number of events per second: %.1f (from Smoluchowski rate equation)" % karr
    print "=> number of bindings per event: %.1f / %.1f = %.5f (= 1 - exp(-a*p) = prob of binding at least once)" % (ckon, karr, b)
    
    # solve b = 1 - exp(-ap); p = -log(1 - b)/a
    a = 0.305
    ap = -np.log(1 - b)
    p = ap/a
    print "=> a*p = -log(1 - %.5f) = %.5f" % (b, ap)
    print
    print "Average number of attempts: a = %.5f (from many simulations with dt=1, eps=0.1)" % a
    print "=> binding probability p = a*p / a = %.5f / %.5f = %.5f" % (ap, a, p)
    #receptor_params["p"] = p

def setup_rw(params):
    pore = nanopores.get_pore(**params)
    rw = randomwalk.RandomWalk(pore, **params)    
    
    zrec = rw.zbot + rrec + (rw.ztop - rw.zbot - 2.*rrec)*params["zreceptor"]
    xrec = pore.radius_at(zrec) - distrec
    posrec = [xrec, 0., zrec]
    print "Receptor position: %s" % posrec
    receptor = randomwalk.Ball(posrec, rrec) # ztop 46.5
    rw.add_domain(receptor, **receptor_params(params))
    return rw

##### run test rw
if run_test:
    rw = setup_rw(params)
    randomwalk.run(rw)
    
##### draw bindings and forces from empirical distribution
def draw_empirically(rw, N=1e8, nmax=1000, success=True):
    self = rw.domains[1]
    N = int(N)
    ka = self.kbind
    # draw indices of existing random walks
    I = np.random.randint(rw.N, size=(N,))
    times = (1e-9*rw.times)[I]
    bindings = np.zeros(N, dtype=bool)
    avgbindings = (ka*rw.attempt_times)[I]
    bindings[avgbindings > 0] = np.random.poisson(avgbindings[avgbindings > 0])
    del avgbindings
    ibind, = np.nonzero(bindings > 0)
    n0 = len(ibind)
    n = min(n0, nmax)
    ibind = ibind[:n]
    print "%d binding events drawn, %s used." % (n0, n)
    
    f = np.array([f for F in rw.binding_zone_forces for f in F])
    F = np.random.choice(f, size=(n,))
    dx = 1e-9*self.dx
    kT = rw.phys.kT
    t = self.t * np.exp(-F*dx/kT)
    print "dwell time reduction by force:", np.mean(t)/self.t
    bind_times = 1e-9*np.random.gamma(bindings[ibind], scale=t)
    times[ibind] += bind_times
    
    if success:
        tfail = times[rw.fail[I]]
        tsuccess = times[rw.success[I]]
        return tfail, tsuccess
    else:
        return times[ibind]

##### load tau_off histogram from source and create fake data
def tauoff_wei():
    csvfile = "tau_off_wei.csv"
    data = np.genfromtxt(csvfile, delimiter=",")
    bins = data[:, 0]
    counts = data[:, 1]
    
    # inspection showed that there seems to be a good,
    # evenly spaced approximation to all bins except the first and last with
    # spacing 0.55, i.e. of the form (beta + 0.55*np.arange(0, N)) for some beta
    x = bins[:-1]
    N = len(x)
    # minimize norm(x - (beta + 0.55*np.arange(0, N)) w.r.t. beta
    #beta = x.mean() - 0.55*(N-1)/2.
    # turns out beta is close to 0.25, which gives nice numbers,
    # so we will just take that
    bins = 0.25 + 0.55*np.arange(0, N)
    bins = [0.] + list(bins) + [20.]
    N = N+1
    
    # the counts should be integer-values, so
    counts = np.round(counts).astype(int)
    
    # TODO: need better experimental data => webtool
    # create fake data samples that reproduce the histogram
    fake = np.array([])
    
    frac = 1.
    while int(counts[0]*frac) > 1:
        frac /= 2.
        a, b = bins[1]*frac, bins[1]*2*frac
        sample = a*(b/a)**(np.random.rand(int(counts[0]*frac)))
        fake = np.append(fake, sample)
        #print "frac", frac
    
    for i in range(1, N):
        a, b = bins[i], bins[i+1]
        sample = a*(b/a)**(np.random.rand(counts[i]))
        fake = np.append(fake, sample)
        
    print len(fake), "events loaded from experimental data."
    return fake

##### run rw in collect mode and draw bindings from empirical distributions
if plot_distribution:
    rw = randomwalk.get_rw(NAME, params, setup=setup_rw)
    ta = rw.attempt_times
    ta = ta[ta > 0.]
    #tt = np.logspace(-.5, 2.5, 100)
    tt = np.linspace(0.25, 200., 100)
    plt.figure("attempt_times")
    plt.hist(ta, bins=tt, normed=True, label="Simulations")
    ta0 = ta.mean()
    plt.plot(tt, 1./ta0 * np.exp(-tt/ta0), label="Exp. fit, mean=%.3gns" % ta0)
    #plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Attempt time [ns]")
    plt.ylabel("Rel. frequency")
    plt.legend()
    
    forces = np.array([f for F in rw.binding_zone_forces for f in F])
    plt.figure("force")
    plt.hist(1e12*forces, bins=200, normed=True)
    plt.xlabel("Force [pN]")
    plt.ylabel("Rel. frequency")
    
    plt.figure("hist")
    fake = tauoff_wei()
    tfail, tsuccess = draw_empirically(rw, N=3e8, nmax=len(fake))
    a, b = -6.5, 3 # log10 of plot interval
    bins = np.logspace(a, b, 40)
    plt.hist(tsuccess, bins=bins, color="green", alpha=0.6, rwidth=0.9, label="Translocated", zorder=50)
    plt.hist(tfail, bins=bins, color="red", alpha=0.6, rwidth=0.9, label="Did not translocate")
    plt.hist(fake, bins=bins, histtype="step", color="orange", label="Wei et al.", zorder=100)
    plt.xscale("log")
    plt.yscale("log")
    plt.ylabel("Count")
    plt.xlabel(r"$\tau$ off [s]")
    plt.ylim(ymin=1.)
    plt.legend()
    
###### determine tauoff from fit to exponential cdf 1 - exp(t/tauoff)
@fields.cache("wei_koff_1", default=dict(params, dx=1.))
def fit_koff(**params):
    rw = randomwalk.get_rw(NAME, params, setup=setup_rw, calc=False)
    times = draw_empirically(rw, N=3e8, nmax=523, success=False)
    bins = np.logspace(-3., 2., 35)
    hist, _ = np.histogram(times, bins=bins)
    cfd = np.cumsum(hist)/float(np.sum(hist))
    t = 0.5*(bins[:-1] + bins[1:])
    tmean = times.mean()
    toff = NLS(t, cfd, t0=tmean)
    koff = 1./toff
    return dict(t=t, cfd=cfd, toff=toff, tmean=tmean, koff=koff)

###### reproduce cumulative tauoff plot with fits and different bV
voltages = [-0.2, -0.25, -0.3, -0.35][::-1]
colors = ["k", "r", "b", "g"][::-1]
zrecs = [.90, .95, .99]
N = 10000
newparams = dict(N=N, dp=30., geop=dict(dp=30.))

if plot_cdf:
    plt.figure("bV_tauoff")
    for i, v in enumerate(voltages):
        data = fit_koff(bV=v, zreceptor=.95, dx=3., **newparams)
        tt = np.logspace(-3., 2., 100)
        
        lines = plt.semilogx(tt, 1. - np.exp(-tt/data.toff), color=colors[i],
                             label="%d mV" % (1000*abs(v)))
        plt.semilogx(data.t, data.cfd, "v", color=lines[0].get_color())
        print "koff", data.koff
    plt.legend()
    
###### read koff-bV dependence from wei data
koff0 = np.array([])
coeff = np.array([])
for i in range(1, 6):
    data = np.genfromtxt("koff%d.csv" %i, delimiter=",")
    x = data[:, 0]*1e-3
    y = np.log(data[:, 1])
    a = (np.diff(y)/np.diff(x))[0]
    b = y[0] - a*x[0]
    coeff = np.append(coeff, a)
    koff0 = np.append(koff0, np.exp(b))
    #xx = np.linspace(0, 400, 50)
    #plt.semilogy(x, np.exp(y), "o")
    #plt.semilogy(xx, np.exp(a*xx + b))
print "coeff %.3g +- %.3g" % (coeff.mean(), coeff.std())
print "koff0 %.3g +- %.3g" % (koff0.mean(), koff0.std())

def regression(bV, koff):
    "find coefficients in relationship koff = koff0 * exp(a*bV)"
    X = np.column_stack([bV, np.ones(len(bV))])
    y = np.log(koff)
    a, b = tuple(np.dot(np.linalg.inv(np.dot(X.T, X)), np.dot(X.T, y)))
    return a, np.exp(b)

voltages = [-0.2, -0.25, -0.3, -0.35]
zrecs = [.90, .95, .99]
dxs = [1., 3., 5., 6.]
for dx in dxs:
    print "dx", dx    
    koff0 = np.array([])
    coeff = np.array([])
    for z in zrecs:
        for v, koff in nanopores.collect(voltages):
            data = fit_koff(bV=v, zreceptor=z, dx=dx, **newparams)
            koff.new = data.koff
        c, k = regression(np.abs(voltages), koff)
        coeff = np.append(coeff, c)
        koff0 = np.append(koff0, k)
    print "coeff %.3g +- %.3g" % (coeff.mean(), coeff.std())
    print "koff0 %.3g +- %.3g" % (koff0.mean(), koff0.std())


###### recreate voltage-dependent plot of tauoff
if voltage_dependence:
    voltages = [-0.2, -0.25, -0.3, -0.35]
    zrecs = [.90, .95, .99]
    N = 10000
    params.update(N=N, dp=30., geop=dict(dp=30.))
    for v in voltages:
        for z in zrecs:
            params.update(bV=v, zreceptor=z)
            rw = randomwalk.get_rw(NAME, params, setup=setup_rw)
  
import folders
nanopores.savefigs("tau_off2", folders.FIGDIR + "/wei", (4, 3), ending=".pdf")
