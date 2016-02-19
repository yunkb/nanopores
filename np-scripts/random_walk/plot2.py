import matplotlib.pyplot as plt
import numpy as np
from math import sqrt, acos, sin


x = np.load('exit_x.npy')
y = np.load('exit_y.npy')
z = np.load('exit_z.npy')
time = np.load('time.npy')
counter = np.load('counter.npy')

X_aHem = np.array([[2.16, 0.0, 0.0],
                      [2.77, 0.0, -0.19],
                      [3.24, 0.0, -0.1 ],
                      [3.59, 0.0, -0.1 ],
                      [3.83, 0.0, -0.35],
                      [3.84, 0.0, -0.8 ],
                      [3.67, 0.0, -1.34],
                      [3.73, 0.0, -1.96],
                      [3.93, 0.0, -2.31],
                      [4.23, 0.0, -2.67],
                      [4.44, 0.0, -2.81],
                      [4.33, 0.0, -3.25],
                      [4.01, 0.0, -3.5 ],
                      [3.99, 0.0, -3.67],
                      [4.11, 0.0, -3.94],
                      [4.39, 0.0, -4.12],
                      [4.44, 0.0, -4.52],
                      [4.73, 0.0, -4.86],
                      [4.96, 0.0, -5.41],
                      [4.89, 0.0, -5.87],
                      [4.63, 0.0, -6.44],
                      [4.43, 0.0, -6.96],
                      [4.07, 0.0, -7.32],
                      [3.71, 0.0, -7.51],
                      [3.46, 0.0, -7.36],
                      [3.41, 0.0, -7.1 ],
                      [3.31, 0.0, -6.9 ],
                      [3.04, 0.0, -6.87],
                      [2.73, 0.0, -6.73],
                      [2.41, 0.0, -6.6 ],
                      [2.17, 0.0, -6.41],
                      [1.97, 0.0, -6.23],
                      [1.84, 0.0, -6.03],
                      [1.76, 0.0, -5.87],
                      [1.54, 0.0, -5.87],
                      [1.4 , 0.0, -5.96],
                      [1.31, 0.0, -6.16],
                      [1.39, 0.0, -6.57],
                      [1.6 , 0.0, -6.81],
                      [1.71, 0.0, -7.09],
                      [1.76, 0.0, -7.32],
                      [1.67, 0.0, -7.65],
                      [1.44, 0.0, -7.81],
                      [1.49, 0.0, -8.06],
                      [1.56, 0.0, -8.36],
                      [1.44, 0.0, -8.61],
                      [1.43, 0.0, -8.79],
                      [1.44, 0.0, -9.1 ],
                      [1.6 , 0.0, -9.48],
                      [1.74, 0.0, -9.84],
                      [1.63, 0.0, -10.0],
                      [1.47, 0.0, -10.19],
                      [1.26, 0.0, -10.21],
                      [1.07, 0.0, -10.05],
                      [1.03, 0.0, -9.76],
                      [1.09, 0.0, -9.44],
                      [1.07, 0.0, -9.02],
                      [0.86, 0.0, -8.79],
                      [0.64, 0.0, -8.68],
                      [0.63, 0.0, -8.36],
                      [0.8 , 0.0, -8.22],
                      [0.81, 0.0, -7.93],
                      [0.89, 0.0, -7.71],
                      [1.04, 0.0, -7.51],
                      [1.1 , 0.0, -7.25],
                      [0.91, 0.0, -7.02],
                      [0.91, 0.0, -6.76],
                      [0.91, 0.0, -6.48],
                      [0.69, 0.0, -6.25],
                      [0.69, 0.0, -6.  ],
                      [0.66, 0.0, -5.68],
                      [0.59, 0.0, -5.36],
                      [0.53, 0.0, -5.12],
                      [0.54, 0.0, -4.92],
                      [0.79, 0.0, -4.84],
                      [1.03, 0.0, -4.89],
                      [1.21, 0.0, -4.7 ],
                      [1.36, 0.0, -4.42],
                      [1.49, 0.0, -4.16],
                      [1.66, 0.0, -3.92],
                      [1.66, 0.0, -3.7 ],
                      [1.8 , 0.0, -3.41],
                      [2.  , 0.0, -3.22],
                      [1.91, 0.0, -2.93],
                      [1.8 , 0.0, -2.71],
                      [1.56, 0.0, -2.55],
                      [1.46, 0.0, -2.38],
                      [1.3 , 0.0, -2.19],
                      [1.21, 0.0, -1.93],
                      [1.09, 0.0, -1.64],
                      [0.9 , 0.0, -1.45],
                      [0.8 , 0.0, -1.28],
                      [0.84, 0.0, -1.  ],
                      [1.  , 0.0, -0.8 ],
                      [1.26, 0.0, -0.64],
                      [1.7 , 0.0, -0.31]])

timestep=5e1/100.
exittime = np.linspace(0.,1.,100)*5e1
exitprop = np.zeros(100)
for index in range(100):
    exitprop[index]=np.where(time<timestep*(index+1))[0].shape[0]
exitprop*=1./np.sum(counter)
plt.plot(exittime,exitprop)
plt.show()
def radius(x,y):
    return sqrt(x**2+y**2)
def det(a,b,c,d):
	return a*d-b*c

def normal(ax,ay,bx,by,px,py):
	AP2=(ax-px)**2+(ay-py)**2
	BP2=(bx-px)**2+(by-py)**2
	AB2=(ax-bx)**2+(ay-by)**2
	AB=sqrt(AB2)
	c = (AP2-BP2+AB2)/(2*AB)
	if c>0. and c<AB:
		if AP2<=c**2:
			return 0.
		else:
			return sqrt(AP2-c**2)
	else:
		return 100.


def distance_to_surface(rad,z):
	if z>3.:
		return 100.
	elif rad>8.:
		return 100.
	else:
		size=X_aHem.shape[0]
		D = np.zeros(size)
		E = np.zeros(size)
		for index in range(size):
			D[index] = radius(rad-X_aHem[index][0],z-X_aHem[index][2])
			E[index] = normal(X_aHem[(index-1)][0],X_aHem[(index-1)][2],X_aHem[(index)][0],X_aHem[(index)][2],rad,z)
		return min([min(D),min(E)])


l=x.shape[0]
r=np.zeros(l)
for index in range(l):
    r[index]=radius(x[index],y[index])
plt.scatter(r,z,color='red')


leftend=max(np.max(r),10.)
x_mem=np.linspace(X_aHem[18][0],leftend,100)
y_mem=np.zeros(x_mem.shape[0])+X_aHem[18][2]
size=X_aHem.shape[0]
X=np.zeros(size+1)
Y=np.zeros(size+1)
for index in range(size):
	X[index]=X_aHem[index][0]
	Y[index]=X_aHem[index][2]
X[size]=X[0]
Y[size]=Y[0]
plt.plot(X,Y,linewidth='2',color='blue')
plt.scatter(X,Y,50,color='blue')
plt.plot(x_mem,y_mem,color='black',linewidth=1)
plt.show()
