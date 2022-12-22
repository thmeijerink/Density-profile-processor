# -*- coding: utf-8 -*-
"""
Created on Wed Aug 11 11:13:55 2021

@author: THMEI4
"""


#%% Add tools
import numpy as np
import pandas as pd

from scipy.optimize import fsolve
# import matploltib to plot data
import matplotlib.pyplot as plt

import scipy.optimize as opt

# import seaborn
import seaborn as sns

# set the context of the plot
sns.set(context='talk')
clear_bkgd = {'axes.facecolor':'none', 'figure.facecolor':'none'}
sns.set(style='ticks', context='talk', color_codes=True, rc=clear_bkgd)
plt.rcParams['axes.facecolor'] = 'w'


#%% Import data
df= pd.read_excel('input file from density profile .DL1 reader here.xlsx')
Outputlocation='Add output location here'
df2 = df.rename(columns = {'Position': 'X', 'K x Log': 'Y'}, inplace = False)


df2.head(10)
#dfx=df2[['Density', 'Thickness']].copy()
#%%Get data
#all but the core versus surface information

compoundData = df2.groupby(['sample'])
fitData = []
for name,group in compoundData:
    SampleID= name
    curfit=dict(zip(['sample'],[SampleID]))
    curfit['Peakleft']=group.Y[group.Xround<=group.Xround.max()*0.5].max()
    curfit['Peakright']=group.Y[group.Xround>=group.Xround.max()*0.5].max()
    curfit['Min']=group.Y[(group.Xround>=2)&(group.Xround<=group.Xround.max()-2)].min()
    curfit['at 3mmleft']=group.Y[group.Xround==3].mean()
    curfit['at 3mmright']=group.Y[group.Xround==group.Xround.max()-3].mean()
    fitData.append(curfit)
fitCompound = [ item['sample'] for item in fitData]
fitData=pd.DataFrame(fitData)
fitData
Output=fitData

#%%Def code
#Sigmoid
def form(x,b,c,d,e):
    '''This function is basically a copy of the LL.4 function from the R drc package with
    - b: hill slope
    - c: min response
    - d: max response
    - e: EC50'''
    return(c+(d-c)/(1+np.exp(b*(np.log(x)-np.log(e)))))

#calculating EC15
def f(x,*Params):
    c,b,d,e,IC15=Params
    y=(c+(d-c)/(1+np.exp(b*(np.log(x)-np.log(e)))))-IC15
    return y


#%% select data in left and right

data=df2[['sample','Y','Xround']]
compoundData = data.groupby(['sample'])
dataleft=pd.DataFrame()
dataright=pd.DataFrame()

for name,group in compoundData:
    temp=group[group.Xround<=group.Xround.max()*0.5]
    dataleft = pd.concat([dataleft,temp])

for name,group in compoundData:
    group.Xround=(group.Xround-group.Xround.max())*-1
    temp=group[group.Xround<=group.Xround.max()*0.5]
    dataright = pd.concat([dataright,temp])

#%%leftside    
    
compoundData = dataleft.groupby(['sample'])
fitData = []
for name,group in compoundData:
    fitCoefs, covMatrix = opt.curve_fit(form, group.Xround, group.Y,p0=np.asarray([3,500,900,1]),maxfev = 10000,bounds=((-5,200,500,0), (10,800,2000,10)))
    resids = group.Y-group.Xround.apply(lambda x: form(x,*fitCoefs))
    curFit = dict(zip(['bleft','cleft','dleft','eleft'],fitCoefs))
    curFit['sample']=name
    curFit['Xminleft']=group.Xround.min()
    curFit['Xmaxleft']=group.Xround.max()
    curFit['Peakleft']=group.Y.max()
    curFit['residualsleft']=sum(resids**2)
    curFit['varianceleft']=np.var(group.Y)
    fitData.append(curFit)
fitCompound = [ item['sample'] for item in fitData]

#Show table of fits
fitTable = pd.DataFrame(fitData).set_index('sample')
fitTable['Rsquaredleft']=1-(fitTable.residualsleft)/(fitTable.varianceleft**2)
fitTable['maxleft']=(fitTable.cleft+(fitTable.dleft-fitTable.cleft)/(1+np.exp(fitTable.bleft*(np.log(fitTable.Xminleft)-np.log(fitTable.eleft)))))
fitTable['minleft']=(fitTable.cleft+(fitTable.dleft-fitTable.cleft)/(1+np.exp(fitTable.bleft*(np.log(fitTable.Xmaxleft)-np.log(fitTable.eleft)))))
fitTable['Heightleft']=abs(fitTable['maxleft']-fitTable['minleft'])
fitTable['IC15left']=((fitTable['maxleft']-fitTable['minleft'])*0.15)+fitTable['minleft']
fitTable['slopeleft']=((fitTable['maxleft']-fitTable['minleft'])/2)*-1

# Make a place to store the answers
fitTable["EC15left"] = None


# Loop through the rows?
for index, coeffs in fitTable.iterrows():
    # Get the coefficients
    Params = (coeffs["cleft"],coeffs["bleft"],coeffs["dleft"],coeffs["eleft"],coeffs["IC15left"])
    # fSolve
    z = fsolve(f,2,args=Params)
    # Set the answers
    fitTable.loc[index,"EC15left"] = z[0]

df10 = pd.merge(dataleft,
                      fitTable,
                      on ='sample',
                      how ='outer')

compoundData2 = df10.groupby(['sample'])
fitData2 = []
for name,group in compoundData2:
    curFit2 = dict()
    curFit2['sample']=name
    curFit2['Surface density left']=group.Y[group.Xround<=group.EC15left].mean()
    curFit2['Core density left']=group.Y[(group.Xround>=group.EC15left)].mean()
    fitData2.append(curFit2)
fitCompound = [ item['sample'] for item in fitData2]

#Show table of fits
fitTable2 = pd.DataFrame(fitData2).set_index('sample')
fitTable2
fitTable = pd.merge(fitTable,
                      fitTable2,
                      on ='sample',
                      how ='outer')

Output['Surface thickness left']=fitTable['EC15left'].tolist()
Output['Surface density left']=fitTable2['Surface density left'].tolist()
Output['Core density left']=fitTable2['Core density left'].tolist()

#%%right side
compoundData = dataright.groupby(['sample'])
fitData = []
for name,group in compoundData:
    fitCoefs, covMatrix = opt.curve_fit(form, group.Xround, group.Y,p0=np.asarray([3,500,900,1]),maxfev = 10000,bounds=((-5,200,500,0), (10,800,2000,10)))
    resids = group.Y-group.Xround.apply(lambda x: form(x,*fitCoefs))
    curFit = dict(zip(['bright','cright','dright','eright'],fitCoefs))
    curFit['sample']=name
    curFit['Xminright']=group.Xround.min()
    curFit['Xmaxright']=group.Xround.max()
    curFit['Peakright']=group.Y.max()
    curFit['residualsright']=sum(resids**2)
    curFit['varianceright']=np.var(group.Y)
    fitData.append(curFit)
fitCompound = [ item['sample'] for item in fitData]

#Show table of fits
fitTable = pd.DataFrame(fitData).set_index('sample')
fitTable['Rsquaredright']=1-(fitTable.residualsright)/(fitTable.varianceright**2)
fitTable['maxright']=(fitTable.cright+(fitTable.dright-fitTable.cright)/(1+np.exp(fitTable.bright*(np.log(fitTable.Xminright)-np.log(fitTable.eright)))))
fitTable['minright']=(fitTable.cright+(fitTable.dright-fitTable.cright)/(1+np.exp(fitTable.bright*(np.log(fitTable.Xmaxright)-np.log(fitTable.eright)))))
fitTable['Heightright']=abs(fitTable['maxright']-fitTable['minright'])
fitTable['IC15right']=((fitTable['maxright']-fitTable['minright'])*0.15)+fitTable['minright']
fitTable['sloperight']=((fitTable['maxright']-fitTable['minright'])/2)*-1

# Make a place to store the answers
fitTable["EC15right"] = None


# Loop through the rows?
for index, coeffs in fitTable.iterrows():
    # Get the coefficients
    Params = (coeffs["cright"],coeffs["bright"],coeffs["dright"],coeffs["eright"],coeffs["IC15right"])
    # fSolve
    z = fsolve(f,2,args=Params)
    # Set the answers
    fitTable.loc[index,"EC15right"] = z[0]

df10 = pd.merge(dataright,
                      fitTable,
                      on ='sample',
                      how ='outer')
compoundData2 = df10.groupby(['sample'])
fitData2 = []
for name,group in compoundData2:
    curFit2 = dict()
    curFit2['sample']=name
    curFit2['Surface density right']=group.Y[group.Xround<=group.EC15right].mean()
    curFit2['Core density right']=group.Y[(group.Xround>=group.EC15right)].mean()
    fitData2.append(curFit2)
fitCompound = [ item['sample'] for item in fitData2]

#Show table of fits
fitTable2 = pd.DataFrame(fitData2).set_index('sample')
fitTable2
fitTable = pd.merge(fitTable,
                      fitTable2,
                      on ='sample',
                      how ='outer')
fitTable.reindex()
Output['Surface thickness right']=fitTable['EC15right'].tolist()
Output['Surface density right']=fitTable2['Surface density right'].tolist()
Output['Core density right']=fitTable2['Core density right'].tolist()


#%% Create output
outputlocation=Outputlocation+'Densityprofileanalysis.xlsx'
writer = pd.ExcelWriter(outputlocation, engine='xlsxwriter')
Output.to_excel(writer, sheet_name='Sheet1')
writer.save()
