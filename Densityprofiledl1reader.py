# -*- coding: utf-8 -*-
"""
Created on Wed Aug 25 10:08:12 2021

@author: THMEI4
"""

#%%
import glob
import xmltodict as xml
import pandas as pd
import os
import re

#%%Input needed
#Place all files per group/material in 1 folde
Source = 'Here the directory of where the folder with .dl1 files is'
Folder = 'Folder name of .dl1 files here'
Nameoutput=Folder

Arrangedata=0 #Highest peak at 1 side
Meanoutput=1 #Give mean profile as output
Meanfrommiddle=0 #Give mean profile with "centered" data
Headeroutput=1 #give header as output

Inputfolder=Source+Folder+'/'
#%%Arrange data
Folders = os.listdir(Inputfolder)
def myround(x, base=0.05):
    return base * round(x/base)

df=[]
header=[]
for i in Folders:
    
    for filename in glob.glob(os.path.join(Inputfolder+i, '*.dl1')):
        with open(os.path.join(os.getcwd(), filename), 'r') as f: # open in readonly mode
           raw_data = xml.parse(f.read())
           data = pd.DataFrame(raw_data['DensityProfil']['Profile'])
           head= raw_data['DensityProfil']['Header']
           head=pd.DataFrame(head, columns=head.keys(),index=[0])
           head=head.iloc[: , :5]
           #head['Hour']=int(re.sub("[^0-9]", "", Folder))
           head['sample']=filename.replace(Inputfolder+i[0],'')
           head['Type']=filename.replace(Inputfolder,'')[:filename.replace(Inputfolder,'').find('\\')]
           head['File']=filename
           #data['Hour']=int(re.sub("[^0-9]", "", Folder))
           data['sample']=filename.replace(Inputfolder+i[0],'')
           data['Type']=filename.replace(Inputfolder,'')[:filename.replace(Inputfolder,'').find('\\')]
           data['File']=filename
           half=(data['x-Value'].astype(float).max()*0.5)
           Yperc=min(data['x-Value'].astype(float), key=lambda x:abs(x-half))
           data['Xcenter']=data['x-Value'].astype(float)-Yperc
           header.append(head)
           df.append(data)
df = pd.concat(df)
header=pd.concat(header)
df['x-Value']=df['x-Value'].astype(float)
df['y-Value']=df['y-Value'].astype(float)
df = df.rename(columns={'x-Value': 'X', 'y-Value': 'Y'})


df['Xround']=myround(df['X'])
df['XroundC']=myround(df['Xcenter'])

#%%Putting high peak first

if Arrangedata==1:
    average=[]

    compoundData = df.groupby(['File'])
    fitData = []
    for name,group in compoundData:
        File= name
        curfit=dict(zip(['File'],[File]))
        curfit['Peakleft']=group.Y[group.X<=(group.X.max()*0.5)].max()
        curfit['Peakright']=group.Y[group.X>=(group.X.max()*0.5)].max()
        curfit['Peakmax']=max(group.Y[group.X<=(group.X.max()*0.5)].max(),group.Y[group.X>(group.X.max()*0.5)].max())
        curfit['Thickness']=group.X.max()
        fitData.append(curfit)
    fitCompound = [ item['File'] for item in fitData]
    fitData=pd.DataFrame(fitData)
    fitData

    dfarranged = pd.merge(df,
                      fitData,
                      on ='File',
                      how ='inner')
    dfarranged['X_left']=myround(dfarranged['X'][dfarranged['Peakleft']==dfarranged['Peakmax']])
    dfarranged['X_right']=myround((dfarranged['X'][dfarranged['Peakright']==dfarranged['Peakmax']]-dfarranged['Thickness'][dfarranged['Peakright']==dfarranged['Peakmax']])*-1)
    dfarranged['X_x']=dfarranged['X_right'].combine_first(dfarranged['X_left'])
    dfarranged=dfarranged[['Type','Hour','File', 'X','X_x','Y']].copy()
    dfarranged = dfarranged.rename(columns={'X':'Xoriginal','X_x': 'Xround'})
    
    outputlocation=Inputfolder+"/"+Nameoutput+"arranged.xlsx"
    writer = pd.ExcelWriter(outputlocation, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1')
    writer.save()

#%%Calculating mean curve
if Meanoutput==1:
    y=df.groupby(['Type'])

    Mean=[]
    for i in y:
        Meanprofile=i[1].groupby(['Xround'])['Y'].mean()
        Meanprofile=pd.DataFrame(Meanprofile)
        Meanprofile=Meanprofile.reset_index()
        Meanprofile.rename(columns={ Meanprofile.columns[1]: "Y" }, inplace = True)
        Meanprofile['Type']=i[0]
        #Meanprofile['Hour']=i[1]['Hour'].mean()
        xmin=max(df.groupby(['File'])['Xround'].min())
        xmax=min(df.groupby(['File'])['Xround'].max())
        #Meanprofile=Meanprofile[(Meanprofile['Xround']>=xmin ) & (Meanprofile['Xround']<=xmax)]
        Meanprofile['Folder']=Folder
        Mean.append(Meanprofile)
    Meanprofile=pd.concat(Mean,axis=0)
    if Meanfrommiddle==1:
        y=df.groupby(['Type'])

        Mean=[]
        for i in y:
            Meanprofile=i[1].groupby(['XroundC'])['Y'].mean()
            Meanmin=i[1].groupby(['File'])['XroundC'].min().mean()
            Meanmax=i[1].groupby(['File'])['XroundC'].max().mean()
            Meanprofile=pd.DataFrame(Meanprofile)
            Meanprofile=Meanprofile.reset_index()
            Meanprofile.rename(columns={ Meanprofile.columns[1]: "Y" }, inplace = True)
            Meanprofile['Type']=i[0]
            #Meanprofile['Hour']=i[1]['Hour'].mean()
            xmin=max(df.groupby(['File'])['XroundC'].min())
            xmax=min(df.groupby(['File'])['XroundC'].max())
            #Meanprofile=Meanprofile[(Meanprofile['Xround']>=xmin ) & (Meanprofile['Xround']<=xmax)]
            Meanprofile['Folder']=Folder
            Meanprofile=Meanprofile[(Meanprofile['XroundC']<=Meanmax)&(Meanprofile['XroundC']>=Meanmin)]
            Mean.append(Meanprofile)
        Meanprofile=pd.concat(Mean,axis=0)
    
    outputlocation=Inputfolder+"/"+Nameoutput+"mean.xlsx"
    writer = pd.ExcelWriter(outputlocation, engine='xlsxwriter')
    Meanprofile.to_excel(writer, sheet_name='Sheet1')
    writer.save()

#%%Output
outputlocation=Inputfolder+"/"+Nameoutput+".xlsx"
writer = pd.ExcelWriter(outputlocation, engine='xlsxwriter')
df.to_excel(writer, sheet_name='Sheet1')
writer.save()


if Headeroutput==1:
    outputlocation=Inputfolder+"/"+Nameoutput+"Header.xlsx"
    writer = pd.ExcelWriter(outputlocation, engine='xlsxwriter')
    header.to_excel(writer, sheet_name='Sheet1')
    writer.save()