import ilo, time, math
#-----------------------------------------------------------------------------
# RGB values for the potential colors
potential_color_values = {
    'brown': (108, 94, 66),
    'green': (55, 114, 92),
    'yellow': (101, 101, 60),
    'blue': (60, 92, 115),
    'orange': (140, 75, 50),
    'pink': (109, 71, 90),
    'white': (74, 97, 87)
}
#-----------------------------------------------------------------------------
ilo.connection()
print('ilo est connecte')
time.sleep(2)
ilo.stop()

# ----------------------------------------------------------------------------
def calculate_distance(color1, color2):
    r1, g1, b1 = color1
    r2, g2, b2 = color2
    return math.sqrt((r2 - r1)**2 + (g2 - g1)**2 + (b2 - b1)**2)

def find_closest_color(rgb_value, color_values):
    closest_color = None
    min_distance = float('inf')
    
    for color_name, color_rgb in color_values.items():
        distance = calculate_distance(rgb_value, color_rgb)
        if distance < min_distance:
            min_distance = distance
            closest_color = color_name
    
    return closest_color


while(1):
    
    color = ilo.get_color_rgb(False)
    print(color)
           
    red   = int(color[0])
    green = int(color[1])
    blue  = int(color[2])
    
    input_rgb = (red, green, blue)
    closest_color = find_closest_color(input_rgb, potential_color_values)
    print(f"The closest color is: {closest_color}")

    if closest_color == 'blue':
        ilo.step('front')
        time.sleep(1)
    
    elif closest_color == 'orange':
        ilo.step('back')
        time.sleep(1)
    
    else:
        time.sleep(1)
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
