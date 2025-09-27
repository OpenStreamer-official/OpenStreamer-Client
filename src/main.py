from yt_dlp import YoutubeDL
import pygame
import pygame_gui
import numpy as np
import os
import json
import requests

version = "v1.0.0-prerelease001"

script_dir = os.path.dirname(os.path.abspath(__file__))

# --- YT_DLP OPTIONS ---

# YDL Options for Listing Top 5 Versions
YDL_OPTIONS_LIST_DEFINITIVE = {
    'format': 'bestaudio',
    'noplaylist': 'True',
    'extract_flat': True,
    }

# --- SETUP ---

# - Pygame stuff -
pygame.init()
w = 1280
h = 720
screen = pygame.display.set_mode((w, h))
windowTitle = "OpenStreamer " + version
pygame.display.set_caption(windowTitle)
Clock = pygame.time.Clock()

# - UI -
currentPage = "Home"

# TODO: Convert UI Managers to a dictionary for cleaner code later
homeUiManager = pygame_gui.UIManager((w, h))
libraryUiManager = pygame_gui.UIManager((w, h))
userUiManager = pygame_gui.UIManager((w, h))

# UI related dictionaries
textboxes = {}

# - Timers -
totalTicks = 0

# --- COLOURS ---

# - Theme Colours -
bgColour = (29,31,42)
primaryColour = (254,1,76)
secondaryColour = (1,254,179)
primaryTextColour = (255,255,255)
secondaryTextColour = (224,224,224)
bgDarkColour = (17,18,25)

# - Misc Colours -
black = (0,0,0)

# --- DICTIONARIES ---

# Song Searching (MusicBrainz)
names = {}
artists = {}
ISRCs = {}
lengths = {}

# --- FONTS ---
Roboto_Bold = pygame.font.Font(script_dir + "/assets/fonts/Roboto-Bold.ttf", 48)
Roboto_Medium = pygame.font.Font(script_dir + "/assets/fonts/Roboto-Medium.ttf", 32)
Roboto_Regular = pygame.font.Font(script_dir + "/assets/fonts/Roboto-Regular.ttf", 24)

# --- ARBITRARY FONTS ---
RobotoForSearchBarHomePage = pygame.font.Font(script_dir + "/assets/fonts/Roboto-Medium.ttf", 20) # Font for homepage search box

# --- IMAGES ---

# App Icon 48x
logo = pygame.image.load(script_dir + "/assets/openstreamer-2048x.png")
logo = pygame.transform.smoothscale(logo, (64, 64))
logoRect = logo.get_rect()
logoRect.topleft = (16, 16)

# homePage Icon
house = pygame.image.load(script_dir + "/assets/icons/house-regular-full.svg")
house = pygame.transform.smoothscale(house, (48, 48)).convert()
arr = pygame.surfarray.pixels3d(house).copy() # RGB
alpha = pygame.surfarray.pixels_alpha(house).copy() # A
inverted_rgb = 255 - arr
inverted_surface = pygame.Surface(house.get_size(), pygame.SRCALPHA)
pygame.surfarray.blit_array(inverted_surface, inverted_rgb)
pygame.surfarray.pixels_alpha(inverted_surface)[:, :] = alpha
house = inverted_surface
houseRect = house.get_rect()
houseRect.center = (w // 2) - 128, 48

# libraryPage Icon
library = pygame.image.load(script_dir + "/assets/icons/bookmark-regular-full.svg")
library = pygame.transform.smoothscale(library, (48, 48)).convert()
arr = pygame.surfarray.pixels3d(library).copy() # RGB
alpha = pygame.surfarray.pixels_alpha(library).copy() # A
inverted_rgb = 255 - arr
inverted_surface = pygame.Surface(library.get_size(), pygame.SRCALPHA)
pygame.surfarray.blit_array(inverted_surface, inverted_rgb)
pygame.surfarray.pixels_alpha(inverted_surface)[:, :] = alpha
library = inverted_surface
libraryRect = library.get_rect()
libraryRect.center = w // 2, 48

# userPage Icon
user = pygame.image.load(script_dir + "/assets/icons/user-regular-full.svg")
user = pygame.transform.smoothscale(user, (48, 48)).convert()
arr = pygame.surfarray.pixels3d(user).copy() # RGB
alpha = pygame.surfarray.pixels_alpha(user).copy() # A
inverted_rgb = 255 - arr
inverted_surface = pygame.Surface(user.get_size(), pygame.SRCALPHA)
pygame.surfarray.blit_array(inverted_surface, inverted_rgb)
pygame.surfarray.pixels_alpha(inverted_surface)[:, :] = alpha
user = inverted_surface
userRect = user.get_rect()
userRect.center = (w // 2) + 128, 48

# Search Bar BG
searchBarHomePage = pygame.image.load(script_dir + "/assets/searchBarHomePage.png")
searchBarHomePageInactive = pygame.image.load(script_dir + "/assets/searchBarHomePageInactive.png")

# --- Search Bars ---
nameSearchBarHomePageRect = pygame.Rect(128, 225, 1024, 36)
artistSearchBarHomePageRect = pygame.Rect(128, 325, 1024, 36)

# --- MISC RECTS ---
playerOverviewBar = pygame.Rect(0, 600, 1280, 120)
playerOverviewBarDividerLine = pygame.Rect(0, 595, 1280, 5)

searchButtonHomePage = pygame.Rect(540, 400, 200, 48)

# --- UI ELEMENTS ---

# Homepage Song Search - Name
textboxes["homePageNameSearchBox"] = pygame_gui.elements.UITextEntryBox(relative_rect=nameSearchBarHomePageRect,manager=homeUiManager)
nameSearchBarHomePageFocused = 0

# Homepage Song Search - Artist
textboxes["homePageArtistSearchBox"] = pygame_gui.elements.UITextEntryBox(relative_rect=artistSearchBarHomePageRect,manager=homeUiManager)
artistSearchBarHomePageFocused = 0

# --- FUNCTIONS ---
def searchForAudioChoiceData(query, amount): # Gets the top 5 versions of a song for the definitive version system
    with YoutubeDL(YDL_OPTIONS_LIST_DEFINITIVE) as ydl:
        result = ydl.extract_info(f"ytsearch{amount}:{query}", download=False)

        # 'entries' contains the list of videos
        videos = result.get('entries', [])

        topResults = []
        for video in videos:
            # sanitize each video
            info = ydl.sanitize_info(video)
            topResults.append({
                'title': info.get('title'),
                'channel': info.get('uploader'),
                'length': info.get('duration'),
                'url': info.get('url')
            })

    return topResults

def listSearchChoiceDataInShell(): # Takes results of searchForAudioChoiceData and lists them in the command line
    data = searchForAudioChoiceData("the big goodbye ajr", 5)
    for i, video in enumerate(data, 1):
        print(f"{i}. {video['title']} by {video['channel']} ({video['length']}s)")
        print(f"URL: {video['url']}\n")

def searchSongs(name, artist): # Gets song results from MusicBrainz
    global names, artists, ISRCs, lengths
    
    # Reset dictionaries
    names.clear()
    artists.clear()
    ISRCs.clear()
    lengths.clear()
    
    url = "https://musicbrainz.org/ws/2/recording" # MusicBrainz API endpoint
    if artist == "":
        params = {
            "query": name,
            "limit": 10,
            "fmt": "json"
        }
        print(f"[INFO] Searching for {name} with no artist")
    else:
        params = {
            "query": f'recording:"{name}" AND artist:"{artist}"',
            "limit": 10,
            "fmt": "json"
        }
        print(f"[INFO] Searching for {name} with {artist}")
    
    headers = {"User-Agent": f"OpenStreamer/{version} (imaginegameservice@gmail.com)"} # User-Agent is required by MusicBrainz
    
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    
    for i, rec in enumerate(data.get("recordings", []), start=1): # Fills dictionaries with fetched info
        names[i] = rec.get("title", "")
        artists[i] = rec.get("artist-credit", [{}])[0].get("name", "")
        ISRCs[i] = rec.get("isrcs", [None])[0] if rec.get("isrcs") else None
        lengths[i] = rec.get("length", None)
        lengths[i] = round(lengths[i] / 1000) # Milliseconds to seconds


# --- PAGES ---
def homePage():
    # Greeting
    queuedText = "What are you in the mood for?"
    queuedText_size = pygame.font.Font.size(Roboto_Bold, queuedText)
    text = Roboto_Bold.render(queuedText, True, primaryTextColour)
    screen.blit(text, (w // 2 - (queuedText_size[0] / 2), 100))

    # - Name Search Bar -

    # Name Search Bar BG
    if nameSearchBarHomePageFocused:
        screen.blit(searchBarHomePage, nameSearchBarHomePageRect)
    else:
        screen.blit(searchBarHomePageInactive, nameSearchBarHomePageRect)

    # Name Search Bar Text
    if nameSearchBarHomePageFocused:
        queuedText = textboxes["homePageNameSearchBox"].get_text()
        if totalTicks <= 15:
            queuedText = queuedText + "|"
    else:
        queuedText = textboxes["homePageNameSearchBox"].get_text()

    # Name Search Bar Text Rendering
    queuedText_size = pygame.font.Font.size(RobotoForSearchBarHomePage, queuedText)
    text = RobotoForSearchBarHomePage.render(queuedText, True, primaryTextColour)
    screen.blit(text, pygame.Rect(140, 229, 1016, 28))

    # - Artist Search Bar -

    # Artist Search Bar BG
    if artistSearchBarHomePageFocused:
        screen.blit(searchBarHomePage, artistSearchBarHomePageRect)
    else:
        screen.blit(searchBarHomePageInactive, artistSearchBarHomePageRect)

    # Artist Search Bar Text
    if artistSearchBarHomePageFocused:
        queuedText = textboxes["homePageArtistSearchBox"].get_text()
        if totalTicks <= 15:
            queuedText = queuedText + "|"
    else:
        queuedText = textboxes["homePageArtistSearchBox"].get_text()

    # Artist Search Bar Text Rendering
    queuedText_size = pygame.font.Font.size(RobotoForSearchBarHomePage, queuedText)
    text = RobotoForSearchBarHomePage.render(queuedText, True, primaryTextColour)
    screen.blit(text, pygame.Rect(140, 329, 1016, 28))
    
    # Search Button
    if searchButtonHomePageActive: # Changes button colour
        pygame.draw.rect(screen, bgDarkColour, searchButtonHomePage, border_radius=10)
    else:
        pygame.draw.rect(screen, primaryColour, searchButtonHomePage, border_radius=10)

    queuedText = "Search!"
    queuedText_size = pygame.font.Font.size(Roboto_Medium, queuedText)
    text = Roboto_Medium.render(queuedText, True, primaryTextColour)
    textRect = text.get_rect()
    textRect.center = searchButtonHomePage.center # Centers label to button
    screen.blit(text, textRect)

    # Name Search Box Label
    queuedText = "Name"
    queuedText_size = pygame.font.Font.size(RobotoForSearchBarHomePage, queuedText)
    text = RobotoForSearchBarHomePage.render(queuedText, True, primaryTextColour)
    screen.blit(text, (w // 2 - (queuedText_size[0] / 2), 190))

    # Name Search Box Label
    queuedText = "Artist"
    queuedText_size = pygame.font.Font.size(RobotoForSearchBarHomePage, queuedText)
    text = RobotoForSearchBarHomePage.render(queuedText, True, primaryTextColour)
    screen.blit(text, (w // 2 - (queuedText_size[0] / 2), 290))

def libraryPage():
    pass

def userPage():
    pass

# --- MAIN LOOP ---
running = True
while running:
    screen.fill(bgColour)
    time_delta = Clock.tick(60)/1000.0 # Delta Time
    
    for event in pygame.event.get(): # Event loop
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            isMouseDown = True
            mouse_pos = pygame.mouse.get_pos()
            if nameSearchBarHomePageRect.collidepoint(mouse_pos): # Name search bar focus
                nameSearchBarHomePageFocused = 1
            else:
                nameSearchBarHomePageFocused = 0

            if artistSearchBarHomePageRect.collidepoint(mouse_pos): # Artist search bar focus
                artistSearchBarHomePageFocused = 1
            else:
                artistSearchBarHomePageFocused = 0

        else:
            isMouseDown = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN: # Detects usage of enter key
                restrictInputs = 1
            else:
                restrictInputs = 0
        else:
                restrictInputs = 0
        
        if restrictInputs != 1: # Blocks inputs when enter key detected to block newlines in one-line textboxes
            homeUiManager.process_events(event)
            libraryUiManager.process_events(event)
            userUiManager.process_events(event)

    # - Mouse Events -
    mouse_pos = pygame.mouse.get_pos()
    if logoRect.collidepoint(mouse_pos): # Detect logo click
        if isMouseDown:
            currentPage = "Home"
    if houseRect.collidepoint(mouse_pos): # Detect home click
        if isMouseDown:
            currentPage = "Home"
        else:
            pygame.draw.rect(screen, primaryColour, houseRect, border_radius=10) # Home hover effect
    if libraryRect.collidepoint(mouse_pos): # Detect library click
        if isMouseDown:
            currentPage = "Library"
        else:
            pygame.draw.rect(screen, primaryColour, libraryRect, border_radius=10) # Library hover effect
    if userRect.collidepoint(mouse_pos): # Detect user click
        if isMouseDown:
            currentPage = "User"
        else:
            pygame.draw.rect(screen, primaryColour, userRect, border_radius=10) # User hover effect
    if searchButtonHomePage.collidepoint(mouse_pos): # Home Page Search Bar focusing
        if isMouseDown:
            searchSongs(textboxes["homePageNameSearchBox"].get_text(), textboxes["homePageArtistSearchBox"].get_text())
            print(names)
            print(artists)
            print(ISRCs)
            print(lengths)
        else:
            searchButtonHomePageActive = 1
    else:
        searchButtonHomePageActive = 0
    
    # Nav bar rendering
    screen.blit(logo, logoRect)
    screen.blit(house, houseRect)
    screen.blit(library, libraryRect)
    screen.blit(user, userRect)
    
    # - Page setting -
    if currentPage == "Home":
        homePage()
    if currentPage == "Library":
        libraryPage()
    if currentPage == "User":
        userPage()
    
    # - Now Playing Bar -
    pygame.draw.rect(screen, black, playerOverviewBar)
    pygame.draw.rect(screen, secondaryColour, playerOverviewBarDividerLine)
    
    # Updating window title every frame
    windowTitle = f"OpenStreamer {version} - {currentPage}"
    pygame.display.set_caption(windowTitle)

    # - UI Managers are needy children -
    if currentPage == "Home":
        # homeUiManager.draw_ui(screen)
        homeUiManager.update(time_delta)
    if currentPage == "Library":
        libraryUiManager.draw_ui(screen)
        libraryUiManager.update(time_delta)
    if currentPage == "User":
        userUiManager.draw_ui(screen)
        userUiManager.update(time_delta)

    # - More Pygame stuff -
    pygame.display.flip()
    pygame.display.update()
    Clock.tick(60)

    # Timer
    if totalTicks == 30:
        totalTicks = 0
    totalTicks += 1

pygame.quit() # make it stop