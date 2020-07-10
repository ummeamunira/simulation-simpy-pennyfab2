'''pennyfab -conwip-with some 
metrics in dataframe:worked'''


import itertools
import random
from random import uniform
import simpy
import pandas as pd


RANDOM_SEED = 42
conwip=10  
hour=8
day=50
SIM_TIME = hour*day+2.5            # Simulation time in hour

df=[]

def fab(name, env, punch, stamp, rim, deburr, job_released, FP, df):
    print('Job released for %s at %.1f' % (name, env.now))
    with punch.request() as req:
        start = env.now
        yield req
        d={'penny':name, 'started_punch':env.now}
        print ('{} is requested for punch {}'.format(name,env.now))
        yield env.timeout(2+float(int(uniform(1,2/4*10)))/100)
        d['finished_punch']=env.now
        
        print ('%s finished punch at %0.1f' % (name,env.now))
        df.append(d)
        
    with stamp.request() as req:
        yield req
        print ('{} is requested for stamp {}'.format(name,env.now))
        d['started_stamp']=env.now
        yield env.timeout(5+float(int(uniform(1,5/4*10)))/100)
        d['finished_stamp']=env.now
        
        print ('%s finished stamp at %0.1f' % (name,env.now))
        df.append(d)
        
    with rim.request() as req:
        yield req
        print ('{} is requested for rim {}'.format(name,env.now))
        d['started_rim']=env.now
        yield env.timeout(10+float(int(uniform(1,10/4*10)))/100)
        d['finished_rim']=env.now
        
        print ('%s finished rim at %0.1f' % (name,env.now))
        df.append(d)
        
    with deburr.request() as req:
        yield req
        print ('{} is requested for deburr {}'.format(name,env.now))
        d['started_deburr']=env.now
        yield env.timeout(3+float(int(uniform(1,3/4*10)))/100)
        yield FP.put(1)
        d['finished_deburr']=env.now
        d['wip in punch']=punch.count
        d['Buffer before punch']=len(punch.queue)
        d['wip in stamp']=stamp.count
        d['Buffer before stamp']=len(stamp.queue)
        d['wip in rim']=rim.count
        d['Buffer before rim']=len(rim.queue)
        d['wip in deburr']=deburr.count-1
        d['Buffer before deburr']=len(deburr.queue)
        d['Finished penny']=FP.level
        print ('%s finished deburr at %0.1f' % (name,env.now))
        df.append(d)
  
        

def jr(env,punch, stamp, rim, deburr, job_released, FP, df):
    while True:
        if punch.count+len(punch.queue)+stamp.count+len(stamp.queue)+rim.count+len(rim.queue)+deburr.count-1+len(deburr.queue)<conwip:
            yield job_released.put(1)
        yield env.timeout(0.05)

def wo_generator(env,punch, stamp, rim, deburr, job_released, FP, df):   
    for i in itertools.count():
        
        yield job_released.get(1)

        env.process(fab('penny %d' %i, env,punch, stamp, rim, deburr, job_released, FP, df))
    

print('Penny Fab')
random.seed(RANDOM_SEED)
env=simpy.Environment()
punch=simpy.Resource(env, capacity= 1) 
stamp=simpy.Resource(env, capacity= 2) 
rim=simpy.Resource(env, capacity=6) 
deburr=simpy.Resource(env, capacity= 2) 

job_released=simpy.Container(env, capacity=conwip, init=conwip)
FP=simpy.Container(env, 500, init=0)


env.process(wo_generator(env, punch, stamp, rim, deburr, job_released, FP, df))
env.process(jr(env,punch, stamp, rim, deburr, job_released, FP, df))
env.run(until=SIM_TIME)
data1=pd.DataFrame(df)
data1=data1.drop_duplicates()
data1['cycle time']=data1['finished_deburr']-data1['started_punch']
data1['throughput']=data1['Finished penny']/data1['finished_deburr']
data1['WIP']=data1['Buffer before punch']+data1['Buffer before stamp']+data1['Buffer before rim']+data1['Buffer before deburr']+data1['wip in punch']+data1['wip in stamp']+data1['wip in rim']+data1['wip in deburr']




#data1.to_csv("data-c.csv", sep=',',index=False)

data1
