# -*- coding: utf-8 -*-

import tingbot
from tingbot import *
import json, requests

# Some thoughts
# page should be a class - we're using an object for simplicity,
# but now we've grown arms and legs and page has a bunch of functions
# that need a reference to themselves.

def fetchStatus():
    global queue
    try:
        data = requests.get(api+endpoints['queue'], timeout=5).json()
        queue = data['queue']
        return True
    except IOError:
        return False
        
def toggleQueueState():
    if queue['paused']:
        endpoint = api+endpoints['resume']
    else:
        endpoint = api+endpoints['pause']
    try:
        data = requests.get(endpoint, timeout=5).json()
        return data['status']
    except IOError:
        return False
        
def clearQueue():
    endpoint = api+endpoints['cancel']
    try:
        data = requests.get(endpoint, timeout=5).json()
        return data['status']
    except IOError:
        return False

def drawDashboardPage(page):
    x = page['x']
    # x is the leftmost edge of the page
    screen.image('sabnzbd.png', xy=(x+(dims['w']/2),20), align='top')

    speed = parseSpeed(queue['kbpersec'])

    screen.text('Speed', xy=(x+dims['pX'],90), color=colours['primary'], align='topleft', font_size=14, font=font)
    screen.text(speed, xy=(x+dims['pX'],103), color=colours['primary'], align='topleft', font_size=32, font=font)
    screen.text('Queued', color=colours['primary'], xy=(x+dims['w']-dims['pX'],90), font_size=14,  align='topright', font=font)
    screen.text(len(queue['slots']), xy=(x+dims['w']-dims['pX'],103), color=colours['primary'],  align='topright', font_size=32, font=font)
    
    if(len(queue['slots']) > 0):
        drawProgressBar(x)

def drawProgressBar(x):
    title = queue['slots'][0]['filename']
    title = title[:35] + (title[35:] and '...')
    percent = int(queue['slots'][0]['percentage'])
    progress = int((dims['w'] - 2*dims['pX'] - 4) * percent/100.0)
    
    # Using 1x1 PNGs for boxes as rects can't have negative xy vals, images can
    # Progress bar container
    screen.image('images/aqua1x1.png', xy=(x+dims['pX'], 183), scale=(280, 20), align='topleft')
    screen.image('images/navy1x1.png', xy=(x+dims['pX'] + 2, 185), scale=(276, 16), align='topleft')
    
    # Progress bar progress
    screen.image('images/aqua1x1.png', xy=(x+dims['pX'], 183), scale=(progress,20), align='topleft')
    
    # Render active file details
    screen.text(title, xy=(x+dims['w']/2, 165), color=colours['primary'],  align='center', font_size=14, font=font)
    screen.text(str(percent)+'%', xy=((x+(dims['w'])/2),193), color='white',  align='center', font_size=14, font=font)

# Takes a kb/s speed string from SABnzbd (e.g. 8453.423) and makes it nice
def parseSpeed(speed):
    if speed == '?':
        return speed
    else:
        speed = speed.split('.')
        if len(speed[0]) <= 3:
            return "%.2f" % round(float(speed[0]),2)+'Kb/s'
        elif 4 <= len(speed[0]) <= 6:
            return "%.2f" % round(float(speed[0])/1000.0,2)+'Mb/s'
        else:
            return "%.2f" % round(float(speed[0])/1000000.0,2)+'Gb/s?!'

def touchedDashboardPage(xy, action):
    return

# Draws the Control page
def drawControlPage(page):
    x = page['x']
    
    screen.image('sabnzbd.png', xy=(x+(dims['w']/2),20), align='top')
        
    for button in page['buttons']:
        drawButton(x+button['dims']['x'], button['dims']['y'], button['dims']['w'], button['dims']['h'], button['text'][button['state']], button['pressed'])
    
def drawButton(x, y, w, h, text, pressed):
    
    buttonState = 'down' if pressed else 'up'
    
    screen.image('images/'+colours['buttons'][buttonState]['border']+'1x1.png', xy=(x, y), scale=(w, h), align='topleft')
    screen.image('images/'+colours['buttons'][buttonState]['fill']+'1x1.png', xy=(x+2, y+2), scale=(w-4, h-4), align='topleft')
    screen.text(text, xy=(x+(w/2), y + 20), color=colours['buttons'][buttonState]['text'],  align='center', font_size=18, font=font)

def touchedControlPage(xy, action, page):
    pageX = page['x']

    for button in page['buttons']:
        if button['debounce'] == 0:
            if isPointInRect(xy[0], xy[1], pageX+button['dims']['x'], button['dims']['y'], pageX+button['dims']['w'], button['dims']['h']):
                if action == 'up':
                    button['pressed'] = False
                    button['action'](button, page)
                elif action == 'move' or action == 'down':
                    button['pressed'] = True

# Pygame has this, but worth spelling it out
def isPointInRect(pX, pY, rX, rY, rW, rH):
    if pX >= rX and pX <= rX + rW and pY >= rY and pY <= rY + rH:
        return True
    else:
        return False
    
def updatePosition():
    global state, q

    if state == 'transitionLeft':
        for page in q:
            page['x'] -= 21.33
        if q[0]['x'] < -dims['w']: # once page is off screen...
            q.pop(0) # knock old current page off the queue - don't need to draw anymore
            q[0]['x'] = 0 # floor current page at x:0
            state = 'display'
    elif state == 'transitionRight':
        for page in q:
            page['x'] += 21.33
        if q[0]['x'] > dims['w']: # once page is off screen...
            q.pop(0) # knock old current page off the queue - don't need to draw anymore
            q[0]['x'] = 0 # floor current page at x:0
            state = 'display'
    else:
        return

# Subtract from debounce timer, if > 0
def updateButtons():
    global q
    
    for page in q:
        for button in page['buttons']:
            if button['debounce'] > 0:
                button['debounce'] -= 2
            else:
                button['debounce'] = 0

# Button pressed event handlers
def handleToggleQueueState(button, page):
    toggleQueueState()
    button['debounce'] = 30
    if button['state'] == 'on':
        button['state'] = 'off'
    else:
        button['state'] = 'on'
    
def handleClearQueue(button, page):
    clearQueue()
    button['debounce'] = 30
    

# Sabnzdb Connection & Data Placeholders
host = tingbot.app.settings['host']
port = tingbot.app.settings['port']
apikey = tingbot.app.settings['apikey']
api = 'http://'+host+':'+port+'/sabnzbd/api?output=json&apikey='+apikey
endpoints = {'queue': '&mode=queue', 'pause': '&mode=pause', 'resume': '&mode=resume', 'cancel': '&mode=queue&name=purge'}
queue = {'speed': '?', 'kbpersec': '?', 'slots': [], 'paused': False}

# Screen / State Management
dims = {'w':320, 'h':240, 'pX':20, 'pY':20}
page = 0 # The current page, or the page we're transitioning to
pages = [
    {
        'x': 0, 
        'draw': drawDashboardPage,
        'touched': touchedDashboardPage,
        'buttons': [],
    },
    {
        'x': dims['w'], 
        'draw': drawControlPage,
        'touched': touchedControlPage,
        'buttons': [
            {
                'dims': {
                    'x': dims['pX'], 'y': 100, 'w': 280, 'h': 40
                },
                'text': {
                    'on': 'Pause Downloads', 'off': 'Resume Downloads'
                },
                'action': handleToggleQueueState,
                'state': 'on', # for toggleable buttons - is it on or off?
                'debounce': 0, # timer to prevent button being 'hit' multiple times in quick succession
                'pressed': False # so we can draw differently
            },
            {
                'dims': {
                  'x': dims['pX'], 'y': 170, 'w': 280, 'h': 40
                },
                'text': {
                    'on': 'Clear Queue', 'off': 'Clear Queue'
                },
                'action': handleClearQueue,
                'state': 'on',
                'debounce': 0, # timer to prevent button being 'hit' multiple times in quick succession
                'pressed': False
            }
        ]
    }
]
state = 'display'
colours = {
    'primary': 'aqua',
    'buttons': {
        'down': {
            'border': 'aqua',
            'fill': 'aqua',
            'text': 'navy',
        },
        'up': {
            'border': 'aqua',
            'fill': 'navy',
            'text': 'white',
        }
    }
}
font = 'fonts/SourceSansPro-Regular.ttf'
q = [pages[page]]
    

# Get fresh Sabnzbd data
@every(seconds=2)
def refresh_data():
    global state
    
    if fetchStatus():
        if state == 'disconnected':
            state = 'display'
    else:
        state = 'disconnected'
 
# Move page left  
@left_button.press
def pageLeft():
    global state, q, page, pages
    if state == 'display':
        state = 'transitionLeft'
        page = 0 if len(pages) == page+1 else page+1
        pages[page]['x'] = dims['w'] # Get new page in position
        q.append(pages[page])

# Move page right
@right_button.press
def pageRight():
    global state, q, page, pages
    if state == 'display':
        state = 'transitionRight'
        page = len(pages)-1 if page-1 < 0 else page-1
        pages[page]['x'] = -dims['w'] # Get new page in position
        q.append(pages[page])

# This is super simple event handling
@touch()
def on_touch(xy, action):
    if state == 'display':
        pages[page]['touched'](xy, action, pages[page])
        
# Logic 
def update():
    updatePosition()
    updateButtons()

# Rendering
def draw():
    screen.fill(color='navy')
    
    if state == 'disconnected':
        screen.text("Can't Connect :(", xy=(dims['w']/2, dims['h']/2), color=colours['primary'],  align='center', font_size=36, font=font)
        return
    
    for page in q:
        page['draw'](page)

# Main loop
@every(seconds=1.0/30)
def run():
    update()
    draw()
        
# Almost ready...
if fetchStatus():
    state = 'display'
else:
    state = 'disconnected'

pages[1]['buttons'][0]['state'] = 'off' if queue['paused'] else 'on' # move this when we do init properly
tingbot.run()
# -*- coding: utf-8 -*-

import tingbot
from tingbot import *
import json, requests

# Some thoughts
# page should be a class - we're using an object for simplicity,
# but now we've grown arms and legs and page has a bunch of functions
# that need a reference to themselves.

def fetchStatus():
    global queue
    try:
        data = requests.get(api+endpoints['queue'], timeout=5).json()
        queue = data['queue']
        return True
    except IOError:
        return False
        
def toggleQueueState():
    if queue['paused']:
        endpoint = api+endpoints['resume']
    else:
        endpoint = api+endpoints['pause']
    try:
        data = requests.get(endpoint, timeout=5).json()
        return data['status']
    except IOError:
        return False
        
def clearQueue():
    endpoint = api+endpoints['cancel']
    try:
        data = requests.get(endpoint, timeout=5).json()
        return data['status']
    except IOError:
        return False

def drawDashboardPage(page):
    x = page['x']
    # x is the leftmost edge of the page
    screen.image('sabnzbd.png', xy=(x+(dims['w']/2),20), align='top')

    speed = parseSpeed(queue['kbpersec'])

    screen.text('Speed', xy=(x+dims['pX'],90), color=colours['primary'], align='topleft', font_size=14, font=font)
    screen.text(speed, xy=(x+dims['pX'],103), color=colours['primary'], align='topleft', font_size=32, font=font)
    screen.text('Queued', color=colours['primary'], xy=(x+dims['w']-dims['pX'],90), font_size=14,  align='topright', font=font)
    screen.text(len(queue['slots']), xy=(x+dims['w']-dims['pX'],103), color=colours['primary'],  align='topright', font_size=32, font=font)
    
    if(len(queue['slots']) > 0):
        drawProgressBar(x)

def drawProgressBar(x):
    title = queue['slots'][0]['filename']
    title = title[:35] + (title[35:] and '...')
    percent = int(queue['slots'][0]['percentage'])
    progress = int((dims['w'] - 2*dims['pX'] - 4) * percent/100.0)
    
    # Using 1x1 PNGs for boxes as rects can't have negative xy vals, images can
    # Progress bar container
    screen.image('images/aqua1x1.png', xy=(x+dims['pX'], 183), scale=(280, 20), align='topleft')
    screen.image('images/navy1x1.png', xy=(x+dims['pX'] + 2, 185), scale=(276, 16), align='topleft')
    
    # Progress bar progress
    screen.image('images/aqua1x1.png', xy=(x+dims['pX'], 183), scale=(progress,20), align='topleft')
    
    # Render active file details
    screen.text(title, xy=(x+dims['w']/2, 165), color=colours['primary'],  align='center', font_size=14, font=font)
    screen.text(str(percent)+'%', xy=((x+(dims['w'])/2),193), color='white',  align='center', font_size=14, font=font)

# Takes a kb/s speed string from SABnzbd (e.g. 8453.423) and makes it nice
def parseSpeed(speed):
    if speed == '?':
        return speed
    else:
        speed = speed.split('.')
        if len(speed[0]) <= 3:
            return "%.2f" % round(float(speed[0]),2)+'Kb/s'
        elif 4 <= len(speed[0]) <= 6:
            return "%.2f" % round(float(speed[0])/1000.0,2)+'Mb/s'
        else:
            return "%.2f" % round(float(speed[0])/1000000.0,2)+'Gb/s?!'

def touchedDashboardPage(xy, action):
    return

# Draws the Control page
def drawControlPage(page):
    x = page['x']
    
    screen.image('images/sabnzbd.png', xy=(x+(dims['w']/2),20), align='top')
        
    for button in page['buttons']:
        drawButton(x+button['dims']['x'], button['dims']['y'], button['dims']['w'], button['dims']['h'], button['text'][button['state']], button['pressed'])
    
def drawButton(x, y, w, h, text, pressed):
    
    buttonState = 'down' if pressed else 'up'
    
    screen.image('images/'+colours['buttons'][buttonState]['border']+'1x1.png', xy=(x, y), scale=(w, h), align='topleft')
    screen.image('images/'+colours['buttons'][buttonState]['fill']+'1x1.png', xy=(x+2, y+2), scale=(w-4, h-4), align='topleft')
    screen.text(text, xy=(x+(w/2), y + 20), color=colours['buttons'][buttonState]['text'],  align='center', font_size=18, font=font)

def touchedControlPage(xy, action, page):
    pageX = page['x']

    for button in page['buttons']:
        if button['debounce'] == 0:
            if isPointInRect(xy[0], xy[1], pageX+button['dims']['x'], button['dims']['y'], pageX+button['dims']['w'], button['dims']['h']):
                if action == 'up':
                    button['pressed'] = False
                    button['action'](button, page)
                elif action == 'move' or action == 'down':
                    button['pressed'] = True

# Pygame has this, but worth spelling it out
def isPointInRect(pX, pY, rX, rY, rW, rH):
    if pX >= rX and pX <= rX + rW and pY >= rY and pY <= rY + rH:
        return True
    else:
        return False
    
def updatePosition():
    global state, q

    if state == 'transitionLeft':
        for page in q:
            page['x'] -= 21.33
        if q[0]['x'] < -dims['w']: # once page is off screen...
            q.pop(0) # knock old current page off the queue - don't need to draw anymore
            q[0]['x'] = 0 # floor current page at x:0
            state = 'display'
    elif state == 'transitionRight':
        for page in q:
            page['x'] += 21.33
        if q[0]['x'] > dims['w']: # once page is off screen...
            q.pop(0) # knock old current page off the queue - don't need to draw anymore
            q[0]['x'] = 0 # floor current page at x:0
            state = 'display'
    else:
        return

# Subtract from debounce timer, if > 0
def updateButtons():
    global q
    
    for page in q:
        for button in page['buttons']:
            if button['debounce'] > 0:
                button['debounce'] -= 2
            else:
                button['debounce'] = 0

# Button pressed event handlers
def handleToggleQueueState(button, page):
    toggleQueueState()
    button['debounce'] = 30
    if button['state'] == 'on':
        button['state'] = 'off'
    else:
        button['state'] = 'on'
    
def handleClearQueue(button, page):
    clearQueue()
    button['debounce'] = 30
    

# Sabnzdb Connection & Data Placeholders
host = tingbot.app.settings['host']
port = tingbot.app.settings['port']
apikey = tingbot.app.settings['apikey']
api = 'http://'+host+':'+port+'/sabnzbd/api?output=json&apikey='+apikey
endpoints = {'queue': '&mode=queue', 'pause': '&mode=pause', 'resume': '&mode=resume', 'cancel': '&mode=queue&name=purge'}
queue = {'speed': '?', 'kbpersec': '?', 'slots': [], 'paused': False}

# Screen / State Management
dims = {'w':320, 'h':240, 'pX':20, 'pY':20}
page = 0 # The current page, or the page we're transitioning to
pages = [
    {
        'x': 0, 
        'draw': drawDashboardPage,
        'touched': touchedDashboardPage,
        'buttons': [],
    },
    {
        'x': dims['w'], 
        'draw': drawControlPage,
        'touched': touchedControlPage,
        'buttons': [
            {
                'dims': {
                    'x': dims['pX'], 'y': 100, 'w': 280, 'h': 40
                },
                'text': {
                    'on': 'Pause Downloads', 'off': 'Resume Downloads'
                },
                'action': handleToggleQueueState,
                'state': 'on', # for toggleable buttons - is it on or off?
                'debounce': 0, # timer to prevent button being 'hit' multiple times in quick succession
                'pressed': False # so we can draw differently
            },
            {
                'dims': {
                  'x': dims['pX'], 'y': 170, 'w': 280, 'h': 40
                },
                'text': {
                    'on': 'Clear Queue', 'off': 'Clear Queue'
                },
                'action': handleClearQueue,
                'state': 'on',
                'debounce': 0, # timer to prevent button being 'hit' multiple times in quick succession
                'pressed': False
            }
        ]
    }
]
state = 'display'
colours = {
    'primary': 'aqua',
    'buttons': {
        'down': {
            'border': 'aqua',
            'fill': 'aqua',
            'text': 'navy',
        },
        'up': {
            'border': 'aqua',
            'fill': 'navy',
            'text': 'white',
        }
    }
}
font = 'fonts/SourceSansPro-Regular.ttf'
q = [pages[page]]
    

# Get fresh Sabnzbd data
@every(seconds=2)
def refresh_data():
    global state
    
    if fetchStatus():
        if state == 'disconnected':
            state = 'display'
    else:
        state = 'disconnected'
 
# Move page left  
@left_button.press
def pageLeft():
    global state, q, page, pages
    if state == 'display':
        state = 'transitionLeft'
        page = 0 if len(pages) == page+1 else page+1
        pages[page]['x'] = dims['w'] # Get new page in position
        q.append(pages[page])

# Move page right
@right_button.press
def pageRight():
    global state, q, page, pages
    if state == 'display':
        state = 'transitionRight'
        page = len(pages)-1 if page-1 < 0 else page-1
        pages[page]['x'] = -dims['w'] # Get new page in position
        q.append(pages[page])

# This is super simple event handling
@touch()
def on_touch(xy, action):
    if state == 'display':
        pages[page]['touched'](xy, action, pages[page])
        
# Logic 
def update():
    updatePosition()
    updateButtons()

# Rendering
def draw():
    screen.fill(color='navy')
    
    if state == 'disconnected':
        screen.text("Can't Connect :(", xy=(dims['w']/2, dims['h']/2), color=colours['primary'],  align='center', font_size=36, font=font)
        return
    
    for page in q:
        page['draw'](page)

# Main loop
@every(seconds=1.0/30)
def run():
    update()
    draw()
        
# Almost ready...
if fetchStatus():
    state = 'display'
else:
    state = 'disconnected'

pages[1]['buttons'][0]['state'] = 'off' if queue['paused'] else 'on' # move this when we do init properly
tingbot.run()
