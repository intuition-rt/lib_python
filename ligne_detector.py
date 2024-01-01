import ilo, time

ilo.connection()
print('ilo est connecte')
time.sleep(2)
ilo.stop()

limit_val = 25

left_clear   = -1
middle_clear = -1
right_clear  = -1


#if clear_data[0] == -1 eror case do noting waiting next value
def get_info_captor():
    global left_clear, middle_clear, right_clear
    clear_data = ilo.get_color_clear(True)
    if clear_data[0] == -1:
        print('Error on captor data')
        return False
    else:
        left_clear   = int(clear_data[0])
        middle_clear = int(clear_data[1])
        right_clear  = int(clear_data[2])
        return True

def get_darker():
    global left_clear, middle_clear, right_clear
    
    if (left_clear <= middle_clear) and (left_clear <= right_clear):                #choix arbitaire de tourner à gauche propritèrement
        darker = 'left'
    elif (middle_clear <= left_clear) and (middle_clear <= right_clear):
        darker = 'middle'
    elif (right_clear <= middle_clear) and (right_clear <= left_clear):
        darker = 'right'
    else:
        darker = 'None'
    return darker
    

def road_research():
    get_info_captor()
    if (left_clear <= limit_val) or (middle_clear <= limit_val) or (right_clear <= limit_val)  :
        return True
    else:
        return False
    

def main():
    
    while True:
        
        if (road_research() == False):      #new mesure is get here
            print('ilo is looking for road ...')    
            ilo.move('front', 10)
            #time.sleep(0.1)
          
        else:
            if (get_darker() == 'left'):
                #ilo.move('rot_trigo', 20)
                ilo.direct_control(135,125,112)
                print('turn left')
                #◘time.sleep(0.1)
                
            elif (get_darker() == 'middle'):
                ilo.move('front', 10) 
                
                print('go ahead')
                #time.sleep(0.1)
                
            elif (get_darker() == 'right'):
                #ilo.move('rot_clock', 20)
                ilo.direct_control(135,131,142)
                print('turn right')
                #time.sleep(0.1)
                
            else:
                print('main / error on darker test')
                
main()         
            
'''         
        
while True:
    print('ilo is looking for road ...')
    clear_data = ilo.get_color_clear(True)
    print(clear_data)
    while (int(clear_data[0]) >= limit_val) and (int(clear_data[1]) >= limit_val) and (int(clear_data[2]) >= limit_val)  :
        #ilo.move('front', 10)
        clear_data = ilo.get_color_clear(False)
        print(clear_data)
        time.sleep(0.1)
        
    print('road detected')
    ilo.stop()
    
    if (int(clear_data[0]) <= limit_val):
        
        print("road on the left")
        
        while (int(clear_data[0]) <= limit_val):
            ilo.move('rot_trigo', 20)
            clear_data = ilo.get_color_clear(False)
            print(clear_data)
            time.sleep(0.1)
            ilo.move('front', 20)
            time.sleep(0.05)
            #print(clear_data)
    
    if (int(clear_data[2]) <= limit_val):
        
        print("road on the right ")
        
        while (int(clear_data[2]) <= limit_val):
            ilo.move('rot_clock', 20)
            clear_data = ilo.get_color_clear(False)
            print(clear_data)
            time.sleep(0.1)
            ilo.move('front', 20)
            time.sleep(0.05)
            #print(clear_data)
            
    if (int(clear_data[1]) <= limit_val):
        
        print("ilo is on the road")
        
        while (int(clear_data[1]) <= limit_val):
            ilo.move('front', 20)               #increase the value of speed step by step
            print('ilo move front')
            clear_data = ilo.get_color_clear(False)
            print(clear_data)
            time.sleep(0.1)
            #print(clear_data)
        
'''       