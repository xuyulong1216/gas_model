import sympy as syp
import numpy as nup
from sympy.vector import CoordSys3D,scalar_potential 
import numba as nub

def vplus(vec0,vec1):
	return [vec0[i]+vec1[i] for i in range(0,len(vec0))] 	

def vsum(vecs):#vecs:[vec0,vec1,...]
	if len(vecs) == 1:
		return vecs[0]
	else:
		return vplus(vecs.pop(),vsum(vecs))

def dlcpy(lis):
	if  (type(lis) == list) and (type(lis[0]) != list):
		return (lambda l : [i for i in l])(lis)
	else:
		return [dlcpy(i) for i in lis]
		
def esum(exprs):#exprs:[expr0,expr1,...]
	if len(exprs) == 1:
		return exprs[0]
	else:
		return exprs.pop()+esum(exprs)
	
def vminus(vec0,vec1):
	return [vec0[i]-vec1[i] for i in range(0,len(vec0))]

def vamp(lbd,vec):
	return [lbd*i for i in vec] 
	
def vdot(vec0,vec1): 
	return sum([vec0[i]*vec1[i] for i in range(0,len(vec0))])
	
def vtimes(vec0,vec1):
	return syp.Matrix(vec0).cross(syp.Matrix(vec1))

def vnormalize(vec):
	return [i/vnorm(vec) for i in vec]

def vnorm(vec):
	return syp.sqrt(sum([i**2 for i in vec]))

def vangle(vec0,vec1):
	return syp.acos(vdot(vec0,vec1)/(vnorm(vec0)*vnorm(vec1)))
	
def dreflect(dic):
	return {v:k for k,v in dic.items()}
	
def avg(lis):
	return sum(lis)/len(lis)

def variance(lis):
	return sum([(i-avg(lis))**2 for i in lis])
	
def convol(fun0,fun1,var):
	tau=syp.symbols('tau')
	return syp.integrate(fun0.subs(var,tau)*fun1.subs(var,var-tau),(tau, -sp.oo, sp.oo))

def coeff(expr,var):
	if syp.Poly(expr).has(var):
		return syp.Poly(expr).coeff_monomial(var)
	else:
		return 0
		
def var_rng(var,rng):
	if (type(rng[-1]) == int or float) and (type(rng[0]) == int or float) :
		return syp.And(var > rng[0] , var < rng[-1])
	else :
		if rng[0] == '-inf' and (type(rng[-1]) == int or float) :
			return syp.And(var < rng[-1],True)
		elif rng[-1] == 'inf' and (type(rng[0]) == int or float ) :
			return syp.And(var > rng[0],True)
		else:
			return True
			
def newton_exterv(vec0,vec1,vec2,timediff,var):#var_val:[var,val1,val2,val3]
	diff1=vminus(vec0,vec1)/timediff
	diff2=vminus(vec1,vec2)/timediff
	ddiff=vminus(diff1,diff2)/(2*timediff)
	return vsum([vec0,vamp(var,diff1),vamp(var*(var+timediff),ddiff)])

def rect2sphere(rect):
	r=syp.sqrt(rect[0]**2+rect[1]**2+rect[2]**2)
	theta=syp.atan(rect[1]/rect[0])
	phi=syp.atan(rect[2]/(rect[0]**2+rect[1]**2))
	return [r,theta,phi]
	
def sphere2rect(sphere):
	x=sphere[0]*syp.sin(sphere[1])*syp.cos(sphere[2])
	y=sphere[0]*syp.sin(sphere[1])*syp.sin(sphere[2])
	z=sphere[0]*syp.cos(sphere[1])
	return [x,y,z]

def vavg(lis):
	return [i/len(lis) for i in vsum(lis)]

def moving_avg(lis):#lis:[var1,var2,var3,...var9] at least,  new data at lis[0]
	return [vavg([lis[0],lis[1],lis[2]]),vavg([lis[3],lis[4],lis[5]]),vavg([lis[6],lis[7],lis[8]])]

def coord_convert(coords,base_a,ori_a,base_b,ori_b): 
	ori_a_c=dlcpy(ori_a)
	ori_b_c=dlcpy(ori_b)
	coo_c=dlcpy(coords)
	
	ori_a_c.append(1)
	ori_b_c.append(1)
	coo_c.append(1)

	a_aff=syp.Matrix(base_a).col_join(syp.Matrix([[0,0,0]])).row_join(syp.Matrix(ori_a_c))
	b_aff=syp.Matrix(base_b).col_join(syp.Matrix([[0,0,0]])).row_join(syp.Matrix(ori_b_c))
	a_inv=syp.Matrix(a_aff).inv()
	b_inv=syp.Matrix(b_aff).inv()
	
	return (b_inv*a_aff*syp.Matrix(coo_c))[0:3]
def gpu_accel():
	pass

class Wind:
	def __init__(self,name,back_data,timediff,timediff_times=3): # moving_avg() limited 
		self.name=name
		self.t=syp.symbols(name+'_t')
		self.data=back_data
		
	def get_expr(self):
		avg_data=moving_avg(rect2sphere(self.data)[0:9])
		exterv=newton_exterv(*avg_data,timediff*timediff_times,self.t)
		return sphere2rect(self.exterv)
		
	def get_val(self,t):
		return [i.subs(self.t,t) for i in self.get_expr()]

class Surface:
	def __init__(self,name,point,diag0,diag1):
		#point:[point_x,point_y,point_z] diag0:[diag0_x,diag0_y,diag_z] diag1:[diag1_x,diag1_y,diag1_z]
		self.name=name
		self.x=syp.symbols(name+'_x')
		self.y=syp.symbols(name+'_y')
		self.z=syp.symbols(name+'_z')
		self.coords=[self.x,self.y,self.z]
		self.point=point
		self.diag0=diag0
		self.diag1=diag1

		vec_0= vminus(diag0,point)
		vec_1= vminus(diag1,point)
		self.nvec=vnormalize(vtimes(vec_0,vec_1))
		#print(name,'nvec',self.nvec)
		vec0= vnormalize(vec_0)
		vec1= vnormalize(vec_1)
		self.vec0=vec0
		self.vec1=vec1
		self.point1=vsum([self.point,vec_0,vec_1]) 
		
	def rnvec(self,source,wind): #source:[source_x,source_y,source_z] wind:[vw_x,vw_y,vw_z]
		wind_vec=wind.get_val(0)
		if vangle(self.nvec,[self.point[i]-source[i] for i in range(0,len(source))]) > nyp.pi/2:	
			return [-i for i in self.nvec]
		elif vangle(self.nvec,[self.point[i]-source[i] for i in range(0,len(source))]) < nyp.pi/2:
			return self.nvec
		else:
			if vangle(wind.t,self.nvec) > nyp.pi / 2:
				return [-i for i in self.nvec]
			elif vangle(wind_vec,self.nvec) < nyp.pi / 2:
				return self.nvec
			else:
				return [0,0,0]	

class Cube:
	def __init__(self,name,surface,source,wind,leng=3):
		rnvec=surface.rnvec(source,wind)
		self.name=name
		self.x=syp.symbols(name+'_x')
		self.y=syp.symbols(name+'_y')
		self.z=syp.symbols(name+'_z')
		self.base=[vsum([vminus([0,0,0],vamp(leng,rnvec))]),vsum([vminus(surface.diag0,surface.point)]),vsum([vminus(surface.diag1,surface.point)])]
		self.surface=surface
		self.abscoord=[self.x,self.y,self.z]
		
	def get_reflect(self,leng=3):
		world_coord=[[1,0,0],[0,1,0],[0,0,1]]
		coord_converted=coord_convert(self.abscoord,world_coord,[0,0,0],self.base,self.surface.point)
		return syp.Piecewise((0.8*syp.exp(-coord_converted[0]),syp.And(*[var_rng(i,[0,1]) for i in coord_converted])),(0,True))
	
	
	def get_decrease(self,leng=3):
		range_list[[-1,0],[0,1],[0,1]]
		coord_converted=coord_convert(self.abscoord,world_coord,[0,0,0],self.base,self.surface.point)
		return syp.Piecewise((0.8*syp.exp(-coord_converted[0]),syp.And(*[var_rng(coord_converted[i],range_list[i]) for i in range(0,len(coord_converted))])),(0,True))
		
class EnvDiscriptor:
	def __init__(self,name,cubes):
		#cubes:[Cube1,Cube2,Cube3...]
		self.x=syp.symbols(name+'_x')
		self.y=syp.symbols(name+'_y')
		self.z=syp.symbols(name+'_z')
		self.expr=0
		self.coords=[self.x,self.y,self.z]
		self.expr=esum([i.get_expr().xreplace({i.x:self.x,i.y:self.y,i.z:self.z}) for i in cubes])
		self.expr=self.expr.doit(deep=False)
		self.decrease=esum([self.get_reflect().xreplace({i.x:self.x,i.y:self.y,i.z:self.z}) for i in cubes])
		self.decrease=self.decrease.doit(deep=False)
		
	def get_expr(self):
		return self.expr
		
	def get_decrease(self):
		return self.decrease
	
class GaussModel:
	def __init__(self,name,source_position):
		self.name=name
		self.x=syp.symbols(name+'_x')
		self.y=syp.symbols(name+'_y')
		self.z=syp.symbols(name+'_z')
		self.t=syp.symbols(name+'_t')
		self.Dx=syp.symbols(name+'_Dx')
		self.Dy=syp.symbols(name+'_Dy')
		self.Dz=syp.symbols(name+'_Dz')
		self.expr=(1/(syp.sqrt(self.Dx*self.Dy*self.Dz)*(4*syp.pi*self.t)**(3/2)))*syp.exp(-((((self.x**2 /self.Dx)+(self.y**2 / self.Dy)+(self.z**2 /self.Dz))/(4*self.t))))
		space_coords=[self.x,self.y,self.z]
		self.expr=self.expr.subs({space_coords[i]:coord_convert(space_coords,[[1,0,0],[0,1,0],[0,0,1]],source_position,[[1,0,0],[0,1,0],[0,0,1]],[0,0,0])[i] for i in range(0,space_coords)})
		
	def get_expr(self):
		return self.expr
	
	def coeff_expr(self,wind):
		w_expr=wind.get_expr().subs(wind.t,self.t)
		R= CoordSys3D('R')
		var_dic={self.x:R.x,self.y:R.y,self.z:R.z}
		return scalar_potential((((self.expr.diff(x)+w_expr[0])*R.i)+(self.expr.diff(y)+w_expr[1]*R.j)+(self.expr.diff(z)+w_expr[2]*R.k)).subs(var_dic),R).subs(dreflect(var_dic))
	
	
	
class Dgas:
	def __init__(self,name,std_x,std_y,std_z):
		self.name=name
		self.std_x=std_x
		self.std_y=std_y
		self.std_z=std_z
		self.stdval=[std_x,std_y,std_z]
	def get_cor_val(self,abs_tmpr=273.15+25,prss=101):# unit : C,kPa
		return vamp((101/prss) *(abs_tmpr**(3/2)/(273.15+25)**(3/2)),self.stdval)
		
class GasMonitor:
	def __init__(self,data,position):  
		#data[data0,data1,data2....] ,30 lines at least ,newer data at top 
		#position:[x,y,z]
		self.data=data
		self.position=position
	def test(self):
		exce=avg(self.data[1:30])
		stddev=nup.sqrt(variance(self.data[1:30]))
		if self.data[0]-exce > exce+3*stddev :
			return 1
		elif self.data[0]-exce < exce+3*stddev :
			return -1
		else:
			return 0
	def get_newval(self):
		return self.data[0]

class SourceDector:
	def __init__(self,name,monitors):
		#monitors:[GasMonitor0,GasMonitor1,...]
		self.name=name
		self.monitors=monitors
		self.geo_center=vavg([i.position for i in monitors])
		
	def raw_center(self):
		return vavg(vsum([vamp(i.get_newval(),i.position) for i in self.monitors]))



class Predictor:
	def __init__(self,name):
		self.name=name
		self.x=syp.symbols(name+'_x')
		self.y=syp.symbols(name+'_y')
		self.z=syp.symbols(name+'_z')
		self.t=syp.symbols(name+'_t')
		self.coords=[self.x,self.y,self.z,self.t]
	def get_value(self,gauss_model,gas_monitor,env_discriptor,dgas,temp,pres,wind,coords,time):
		c_expr=gauss_model.coeff_expr(wind)
		phi_0=(gas_monitor.get_newval()-avg(gas_monitor.data))/c_expr.subs({self.coords[i]:(gas_monitor.position+[1])[i] for i in range(0,len(self.coords))}).subs(gauss_model.D,dgas.get_cor_val(temp,pres))
		c_expr=c_expr*phi_0
		return convol(syp.Piecewice((1,syp.And(t>0,t<time)),(0,True)), c_expr.subs({self.coords[i]:(coord+[times])[i] for i in range(0,len(self.coords))}).subs(gauss_model.D,dgas.get_cor_val(temp,pres)).evalf()*(1-env_discriptor.decrease+env_discriptor.expr).subs({{env_discriptor.coords[i]:(coord)[i] for i in range(0,len(env_discriptor.coords))}}))
	def get_lbdfy(self):
		pass
	
		
		
