from earsketch import *

init()
setTempo(126) 

# --- SOUND PALETTE ---
beat = HOUSE_MAIN_BEAT_002
percussion = HOUSE_BREAKBEAT_001
bass = HOUSE_DEEP_BASS_001
lead = TECHNO_SYNTHPLUCK_001
chords = Y01_HI_HATS_1

# --- 1. THE BUILD-UP ---
fitMedia(chords, 1, 1, 21) 
fitMedia(percussion, 2, 1, 21)

# Effect: Filter sweep (Muffled -> Clear)
setEffect(2, FILTER, FILTER_FREQ, 500, 1, 8000, 5)

# --- 2. THE DROP ---
fitMedia(beat, 3, 5, 21)
fitMedia(bass, 4, 5, 21)

# --- 3. THE HOOK ---
fitMedia(lead, 5, 5, 21)

# --- 4. MIXING TRICKS ---

# Trick 1: Sidechain (The "Pumping" Effect)
# FIX: Removed the conflicting volume fade from lines 19-20 so this works smoothly.
for measure in range(5, 21):
    setEffect(1, VOLUME, GAIN, -15, measure, 0, measure + 0.5) 

# Trick 2: Stereo Image (Width)
setEffect(5, PAN, LEFT_RIGHT, 30)  
setEffect(1, PAN, LEFT_RIGHT, -30) 

# Trick 3: Pitch Rise Transition
setEffect(2, PITCHSHIFT, PITCHSHIFT_SHIFT, 0, 8, 2, 9)
setEffect(2, PITCHSHIFT, PITCHSHIFT_SHIFT, 0, 9)

# --- 5. ENDING
# It fades everything out from measure 17 to 21.
setEffect(0, VOLUME, GAIN, 0, 17, -60, 21)

finish()