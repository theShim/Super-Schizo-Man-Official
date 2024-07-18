import numpy as np
import matplotlib.pyplot as plt

# Define a function to create pixel art for Masked Hero
def create_masked_hero():
    # Create an 8x8 grid of RGB values
    hero = np.zeros((8, 8, 3), dtype=int)
    
    # Colors
    mask_color = [255, 0, 0]  # Red mask
    body_color = [0, 0, 255]  # Blue body
    eye_color = [255, 255, 255]  # White eyes
    
    # Design the mask
    hero[1, 2:6] = mask_color
    hero[2, 1:7] = mask_color
    hero[3, 2:6] = mask_color
    
    # Design the eyes
    hero[2, 3] = eye_color
    hero[2, 4] = eye_color
    
    # Design the body
    hero[4:7, 2:6] = body_color
    
    return hero

# Define a function to create pixel art for Shadow Figure
def create_shadow_figure():
    # Create an 8x8 grid of RGB values
    shadow = np.zeros((8, 8, 3), dtype=int)
    
    # Color
    shadow_color = [50, 50, 50]  # Dark grey shadow
    eye_color = [255, 0, 0]  # Red eyes
    
    # Design the shadow figure
    shadow[1:7, 2:6] = shadow_color
    shadow[2, 3:5] = [0, 0, 0]  # Eye sockets
    
    # Design the eyes
    shadow[2, 3] = eye_color
    shadow[2, 4] = eye_color
    
    return shadow

# Create the characters
masked_hero = create_masked_hero()
shadow_figure = create_shadow_figure()

# Plot the characters
fig, axes = plt.subplots(1, 2, figsize=(10, 5))

axes[0].imshow(masked_hero, interpolation='nearest')
axes[0].set_title('Masked Hero')
axes[0].axis('off')

axes[1].imshow(shadow_figure, interpolation='nearest')
axes[1].set_title('Shadow Figure')
axes[1].axis('off')

plt.show()
