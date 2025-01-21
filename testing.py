import pygame as pg
import sys
import numpy as np
from math import*
from random import*
pg.init()


width,height=1100,600
screen=pg.display.set_mode((width,height))
clock=pg.time.Clock()
font=pg.font.SysFont(None,32)


class Particle_System:
    def __init__(self,particle_num,wid,connections,lengths,stiffnesses,grav,colour):
        self.locs=[np.array([300+i,300+i]) for i in range(particle_num)]
        self.old_locs=self.locs.copy()
        self.connections=connections
        self.stiffnesses=stiffnesses
        self.grav=grav
        self.forces=[np.array([0,grav]) for i in range(particle_num)]
        self.particle_num=particle_num
        self.wid=wid
        self.connection_lengths=lengths
        self.colour=colour
    def move(self):
        for i in range(self.particle_num):
            temp=self.locs[i].copy()
            self.locs[i]=self.locs[i]*1.99-self.old_locs[i]*0.99+self.forces[i]
            self.old_locs[i]=temp
    def keep_boxed(self):
        for i in range(self.particle_num):
            self.locs[i]=np.array([min(width-self.wid/2,max(self.wid/2,self.locs[i][0])),
                                   min(height-self.wid/2,max(self.wid/2,self.locs[i][1]))])
    def draw_circles(self):
        for i in range(self.particle_num):
            pg.draw.circle(screen,self.colour,self.locs[i],5)
    def draw_lines(self):
        for i in range(len(self.connections)):
            if self.stiffnesses[i]==1:
                pg.draw.line(screen,self.colour,
                            self.locs[self.connections[i][1]],self.locs[self.connections[i][0]],self.wid)
       
    def connect(self):
        for i,indexes in enumerate(self.connections):
            difference=self.locs[indexes[0]]-self.locs[indexes[1]]


            length=sqrt(np.dot(difference,difference))
            if length==0:
                continue
            ratio_of_length=(length-self.connection_lengths[i])/length


            self.locs[indexes[1]]=self.locs[indexes[1]]+difference*0.5*ratio_of_length*self.stiffnesses[i]
            self.locs[indexes[0]]=self.locs[indexes[0]]-difference*0.5*ratio_of_length*self.stiffnesses[i]


    def constrain(self,accuracy):
        for j in range(accuracy):
            self.keep_boxed()
            self.connect()
    def reset_forces(self):
        self.forces=[np.array([0,self.grav]) for i in range(self.particle_num)]
    def ccw(self,p1,p2,p3):
        return (p3[1]-p1[1])*(p2[0]-p1[0])>(p2[1]-p1[1])*(p3[0]-p1[0])
    def check_collision_between_segments(self,connection,points):
        not_same=self.ccw(self.locs[connection[0]],points[0],
                          points[1])!=self.ccw(self.locs[connection[1]],points[0],points[1])
        not_same1=self.ccw(self.locs[connection[0]],self.locs[connection[1]],
                          points[0])!=self.ccw(self.locs[connection[0]],self.locs[connection[1]],points[1])
        return not_same and not_same1
    def one_mag_vector(self,points):
        difference=np.array([points[0][0]-points[1][0],points[0][1]-points[1][1]])
        one_mag_point=difference/(hypot(difference[0],difference[1]))
        return one_mag_point
                       


class Ragdoll(Particle_System):
    def __init__(self,scale,grav,speed,jump_power,colour,health):
        arms=[45 for i in range(4)]
        legs=[55 for i in range(4)]
        body_size=[60]+arms+legs+[10,70,20,40]
        connects=[(0,1),(0,2),(0,4),(2,3),(4,5),(1,6),(1,8),(6,7),(8,9),(0,10),(10,1),(6,8),(2,4)]
        stiffnesses=[1,1,1,1,1,1,1,1,1,1,0.5,0.01,grav/5]
        for i in range(len(body_size)):
            body_size[i]=scale*body_size[i]
        super().__init__(11,int(8*scale),connects,body_size,stiffnesses,grav,colour)
        self.speed=speed
        self.jump_power=jump_power
        self.jumping=False
        self.rocked=False
        self.rocked_time=1000000
        self.rocked_count=0
        self.hits=0
        self.upright=False
        self.health=health
    def upright_forces(self,timer):
        if not(self.rocked) and self.upright:
            self.forces[10]=np.array([0,-self.grav*10])
            self.forces[9]=np.array([0,self.grav*4])
            self.forces[7]=np.array([0,self.grav*4])
        elif timer-self.rocked_count==self.rocked_time:
            self.rocked=False


    def walk(self,direction):
        if not(self.rocked):
            self.locs[9][0]+=direction*self.speed
    def jump(self):
        if not(self.rocked):
            self.forces[1][1]=self.jump_power
            self.forces[6][1]=-self.jump_power
            self.forces[8][1]=-self.jump_power
    def reset_jumping(self):
        self.jumping=True
        if abs(self.locs[9][1]-(height-self.wid/2))<1 or abs(self.locs[7][1]-(height-self.wid/2))<1:
            self.jumping=False
            self.upright=True
        else:
            self.upright=False
    def punching(self,point):
        if not(self.rocked):
            #index=choice([[3,2],[5,4],[9,8],[7,6]])
            index=choice([[9,8],[7,6]])
            #index=choice([[3,2],[5,4]])
            difference=np.array([point[0]-self.locs[index[1]][0],point[1]-self.locs[index[1]][1]])
            one_mag_point=difference/(hypot(difference[0],difference[1]))
            if index==[3,2] or index==[5,4]:
                self.locs[index[0]]=self.locs[index[1]]+one_mag_point*self.connection_lengths[2]*3
                self.old_locs[index[0]]=self.locs[index[1]]+one_mag_point*self.connection_lengths[2]*2
            else:
                self.locs[index[0]]=self.locs[index[1]]+one_mag_point*self.connection_lengths[2]*3
                self.old_locs[index[0]]=self.locs[index[1]]+one_mag_point*self.connection_lengths[2]*1


    def get_punched(self,points,power,timer):
        if self.check_collision_between_segments(self.connections[0],points) and not(self.rocked):
            force=self.one_mag_vector(points)*power
            self.forces[0]=force
            self.forces[1]=force
            self.hits+=1
           
        elif hypot(points[0][0]-self.locs[10][0],
                   points[0][1]-self.locs[10][1])<2.5*self.wid and not(self.rocked):
            self.hits+=2
            force=self.one_mag_vector(points)*power*2
            self.forces[10]=force
        if self.hits>=self.health:
                self.rocked=True
                self.rocked_count=timer
                self.hits=0




    def draw_ragdoll(self):
        self.draw_lines()
        pg.draw.circle(screen,(self.colour),self.locs[-1],self.wid*2.5)
        #pg.draw.circle(screen,(self.colour),self.locs[3],self.wid*1.5)
        #pg.draw.circle(screen,(self.colour),self.locs[5],self.wid*1.5)




def points_and_connections(mouse_pos,points,connections,lengths,selected_index):


    carry=True
    for point in points:
        if hypot(mouse_pos[0]-point[0],mouse_pos[1]-point[1])<10:


            if len(selected_index)==1:
                connections.append((selected_index[0],points.index(point)))
                lengths.append(hypot(point[0]-points[selected_index[0]][0],
                                     point[1]-points[selected_index[0]][1]))
                selected_index=[]


            else:
                selected_index.append(points.index(point))
            carry=False
            break
    if carry:
        points.append(mouse_pos)
    return points,connections,lengths,selected_index


scale=0.5




ragdoll=Ragdoll(scale,0.5,1,100,(255,255,255),500)
npcs=[Ragdoll(scale,0.5,0.1,50,(145,0,0),500) for i in range(1)]
moving=False
direction=0
selected_point='None'
punch=False
timer=0
power=100
while True:
    timer+=1
    screen.fill((50,100,150))
    mouse_pos=pg.mouse.get_pos()
    ragdoll.reset_forces()
    for npc in npcs:
        npc.reset_forces()
        npc.upright_forces(timer)
    ragdoll.upright_forces(timer)
    for event in pg.event.get():
        if event.type==pg.QUIT:
            pg.quit()
            sys.exit()
        if event.type==pg.MOUSEBUTTONDOWN:
            punch=True
        if event.type==pg.MOUSEBUTTONUP:
            punch=False
        if event.type==pg.KEYDOWN:
            if event.key==pg.K_d:
                direction=1
            elif event.key==pg.K_a:
                direction=-1
            if event.key==pg.K_w:
                if not(ragdoll.jumping):
                    ragdoll.jump()
            if event.key==pg.K_p:
                punch=True
        if event.type==pg.KEYUP:
            if event.key==pg.K_a or event.key==pg.K_d:
                direction=0
    for npc in npcs:
        #npc.get_punched([ragdoll.locs[3],ragdoll.locs[2]],power,timer)
        #npc.get_punched([ragdoll.locs[5],ragdoll.locs[4]],power,timer)
        npc.get_punched([ragdoll.locs[9],ragdoll.locs[8]],power,timer)
        npc.get_punched([ragdoll.locs[7],ragdoll.locs[6]],power,timer)


        #ragdoll.get_punched([npc.locs[3],npc.locs[2]],power,timer)
        #ragdoll.get_punched([npc.locs[5],npc.locs[4]],power,timer)
        ragdoll.get_punched([npc.locs[9],npc.locs[8]],power,timer)
        ragdoll.get_punched([npc.locs[7],npc.locs[6]],power,timer)
   
    ragdoll.move()
    for npc in npcs:
        npc.move()
    ragdoll.walk(direction)
   
    for npc in npcs:
        if timer%randint(1,40)==1:    
            npc.punching(ragdoll.locs[10])
    if timer%randint(1,40)==1:
        ragdoll.punching(npcs[0].locs[10])
    if punch:
       ragdoll.punching(mouse_pos)
       punch=False
    ragdoll.constrain(1)
    for npc in npcs:
        npc.constrain(1)
   
   
    for npc in npcs:
        npc.draw_ragdoll()
        npc.reset_jumping()
    ragdoll.draw_ragdoll()    
    ragdoll.reset_jumping()
    text=font.render(f'fps:{int(clock.get_fps())}',True,(255,0,0))
    screen.blit(text,(0,0))
    health=font.render(f'health:{ragdoll.health-ragdoll.hits}',True,(255,0,0))
    screen.blit(health,(100,0))
    pg.display.update()
    clock.tick(60)



